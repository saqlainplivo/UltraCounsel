"""
api/webhook/events.py
Ultravox event webhook — processes real-time events during a call.

Handles:
- transcript: stores dialogue turns
- call_ended: closes call, builds summary, saves session
- intent_detected: stores detected intent
"""

import logging
from fastapi import APIRouter, Request
from typing import Optional

from lib.db import execute, fetch_one, fetch_all
from lib.security import hash_phone_number
from lib.session_manager import save_caller_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/events")
async def handle_events(request: Request):
    """
    Receives Ultravox event payloads.
    Events: transcript, call_ended, intent_detected
    """
    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    event_type = body.get("type") or body.get("event")
    call_id = body.get("callId") or body.get("call_id") or body.get("call_uuid")

    if not event_type or not call_id:
        return {"status": "ignored", "message": "Missing event type or call_id"}

    logger.debug(f"Event: {event_type} for call {call_id}")

    # ── Transcript event ──────────────────────────────────────────────────
    if event_type == "transcript":
        role = body.get("role", "unknown")
        content = body.get("text") or body.get("transcript") or ""
        if content:
            await execute(
                """
                INSERT INTO transcripts (call_id, role, content, timestamp)
                VALUES ($1, $2, $3, NOW())
                """,
                call_id, role, content
            )

    # ── Call ended event ──────────────────────────────────────────────────
    elif event_type in ("call_ended", "hangup", "call.ended"):
        duration = body.get("duration") or body.get("duration_seconds")

        # Update call_logs
        await execute(
            """
            UPDATE call_logs
            SET status = 'completed',
                ended_at = NOW(),
                duration_seconds = $1
            WHERE call_uuid = $2
            """,
            int(duration) if duration else None,
            call_id,
        )

        # Generate summary
        summary = await _generate_call_summary(call_id)

        # Save summary
        await execute(
            """
            INSERT INTO call_summaries
                (call_id, primary_intent, courses_discussed, inquiry_logged,
                 demo_booked, sms_sent, resolution_status, summary_text, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            ON CONFLICT DO NOTHING
            """,
            call_id,
            summary["primary_intent"],
            summary["courses_discussed"],
            summary["inquiry_logged"],
            summary["demo_booked"],
            summary["sms_sent"],
            summary["resolution_status"],
            summary["summary_text"],
        )

        # Save session for returning caller context
        call_log = await fetch_one("SELECT caller_hash FROM call_logs WHERE call_uuid = $1", call_id)
        if call_log and call_log["caller_hash"]:
            inquiry = await fetch_one(
                "SELECT inquiry_ref FROM student_inquiries WHERE call_id = $1 LIMIT 1",
                call_id
            )
            await save_caller_session(
                phone_hash=call_log["caller_hash"],
                call_id=call_id,
                topics_discussed=summary["courses_discussed"] or [],
                courses_recommended=summary["courses_discussed"] or [],
                inquiry_ref=inquiry["inquiry_ref"] if inquiry else None,
            )

        logger.info(f"Call {call_id} ended. Intent: {summary['primary_intent']}, Resolution: {summary['resolution_status']}")

    # ── Intent detected event ─────────────────────────────────────────────
    elif event_type in ("intent_detected", "intent"):
        intent = body.get("intent") or body.get("name", "unknown")
        confidence = body.get("confidence")
        raw_text = body.get("text") or body.get("raw_text")

        await execute(
            """
            INSERT INTO detected_intents (call_id, intent, confidence, raw_text, detected_at)
            VALUES ($1, $2, $3, $4, NOW())
            """,
            call_id, intent, confidence, raw_text
        )

    return {"status": "ok"}


async def _generate_call_summary(call_id: str) -> dict:
    """
    Analyse tool calls and transcripts to build a post-call summary.
    """
    # What tools were called?
    tools = await fetch_all(
        "SELECT tool_name, input_data FROM tool_calls WHERE call_id = $1 ORDER BY called_at",
        call_id
    )
    tool_names = [t["tool_name"] for t in tools]

    # Determine primary intent
    if "book_demo_class" in tool_names:
        primary_intent = "demo_booking"
    elif "log_student_inquiry" in tool_names:
        primary_intent = "enrollment_inquiry"
    elif "check_scholarship" in tool_names:
        primary_intent = "scholarship_inquiry"
    elif "check_batch_availability" in tool_names:
        primary_intent = "batch_inquiry"
    elif "get_course_details" in tool_names:
        primary_intent = "course_details"
    elif "search_courses" in tool_names:
        primary_intent = "course_search"
    else:
        primary_intent = "general_inquiry"

    # Courses discussed
    courses_discussed = []
    for t in tools:
        if t["tool_name"] in ("search_courses", "get_course_details", "check_batch_availability"):
            input_data = t["input_data"] or {}
            if isinstance(input_data, dict):
                course = input_data.get("course_id") or input_data.get("query")
                if course and course not in courses_discussed:
                    courses_discussed.append(str(course))

    # Check actions taken
    inquiry_logged = "log_student_inquiry" in tool_names
    demo_booked = "book_demo_class" in tool_names
    sms_sent = "send_learning_plan" in tool_names

    # Resolution status
    if demo_booked or inquiry_logged:
        resolution = "resolved"
    elif any(t in tool_names for t in ("search_courses", "get_course_details")):
        resolution = "partial"
    else:
        resolution = "unresolved"

    # Build text summary
    parts = []
    if courses_discussed:
        parts.append(f"Discussed: {', '.join(courses_discussed[:3])}")
    if inquiry_logged:
        parts.append("Inquiry logged for admissions follow-up")
    if demo_booked:
        parts.append("Demo class booked")
    if sms_sent:
        parts.append("Learning plan SMS sent")
    if not parts:
        parts.append("Caller browsed course information")

    return {
        "primary_intent": primary_intent,
        "courses_discussed": courses_discussed,
        "inquiry_logged": inquiry_logged,
        "demo_booked": demo_booked,
        "sms_sent": sms_sent,
        "resolution_status": resolution,
        "summary_text": ". ".join(parts) + ".",
    }
