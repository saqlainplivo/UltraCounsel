"""
lib/tools/check_batch_availability.py
Tool 3: Check available batches with timing personalization.
"""

import time
import re
from lib.db import fetch_all, execute


async def check_batch_availability(
    course_id: str,
    preferred_time: str,
    call_id: str
) -> dict:
    """
    Return active batches for a course with personalized timing recommendations.
    If preferred_time is provided (e.g., "morning", "after 4 PM", "weekend"),
    ranks and annotates batches by fit. Also flags school-hour conflicts.
    """
    start = time.monotonic()

    rows = await fetch_all(
        """
        SELECT b.id, b.batch_name, b.timing, b.days_per_week, b.days,
               b.start_date, b.total_seats, b.enrolled_students,
               (b.total_seats - b.enrolled_students) AS seats_left,
               b.mode, b.branch_id, b.note,
               br.name AS branch_name, br.city AS branch_city,
               br.area AS branch_area
        FROM batches b
        LEFT JOIN branches br ON br.id = b.branch_id
        WHERE b.course_id = $1 AND b.is_active = TRUE
        ORDER BY b.start_date, b.timing
        """,
        course_id
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    if not rows:
        await _log(call_id, course_id, preferred_time, False, elapsed_ms)
        return {
            "found": False,
            "message": f"No active batches found for course '{course_id}'. New batches may be starting soon — ask to log an inquiry and we'll contact you when seats open.",
        }

    batches = []
    for r in rows:
        seats_left = r["seats_left"]
        batch = {
            "id": r["id"],
            "name": r["batch_name"],
            "timing": r["timing"],
            "days": r["days"],
            "start_date": str(r["start_date"]) if r["start_date"] else None,
            "seats_left": seats_left,
            "total_seats": r["total_seats"],
            "mode": r["mode"],
            "branch": f"{r['branch_name']}, {r['branch_area']}, {r['branch_city']}" if r["branch_name"] else r["branch_id"],
            "note": r["note"],
            "availability_status": _availability_label(seats_left),
            "fit_score": 0,
            "fit_notes": [],
        }

        # Personalization: score against preferred_time
        if preferred_time:
            fit_score, fit_notes = _score_batch(r["timing"], r["days_per_week"], preferred_time)
            batch["fit_score"] = fit_score
            batch["fit_notes"] = fit_notes

        batches.append(batch)

    # Sort by fit score (descending) if preference given
    if preferred_time:
        batches.sort(key=lambda x: x["fit_score"], reverse=True)

    # General contextual insights
    insights = []
    if preferred_time:
        pref_lower = preferred_time.lower()
        if "morning" in pref_lower:
            insights.append("Morning batches typically have higher attendance consistency and students tend to retain concepts better in morning sessions.")
        elif "evening" in pref_lower or "after school" in pref_lower:
            insights.append("Evening batches are popular among school-going students. Ensure your school schedule doesn't overlap.")
        elif "weekend" in pref_lower:
            insights.append("Weekend batches are ideal if weekdays are fully occupied with school. The longer sessions on weekends ensure sufficient coverage.")

    # School-hour conflict detection
    school_conflict_warning = None
    if preferred_time and _likely_school_hours(preferred_time):
        school_conflict_warning = "The timing you mentioned overlaps with typical school hours (8 AM to 2 PM on weekdays). Please confirm your school schedule before finalizing a batch."

    await _log(call_id, course_id, preferred_time, True, elapsed_ms)

    return {
        "found": True,
        "course_id": course_id,
        "total_batches": len(batches),
        "batches": batches,
        "insights": insights,
        "school_conflict_warning": school_conflict_warning,
    }


def _availability_label(seats_left: int) -> str:
    if seats_left <= 0:
        return "FULL — no seats available"
    elif seats_left <= 3:
        return f"ALMOST FULL — only {seats_left} seat(s) left"
    elif seats_left <= 8:
        return f"LIMITED — {seats_left} seats remaining"
    return f"AVAILABLE — {seats_left} seats open"


def _score_batch(timing: str, days: int, preferred_time: str) -> tuple[int, list]:
    """Score a batch against preferred_time. Returns (score 0-10, notes list)."""
    score = 5
    notes = []
    timing_lower = timing.lower()
    pref_lower = preferred_time.lower()

    if "morning" in pref_lower and ("am" in timing_lower or "morning" in timing_lower):
        score += 3
        notes.append("Matches your morning preference")
    elif "evening" in pref_lower and ("pm" in timing_lower or "evening" in timing_lower):
        score += 3
        notes.append("Matches your evening preference")
    elif "weekend" in pref_lower and ("sat" in timing_lower or "sun" in timing_lower):
        score += 4
        notes.append("Weekend batch — perfect match")
    elif "weekday" in pref_lower and days >= 5:
        score += 2
        notes.append("Weekday batch as preferred")

    # Extract hour preference like "after 4" or "before 8"
    after_match = re.search(r"after\s+(\d+)", pref_lower)
    if after_match:
        preferred_hour = int(after_match.group(1))
        time_match = re.search(r"(\d+):?(\d*)\s*(am|pm)", timing_lower)
        if time_match:
            hour = int(time_match.group(1))
            ampm = time_match.group(3)
            if ampm == "pm" and hour != 12:
                hour += 12
            if hour >= preferred_hour:
                score += 2
                notes.append(f"Starts after {preferred_hour} as you requested")

    return min(score, 10), notes


def _likely_school_hours(preferred_time: str) -> bool:
    """Check if preferred_time falls in typical school hours (8 AM - 2 PM weekdays)."""
    pref_lower = preferred_time.lower()
    school_indicators = ["8 am", "9 am", "10 am", "11 am", "12 pm", "1 pm", "morning"]
    return any(ind in pref_lower for ind in school_indicators)


async def _log(call_id, course_id, preferred_time, success, elapsed_ms):
    await execute(
        """
        INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
        VALUES ($1, 'check_batch_availability', $2::jsonb, $3::jsonb, $4, $5)
        """,
        call_id,
        f'{{"course_id": "{course_id}", "preferred_time": "{preferred_time}"}}',
        f'{{"success": {str(success).lower()}}}',
        success,
        elapsed_ms
    )
