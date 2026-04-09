"""
api/calls.py
Analytics endpoints: call logs, summaries, and aggregate metrics.
"""

from fastapi import APIRouter, Query
from typing import Optional

from lib.db import fetch_all, fetch_one

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/calls")
async def list_calls(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
):
    """List call logs with pagination."""
    offset = (page - 1) * limit
    if status:
        rows = await fetch_all(
            """
            SELECT call_uuid, caller_masked, direction, status,
                   started_at, ended_at, duration_seconds
            FROM call_logs
            WHERE status = $1
            ORDER BY started_at DESC
            LIMIT $2 OFFSET $3
            """,
            status, limit, offset
        )
    else:
        rows = await fetch_all(
            """
            SELECT call_uuid, caller_masked, direction, status,
                   started_at, ended_at, duration_seconds
            FROM call_logs
            ORDER BY started_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset
        )
    return {"calls": [dict(r) for r in rows], "page": page, "limit": limit}


@router.get("/calls/{call_uuid}")
async def get_call(call_uuid: str):
    """Get full details of a specific call including transcript and tool calls."""
    call = await fetch_one(
        "SELECT * FROM call_logs WHERE call_uuid = $1",
        call_uuid
    )
    if not call:
        return {"error": "Call not found"}

    transcript = await fetch_all(
        "SELECT role, content, timestamp FROM transcripts WHERE call_id = $1 ORDER BY timestamp",
        call_uuid
    )
    tools = await fetch_all(
        "SELECT tool_name, input_data, output_data, success, duration_ms, called_at FROM tool_calls WHERE call_id = $1 ORDER BY called_at",
        call_uuid
    )
    intents = await fetch_all(
        "SELECT intent, confidence, detected_at FROM detected_intents WHERE call_id = $1",
        call_uuid
    )
    summary = await fetch_one(
        "SELECT * FROM call_summaries WHERE call_id = $1",
        call_uuid
    )

    return {
        "call": dict(call),
        "transcript": [dict(t) for t in transcript],
        "tool_calls": [dict(t) for t in tools],
        "intents": [dict(i) for i in intents],
        "summary": dict(summary) if summary else None,
    }


@router.get("/calls/{call_uuid}/summary")
async def get_call_summary(call_uuid: str):
    """Get the summary for a specific call."""
    summary = await fetch_one(
        "SELECT * FROM call_summaries WHERE call_id = $1",
        call_uuid
    )
    return {"summary": dict(summary) if summary else None}


@router.get("/analytics")
async def get_analytics():
    """Aggregate metrics for the UltraCounsel dashboard."""
    total_calls = await fetch_one("SELECT COUNT(*) AS cnt FROM call_logs")
    total_inquiries = await fetch_one("SELECT COUNT(*) AS cnt FROM student_inquiries")
    demos_booked = await fetch_one("SELECT COUNT(*) AS cnt FROM demo_bookings")
    sms_sent = await fetch_one("SELECT COUNT(*) AS cnt FROM communications_sent WHERE status = 'sent'")
    avg_duration = await fetch_one(
        "SELECT ROUND(AVG(duration_seconds)) AS avg_secs FROM call_logs WHERE duration_seconds IS NOT NULL"
    )

    # Most popular courses discussed
    top_courses = await fetch_all(
        """
        SELECT interested_course, COUNT(*) AS inquiries
        FROM student_inquiries
        WHERE interested_course IS NOT NULL
        GROUP BY interested_course
        ORDER BY inquiries DESC
        LIMIT 5
        """
    )

    # Lead stage breakdown
    lead_stages = await fetch_all(
        """
        SELECT lead_stage, COUNT(*) AS count
        FROM student_inquiries
        GROUP BY lead_stage
        ORDER BY count DESC
        """
    )

    # Tool usage stats
    tool_usage = await fetch_all(
        """
        SELECT tool_name, COUNT(*) AS calls,
               ROUND(AVG(duration_ms)) AS avg_ms
        FROM tool_calls
        GROUP BY tool_name
        ORDER BY calls DESC
        """
    )

    # Recent inquiries
    recent_inquiries = await fetch_all(
        """
        SELECT inquiry_ref, student_name, interested_course,
               class_or_target, lead_stage, created_at
        FROM student_inquiries
        ORDER BY created_at DESC
        LIMIT 10
        """
    )

    return {
        "overview": {
            "total_calls": total_calls["cnt"] if total_calls else 0,
            "total_inquiries": total_inquiries["cnt"] if total_inquiries else 0,
            "demos_booked": demos_booked["cnt"] if demos_booked else 0,
            "sms_sent": sms_sent["cnt"] if sms_sent else 0,
            "avg_call_duration_seconds": avg_duration["avg_secs"] if avg_duration else 0,
        },
        "top_courses": [dict(r) for r in top_courses],
        "lead_stages": [dict(r) for r in lead_stages],
        "tool_usage": [dict(r) for r in tool_usage],
        "recent_inquiries": [dict(r) for r in recent_inquiries],
    }


@router.get("/inquiries")
async def list_inquiries(
    stage: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """List student inquiries, optionally filtered by lead stage."""
    if stage:
        rows = await fetch_all(
            """
            SELECT inquiry_ref, student_name, interested_course,
                   class_or_target, preferred_timing, preferred_branch,
                   lead_stage, status, created_at
            FROM student_inquiries
            WHERE lead_stage = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            stage, limit
        )
    else:
        rows = await fetch_all(
            """
            SELECT inquiry_ref, student_name, interested_course,
                   class_or_target, preferred_timing, preferred_branch,
                   lead_stage, status, created_at
            FROM student_inquiries
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )
    return {"inquiries": [dict(r) for r in rows]}
