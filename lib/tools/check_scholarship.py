"""
lib/tools/check_scholarship.py
Tool 5: Scholarship eligibility and fee flexibility lookup.
"""

import time
from lib.db import fetch_all, execute


async def check_scholarship(
    course_id: str,
    student_profile: str,
    call_id: str
) -> dict:
    """
    Return applicable scholarships and installment options for a course.
    student_profile is a free-text description (e.g., "Class 11, dropper, financial difficulty")
    used to recommend the most relevant scholarship.
    """
    start = time.monotonic()

    # Get course-specific scholarships + universal ones
    rows = await fetch_all(
        """
        SELECT id, name, description, discount_percent, discount_flat,
               eligibility, applicable_courses, deadline, installment_still_available
        FROM scholarships
        WHERE applicable_courses = 'all'
           OR applicable_courses ILIKE $1
        ORDER BY COALESCE(discount_percent, 0) DESC
        """,
        f"%{course_id}%"
    )

    # Also get course fee for savings calculation
    from lib.db import fetch_one
    course_row = await fetch_one(
        "SELECT fee, installment_plans FROM courses WHERE id = $1",
        course_id
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    scholarships = []
    for r in rows:
        saving = None
        if r["discount_percent"] and course_row:
            saving = int(course_row["fee"] * r["discount_percent"] / 100)
            saving_str = _format_fee(saving)
        elif r["discount_flat"]:
            saving = r["discount_flat"]
            saving_str = _format_fee(saving)
        else:
            saving_str = None

        scholarships.append({
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "discount_percent": r["discount_percent"],
            "discount_flat": r["discount_flat"],
            "saving_readable": saving_str,
            "eligibility": r["eligibility"],
            "deadline": r["deadline"],
            "installment_available": r["installment_still_available"],
        })

    # Recommend best match based on student_profile
    best_match = _recommend_scholarship(scholarships, student_profile, course_id)

    # Installment plans from course table
    installment_plans = course_row["installment_plans"] if course_row else []
    total_fee = course_row["fee"] if course_row else None

    result = {
        "found": len(scholarships) > 0,
        "total_fee": total_fee,
        "total_fee_readable": _format_fee(total_fee) if total_fee else None,
        "scholarships": scholarships,
        "best_match_for_profile": best_match,
        "installment_plans": installment_plans,
        "combined_tip": _combined_tip(scholarships, installment_plans),
    }

    await execute(
        """
        INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
        VALUES ($1, 'check_scholarship', $2::jsonb, $3::jsonb, $4, $5)
        """,
        call_id,
        f'{{"course_id": "{course_id}", "student_profile": "{student_profile[:50]}"}}',
        f'{{"found": {str(result["found"]).lower()}, "scholarships_count": {len(scholarships)}}}',
        True,
        elapsed_ms
    )

    return result


def _recommend_scholarship(scholarships: list, profile: str, course_id: str) -> dict | None:
    """Pick the most likely scholarship given student profile text."""
    profile_lower = profile.lower()

    # Check for dropper profile
    if "drop" in profile_lower or "repeat" in profile_lower:
        for s in scholarships:
            if "dropper" in s["name"].lower():
                return {**s, "reason": "You mentioned you're a dropper — the Dropper Special Discount applies directly to you."}

    # Check for financial need
    financial_keywords = ["financial", "fee too high", "can't afford", "less money", "poor", "need help", "scholarship", "concession"]
    if any(k in profile_lower for k in financial_keywords):
        for s in scholarships:
            if "need" in s["name"].lower() or "financial" in s["name"].lower():
                return {**s, "reason": "Based on what you mentioned, the Need-Based Financial Aid could be the most helpful — up to 30% off with income documentation."}

    # Check for sibling
    if "sibling" in profile_lower or "brother" in profile_lower or "sister" in profile_lower:
        for s in scholarships:
            if "sibling" in s["name"].lower():
                return {**s, "reason": "If your sibling is already at Apex, the Sibling Scholarship gives you 10% off."}

    # Default to merit if no match
    for s in scholarships:
        if "merit" in s["name"].lower():
            return {**s, "reason": "We recommend taking our free Scholarship Test — if you score in the top 10%, you get 20% off immediately."}

    return scholarships[0] if scholarships else None


def _combined_tip(scholarships: list, plans: list) -> str:
    """Build a combined tip about scholarships + installments."""
    if not scholarships:
        return "Installment plans are available to spread the fee over multiple months."
    best = max(scholarships, key=lambda x: x.get("discount_percent") or 0)
    plan_note = f" You can also combine this with our installment plans — {plans[0] if plans else 'monthly EMIs available'}." if plans else ""
    return f"Best option: {best['name']} could save you {best['saving_readable'] or 'significantly'}.{plan_note}"


def _format_fee(fee: int) -> str:
    if not fee:
        return "N/A"
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
