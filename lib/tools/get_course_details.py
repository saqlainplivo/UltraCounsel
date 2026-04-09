"""
lib/tools/get_course_details.py
Tool 2: Get full course details including syllabus, faculty intelligence, and outcomes.
"""

import time
from lib.db import fetch_one, fetch_all, execute


async def get_course_details(course_id: str, call_id: str) -> dict:
    """
    Return comprehensive details for a specific course.
    Includes: course info, faculty profile, sequenced syllabus,
    outcome data, study material, reference books, and fee breakdown.
    """
    start = time.monotonic()

    # 1. Core course info
    course = await fetch_one(
        """
        SELECT id, name, category, target_class, board, subjects,
               duration, fee, mode, eligibility, description,
               study_material, reference_books, test_frequency,
               installment_available, installment_plans
        FROM courses
        WHERE id = $1
        """,
        course_id
    )

    if not course:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        await _log(call_id, course_id, False, elapsed_ms)
        return {
            "found": False,
            "message": f"Course '{course_id}' not found. Use search_courses to find valid course IDs."
        }

    # 2. Faculty for this course
    faculty_rows = await fetch_all(
        """
        SELECT id, name, qualification, experience_years, subjects,
               specialization, teaching_style, past_results, availability
        FROM faculty
        WHERE $1 = ANY(assigned_courses)
        ORDER BY experience_years DESC
        """,
        course_id
    )

    # 3. Syllabus topics (ordered)
    syllabus = await fetch_all(
        """
        SELECT sequence_order, topic_name, sub_topics,
               ncert_aligned, estimated_weeks, difficulty
        FROM syllabus_topics
        WHERE course_id = $1
        ORDER BY sequence_order
        """,
        course_id
    )

    # 4. Outcomes
    outcome = await fetch_one(
        """
        SELECT avg_score_improvement, selection_rate, past_rankers, note
        FROM course_outcomes
        WHERE course_id = $1
        """,
        course_id
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Build readable result
    faculty_list = []
    for f in faculty_rows:
        faculty_list.append({
            "name": f["name"],
            "qualification": f["qualification"],
            "experience": f"{f['experience_years']} years",
            "subjects": f["subjects"],
            "specialization": f["specialization"],
            "teaching_style": f["teaching_style"],
            "past_results": f["past_results"],
            "availability": f["availability"],
        })

    # Build syllabus summary (voice-friendly)
    syllabus_summary = []
    for t in syllabus:
        syllabus_summary.append({
            "order": t["sequence_order"],
            "topic": t["topic_name"],
            "sub_topics": t["sub_topics"] or [],
            "ncert_aligned": t["ncert_aligned"],
            "duration": f"{t['estimated_weeks']} weeks" if t["estimated_weeks"] else None,
            "difficulty": t["difficulty"],
        })

    # Check if organic chemistry is covered (for NEET/JEE queries)
    has_organic_chem = any(
        "organic" in t["topic_name"].lower()
        for t in syllabus
    )

    # Check NCERT coverage
    ncert_topics = [t for t in syllabus if t["ncert_aligned"]]
    ncert_coverage = f"{len(ncert_topics)} out of {len(syllabus)} topics are NCERT-aligned" if syllabus else "N/A"

    result = {
        "found": True,
        "course": {
            "id": course["id"],
            "name": course["name"],
            "category": course["category"],
            "target_class": course["target_class"],
            "board": course["board"],
            "subjects": course["subjects"],
            "duration": course["duration"],
            "fee": course["fee"],
            "fee_readable": _format_fee(course["fee"]),
            "modes": course["mode"],
            "eligibility": course["eligibility"],
            "description": course["description"],
        },
        "study_material": {
            "material": course["study_material"],
            "reference_books": course["reference_books"],
            "test_frequency": course["test_frequency"],
        },
        "fee_details": {
            "total_fee": course["fee"],
            "fee_readable": _format_fee(course["fee"]),
            "installment_available": course["installment_available"],
            "installment_plans": course["installment_plans"],
        },
        "faculty": faculty_list,
        "syllabus": {
            "total_topics": len(syllabus_summary),
            "topics": syllabus_summary,
            "ncert_coverage": ncert_coverage,
            "organic_chemistry_covered": has_organic_chem,
        },
        "outcomes": dict(outcome) if outcome else {},
    }

    await _log(call_id, course_id, True, elapsed_ms)
    return result


async def _log(call_id: str, course_id: str, success: bool, elapsed_ms: int):
    await execute(
        """
        INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
        VALUES ($1, 'get_course_details', $2::jsonb, $3::jsonb, $4, $5)
        """,
        call_id,
        f'{{"course_id": "{course_id}"}}',
        f'{{"success": {str(success).lower()}}}',
        success,
        elapsed_ms
    )


def _format_fee(fee: int) -> str:
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
