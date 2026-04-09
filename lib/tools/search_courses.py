"""
lib/tools/search_courses.py
Tool 1: Search courses by subject, class, exam, or keyword.
"""

import time
from lib.db import fetch_all, execute


async def search_courses(query: str, call_id: str) -> dict:
    """
    Search the Apex course catalog by keyword.
    Supports: class name, board, exam (JEE/NEET), subject, or general keyword.
    Returns up to 5 matching courses with essential details.
    """
    start = time.monotonic()

    # Normalize query for better matching
    search_term = f"%{query.strip()}%"

    rows = await fetch_all(
        """
        SELECT id, name, category, target_class, board,
               duration, fee, mode, eligibility
        FROM courses
        WHERE
            name         ILIKE $1 OR
            category     ILIKE $1 OR
            target_class ILIKE $1 OR
            board        ILIKE $1 OR
            description  ILIKE $1 OR
            array_to_string(subjects, ',') ILIKE $1
        ORDER BY
            CASE category
                WHEN 'IIT-JEE' THEN 1
                WHEN 'NEET'    THEN 2
                ELSE 3
            END,
            target_class
        LIMIT 5
        """,
        search_term
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    if not rows:
        result = {
            "found": False,
            "courses": [],
            "message": f"No courses found matching '{query}'. Available categories: Class 8-10 CBSE/ICSE, JEE Mains, JEE Advanced, JEE Dropper, NEET 2-Year, NEET 1-Year, NEET Repeater.",
        }
    else:
        courses = []
        for r in rows:
            courses.append({
                "id": r["id"],
                "name": r["name"],
                "category": r["category"],
                "target_class": r["target_class"],
                "board": r["board"],
                "duration": r["duration"],
                "fee": r["fee"],
                "fee_readable": _format_fee(r["fee"]),
                "modes_available": r["mode"],
                "eligibility": r["eligibility"],
            })

        result = {
            "found": True,
            "count": len(courses),
            "courses": courses,
        }

    # Log tool call
    await execute(
        """
        INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, duration_ms)
        VALUES ($1, 'search_courses', $2::jsonb, $3::jsonb, $4)
        """,
        call_id,
        f'{{"query": "{query}"}}',
        f'{{"found": {str(result["found"]).lower()}, "count": {result.get("count", 0)}}}',
        elapsed_ms
    )

    return result


def _format_fee(fee: int) -> str:
    """Convert fee integer to readable Indian format."""
    if fee >= 100000:
        lakhs = fee / 100000
        if lakhs == int(lakhs):
            return f"{int(lakhs)} lakh rupees"
        return f"{lakhs:.1f} lakh rupees"
    elif fee >= 1000:
        thousands = fee / 1000
        if thousands == int(thousands):
            return f"{int(thousands)} thousand rupees"
        return f"{thousands:.1f} thousand rupees"
    return f"{fee} rupees"
