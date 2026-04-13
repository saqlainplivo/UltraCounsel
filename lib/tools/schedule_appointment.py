"""
lib/tools/schedule_appointment.py
Schedules a counselling, demo, or enrollment appointment at an Apex branch.
Simulated (no Google Calendar) — stored in custom_appointments DB table.
"""

import logging
import secrets
from datetime import date, datetime, timedelta
from lib.db import get_pool

logger = logging.getLogger(__name__)


def _resolve_date(preferred_date: str) -> date:
    if not preferred_date:
        return date.today() + timedelta(days=2)
    s = preferred_date.lower().strip()
    today = date.today()
    if "today" in s:
        return today
    if "tomorrow" in s:
        return today + timedelta(days=1)
    if "saturday" in s:
        days_ahead = (5 - today.weekday()) % 7 or 7
        return today + timedelta(days=days_ahead)
    if "sunday" in s:
        days_ahead = (6 - today.weekday()) % 7 or 7
        return today + timedelta(days=days_ahead)
    if "next week" in s:
        return today + timedelta(days=7)
    try:
        return date.fromisoformat(preferred_date.strip())
    except ValueError:
        return today + timedelta(days=3)


def _resolve_time(preferred_time: str) -> str:
    if not preferred_time:
        return "10:00 AM"
    s = preferred_time.lower()
    if any(x in s for x in ["morning", "9 am", "10 am", "11 am", "9am", "10am", "11am"]):
        return "10:00 AM"
    if any(x in s for x in ["afternoon", "1 pm", "2 pm", "3 pm", "1pm", "2pm", "3pm", "noon"]):
        return "02:00 PM"
    if any(x in s for x in ["evening", "4 pm", "5 pm", "6 pm", "4pm", "5pm", "6pm"]):
        return "05:00 PM"
    for fmt in ["%I %p", "%I:%M %p", "%H:%M"]:
        try:
            t = datetime.strptime(preferred_time.upper().strip(), fmt)
            return t.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue
    return "10:00 AM"


async def schedule_appointment(
    call_id: str,
    student_name: str,
    caller_hash: str,
    course_id: str,
    preferred_date: str,
    preferred_time: str,
    branch_or_city: str,
    appointment_type: str = "counseling",
) -> dict:
    pool = get_pool()
    started = datetime.utcnow()

    try:
        async with pool.acquire() as conn:
            branch = None
            if branch_or_city and branch_or_city.lower() not in ("online", "virtual", "remote", ""):
                branch = await conn.fetchrow("""
                    SELECT id, name, city, area, address, contact
                    FROM branches
                    WHERE (LOWER(city) LIKE LOWER($1) OR LOWER(area) LIKE LOWER($1) OR LOWER(name) LIKE LOWER($1))
                      AND id != 'B-ONLINE'
                    LIMIT 1
                """, f"%{branch_or_city}%")

            is_online = branch is None
            if is_online:
                branch = await conn.fetchrow(
                    "SELECT id, name, city, contact FROM branches WHERE id = 'B-ONLINE'"
                )

            appt_date = _resolve_date(preferred_date)
            appt_time = _resolve_time(preferred_time)
            if appt_date <= date.today():
                appt_date = date.today() + timedelta(days=1)

            appt_type = "counseling"
            if appointment_type:
                t = appointment_type.lower()
                if "demo" in t:
                    appt_type = "demo"
                elif any(x in t for x in ["enroll", "admission", "walk"]):
                    appt_type = "enrollment_walk_in"

            inquiry_ref = None
            if caller_hash:
                row = await conn.fetchrow(
                    "SELECT inquiry_ref FROM student_inquiries WHERE caller_hash=$1 ORDER BY created_at DESC LIMIT 1",
                    caller_hash
                )
                if row:
                    inquiry_ref = row["inquiry_ref"]

            meeting_token = secrets.token_urlsafe(8)
            meeting_link = f"https://meet.apexcoaching.in/session/{meeting_token}" if is_online else None

            appt_id = await conn.fetchval("""
                INSERT INTO custom_appointments
                  (inquiry_ref, student_name, caller_hash, course_id, branch_id,
                   appt_type, appt_date, appt_time, mode, meeting_link, status)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'scheduled')
                RETURNING id
            """,
            inquiry_ref, student_name, caller_hash,
            course_id if course_id else None,
            branch["id"] if branch else None,
            appt_type, appt_date, appt_time,
            "online" if is_online else "offline",
            meeting_link)

            duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            result = {
                "success": True,
                "appointment_id": f"APT-{appt_id:05d}",
                "student_name": student_name,
                "appointment_type": appt_type,
                "date": appt_date.strftime("%A, %d %B %Y"),
                "time": appt_time,
                "mode": "online" if is_online else "offline",
                "branch_name": branch["name"] if branch else "Online Session",
                "branch_city": branch.get("city", "India") if branch and not is_online else "Pan-India",
                "address": branch.get("address", "") if branch and not is_online else None,
                "contact": branch.get("contact", "") if branch else None,
                "meeting_link": meeting_link,
                "inquiry_ref": inquiry_ref,
                "confirmation_message": (
                    f"Your {appt_type.replace('_',' ')} appointment is confirmed for "
                    f"{appt_date.strftime('%A, %d %B')} at {appt_time} "
                    f"{'online' if is_online else 'at ' + branch['name']}. "
                    f"Appointment ID: APT-{appt_id:05d}."
                ),
                "next_steps": [
                    "Our counselling team will call you the day before to confirm.",
                    "Please keep your marksheet handy if you have one.",
                    "Join 5 minutes early." if is_online else "Please arrive 10 minutes early at the branch."
                ]
            }

            await conn.execute("""
                INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
                VALUES ($1,'schedule_appointment',$2,$3,true,$4)
            """, call_id, {
                "student_name": student_name, "preferred_date": preferred_date,
                "preferred_time": preferred_time, "branch_or_city": branch_or_city,
                "appointment_type": appointment_type
            }, result, duration_ms)

            return result

    except Exception as e:
        logger.error(f"schedule_appointment error: {e}", exc_info=True)
        return {
            "success": False,
            "error": "Could not schedule appointment right now. Our team will call you to confirm a slot.",
            "fallback": "Please call us directly at +91-800-APEX-LEARN to book your appointment."
        }
