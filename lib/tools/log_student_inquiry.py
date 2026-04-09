"""
lib/tools/log_student_inquiry.py
Tool 6: Log student interest in CRM with lead stage tracking.
"""

import time
import random
import string
from datetime import date
from lib.db import execute, fetch_one


async def log_student_inquiry(
    call_id: str,
    student_name: str,
    interested_course: str,
    class_or_target: str,
    preferred_timing: str,
    preferred_branch: str,
    caller_number_hash: str
) -> dict:
    """
    Create a CRM inquiry record for a student who has shown genuine interest.
    Generates a unique reference number (APX-YYYYMMDD-XXXXX) for follow-up.
    Admissions team will call the student back within 24 hours.
    """
    start = time.monotonic()

    inquiry_ref = _generate_ref()

    await execute(
        """
        INSERT INTO student_inquiries
            (inquiry_ref, call_id, caller_hash, student_name,
             interested_course, class_or_target, preferred_timing,
             preferred_branch, status, lead_stage, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'new', 'contacted', NOW(), NOW())
        """,
        inquiry_ref,
        call_id,
        caller_number_hash,
        student_name,
        interested_course,
        class_or_target,
        preferred_timing,
        preferred_branch,
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    await execute(
        """
        INSERT INTO tool_calls (call_id, tool_name, input_data, output_data, success, duration_ms)
        VALUES ($1, 'log_student_inquiry', $2::jsonb, $3::jsonb, $4, $5)
        """,
        call_id,
        f'{{"student_name": "{student_name}", "course": "{interested_course}"}}',
        f'{{"inquiry_ref": "{inquiry_ref}"}}',
        True,
        elapsed_ms
    )

    return {
        "success": True,
        "inquiry_ref": inquiry_ref,
        "student_name": student_name,
        "course": interested_course,
        "message": f"Your inquiry has been registered with reference number {inquiry_ref}. Our admissions counsellor will call you back within 24 working hours to answer all your questions and help with enrollment.",
        "next_steps": [
            "Admissions team will call within 24 working hours",
            "They will guide you through the enrollment process",
            "You can also attend a free demo class before enrolling",
        ]
    }


def _generate_ref() -> str:
    """Generate unique inquiry reference: APX-YYYYMMDD-XXXXX"""
    today = date.today().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"APX-{today}-{suffix}"
