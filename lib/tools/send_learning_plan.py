"""
lib/tools/send_learning_plan.py
Tool 7: Send personalised study roadmap SMS to student.
Only called with explicit student consent.
"""

import time
import os
from lib.db import execute, fetch_one
from lib.plivo_client import send_sms


async def send_learning_plan(
    call_id: str,
    course_id: str,
    recipient_phone: str,
    student_name: str
) -> dict:
    """
    Build and send a personalised learning plan SMS.
    Includes: course name, next batch start, fee summary, demo link, WhatsApp link.
    Must only be called after explicit student consent.
    """
    start = time.monotonic()

    # Get course details
    course = await fetch_one(
        """
        SELECT name, duration, fee, installment_plans
        FROM courses WHERE id = $1
        """,
        course_id
    )

    # Get nearest upcoming batch
    batch = await fetch_one(
        """
        SELECT batch_name, timing, start_date,
               (total_seats - enrolled_students) AS seats_left
        FROM batches
        WHERE course_id = $1
          AND is_active = TRUE
          AND (total_seats - enrolled_students) > 0
        ORDER BY start_date
        LIMIT 1
        """,
        course_id
    )

    # Get best scholarship
    scholarship = await fetch_one(
        """
        SELECT name, discount_percent, discount_flat
        FROM scholarships
        WHERE applicable_courses = 'all'
        ORDER BY COALESCE(discount_percent, 0) DESC
        LIMIT 1
        """
    )

    if not course:
        return {"success": False, "message": "Course not found — cannot build learning plan."}

    institute_name = os.getenv("INSTITUTE_NAME", "Apex Coaching Institute")
    institute_whatsapp = os.getenv("ADMISSION_WHATSAPP", "+919999999999")
    institute_website = os.getenv("INSTITUTE_WEBSITE", "https://apexcoaching.in")
    fee_readable = _format_fee(course["fee"])

    # Build SMS message
    lines = [
        f"Hi {student_name}! 👋",
        f"",
        f"📚 Your Learning Plan from {institute_name}",
        f"",
        f"🎯 Course: {course['name']}",
        f"⏱ Duration: {course['duration']}",
        f"💰 Fee: {fee_readable}",
    ]

    if course.get("installment_plans"):
        lines.append(f"📆 EMI: {course['installment_plans'][0]}")

    if batch:
        lines.append(f"")
        lines.append(f"📅 Next Batch: {batch['start_date']}")
        lines.append(f"🕐 Timing: {batch['timing']}")
        if batch["seats_left"] <= 5:
            lines.append(f"⚠️ Only {batch['seats_left']} seats left!")

    if scholarship and scholarship["discount_percent"]:
        lines.append(f"")
        lines.append(f"🎓 Scholarship: {scholarship['name']} — {scholarship['discount_percent']}% off available!")

    lines.extend([
        f"",
        f"📞 Enroll / Query: WhatsApp us at {institute_whatsapp}",
        f"🌐 More info: {institute_website}",
        f"",
        f"Best of luck! — Team Apex",
    ])

    message = "\n".join(lines)

    # Send SMS
    try:
        response = await send_sms(recipient_phone, message)
        sms_status = "sent"
        message_sid = str(response) if response else "unknown"
    except Exception as e:
        sms_status = "failed"
        message_sid = str(e)[:100]

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Log to communications_sent
    await execute(
        """
        INSERT INTO communications_sent
            (call_id, channel, recipient, message_type, content, status, sent_at)
        VALUES ($1, 'sms', $2, 'learning_plan', $3, $4, NOW())
        """,
        call_id,
        recipient_phone,
        message,
        sms_status,
    )

    # Log tool call
    await execute(
        """
        INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
        VALUES ($1, 'send_learning_plan', $2::jsonb, $3::jsonb, $4, $5)
        """,
        call_id,
        f'{{"course_id": "{course_id}", "student_name": "{student_name}"}}',
        f'{{"status": "{sms_status}"}}',
        sms_status == "sent",
        elapsed_ms
    )

    if sms_status == "sent":
        return {
            "success": True,
            "message": f"Learning plan sent to your phone! Check your messages — it includes the course details, upcoming batch date, fee info, and our WhatsApp number for enrollment.",
            "status": "sent",
        }
    else:
        return {
            "success": False,
            "message": "I wasn't able to send the SMS right now. Please WhatsApp us directly at " + institute_whatsapp + " and our team will send you the full details.",
            "status": "failed",
        }


def _format_fee(fee: int) -> str:
    if fee >= 100000:
        lakhs = fee / 100000
        if lakhs == int(lakhs):
            return f"Rs {int(lakhs)} Lakh"
        return f"Rs {lakhs:.1f} Lakh"
    elif fee >= 1000:
        return f"Rs {fee // 1000},{fee % 1000:03d}"
    return f"Rs {fee}"
