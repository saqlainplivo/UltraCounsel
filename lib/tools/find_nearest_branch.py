"""
lib/tools/find_nearest_branch.py
Tool 4: Location-aware branch discovery for Apex Coaching Institute.
"""

import time
from lib.db import fetch_all, execute


async def find_nearest_branch(
    city_or_area: str,
    course_id: str,
    call_id: str
) -> dict:
    """
    Find Apex branches near the caller's city or area that offer the specified course.
    If no match found, returns the online option with full feature list.
    """
    start = time.monotonic()

    # Search by city or area name
    search_term = f"%{city_or_area.strip()}%"
    rows = await fetch_all(
        """
        SELECT id, name, city, area, address, contact,
               modes_available, facilities, available_courses
        FROM branches
        WHERE
            (city ILIKE $1 OR area ILIKE $1)
            AND $2 = ANY(available_courses)
            AND id != 'B-ONLINE'
        ORDER BY city, area
        """,
        search_term,
        course_id
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    if rows:
        branches = []
        for r in rows:
            branches.append({
                "id": r["id"],
                "name": r["name"],
                "city": r["city"],
                "area": r["area"],
                "address": r["address"],
                "contact": r["contact"],
                "modes_available": r["modes_available"],
                "facilities": r["facilities"],
                "course_available": True,
            })

        # Also always mention online option
        online = await _get_online_branch()

        result = {
            "found_offline": True,
            "branches_near_you": branches,
            "online_also_available": True,
            "online_option": online,
            "recommendation": _build_recommendation(branches, city_or_area),
        }
    else:
        # No offline branch near them — recommend online
        online = await _get_online_branch()

        result = {
            "found_offline": False,
            "message": f"We don't have an offline branch in '{city_or_area}' that offers this course, but our online program has everything you need.",
            "online_option": online,
            "online_also_available": True,
            "recommendation": "Our Pan-India Online program is a great fit. You get live classes, recorded lectures, weekly tests, and dedicated doubt sessions — all from home.",
        }

    await execute(
        """
        INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
        VALUES ($1, 'find_nearest_branch', $2::jsonb, $3::jsonb, $4, $5)
        """,
        call_id,
        f'{{"city_or_area": "{city_or_area}", "course_id": "{course_id}"}}',
        f'{{"found_offline": {str(result["found_offline"]).lower()}}}',
        True,
        elapsed_ms
    )

    return result


async def _get_online_branch() -> dict:
    from lib.db import fetch_one
    row = await fetch_one("SELECT * FROM branches WHERE id = 'B-ONLINE'")
    if not row:
        return {
            "name": "Apex Online — Pan-India",
            "contact": "1800-APEX-LEARN (toll free)",
            "modes_available": ["online"],
            "facilities": [
                "Live interactive classes",
                "Recorded lectures with 180-day replay",
                "Online doubt sessions 6 days a week",
                "Weekly tests with auto-grading",
                "Parent progress dashboard",
                "WhatsApp batch support group"
            ]
        }
    return {
        "name": row["name"],
        "contact": row["contact"],
        "modes_available": row["modes_available"],
        "facilities": row["facilities"],
    }


def _build_recommendation(branches: list, area: str) -> str:
    if len(branches) == 1:
        b = branches[0]
        return f"Our {b['area']} branch in {b['city']} is your nearest Apex center. It offers offline and hybrid classes with all major facilities."
    elif len(branches) > 1:
        names = [f"{b['area']}, {b['city']}" for b in branches]
        return f"You have {len(branches)} Apex branches near you: {' and '.join(names)}. You can choose based on which is more convenient to commute to."
    return f"No offline branch found near {area}."
