"""
lib/tools/get_batch_stats.py
Returns cohort-level batch statistics and track record for a course.
"""

import logging
from datetime import datetime
from lib.db import get_pool

logger = logging.getLogger(__name__)


async def get_batch_stats(course_id: str, call_id: str) -> dict:
    """
    Returns historical batch statistics for a course.
    Last 3 cohorts with selection rates, topper scores, colleges joined.
    """
    pool = get_pool()
    started = datetime.utcnow()

    try:
        async with pool.acquire() as conn:
            course = await conn.fetchrow(
                "SELECT name, category FROM courses WHERE id = $1", course_id
            )
            if not course:
                return {"found": False, "error": f"Course {course_id} not found"}

            stats = await conn.fetch("""
                SELECT cohort_label, cohort_year, total_enrolled,
                       avg_score_improvement, selection_rate, qualified_count,
                       topper_name, topper_score, colleges_joined,
                       notable_achievement, honest_disclaimer
                FROM batch_statistics
                WHERE course_id = $1
                ORDER BY cohort_year DESC, id DESC
                LIMIT 3
            """, course_id)

            outcome = await conn.fetchrow(
                "SELECT avg_score_improvement, selection_rate, past_rankers, note FROM course_outcomes WHERE course_id = $1",
                course_id
            )

            cohorts = []
            for s in stats:
                cohorts.append({
                    "cohort": s["cohort_label"],
                    "year": s["cohort_year"],
                    "total_enrolled": s["total_enrolled"],
                    "avg_score_improvement": s["avg_score_improvement"],
                    "selection_rate": s["selection_rate"],
                    "qualified_count": s["qualified_count"],
                    "topper_name": s["topper_name"],
                    "topper_score": s["topper_score"],
                    "colleges_joined": list(s["colleges_joined"]) if s["colleges_joined"] else [],
                    "notable_achievement": s["notable_achievement"],
                })

            duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            result = {
                "found": True,
                "course_id": course_id,
                "course_name": course["name"],
                "category": course["category"],
                "cohort_count": len(cohorts),
                "cohorts": cohorts,
                "overall_outcome": {
                    "avg_score_improvement": outcome["avg_score_improvement"] if outcome else "Data updating",
                    "selection_rate": outcome["selection_rate"] if outcome else "Data updating",
                    "past_rankers": outcome["past_rankers"] if outcome else "",
                    "note": outcome["note"] if outcome else "",
                } if outcome else None,
                "disclaimer": "Past batch performance is indicative of teaching quality and not a guarantee of individual results.",
            }

            await conn.execute("""
                INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
                VALUES ($1,'get_batch_stats',$2,$3,true,$4)
            """, call_id, {"course_id": course_id}, result, duration_ms)

            return result

    except Exception as e:
        logger.error(f"get_batch_stats error: {e}", exc_info=True)
        return {
            "found": False,
            "error": "Could not fetch batch statistics right now.",
            "fallback": "Our counsellor can share detailed batch results during your consultation."
        }
