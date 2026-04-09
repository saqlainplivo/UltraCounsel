"""
lib/session_manager.py
Manages caller profiles and session history for UltraCounsel.
Phone numbers are NEVER stored raw — only hashed.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from lib.db import fetch_one, execute
from lib.security import hash_phone_number


async def get_or_create_caller(raw_phone: str) -> Dict[str, Any]:
    """
    Look up (or create) a caller profile by hashed phone number.
    Returns a dict with profile data.
    """
    phone_hash = hash_phone_number(raw_phone)

    row = await fetch_one(
        "SELECT * FROM caller_profiles WHERE phone_hash = $1",
        phone_hash
    )

    if row:
        await execute(
            """
            UPDATE caller_profiles
            SET total_calls = total_calls + 1,
                last_seen_at = NOW()
            WHERE phone_hash = $1
            """,
            phone_hash
        )
        return dict(row)
    else:
        await execute(
            """
            INSERT INTO caller_profiles (phone_hash, total_calls, first_seen_at, last_seen_at)
            VALUES ($1, 1, NOW(), NOW())
            """,
            phone_hash
        )
        row = await fetch_one(
            "SELECT * FROM caller_profiles WHERE phone_hash = $1",
            phone_hash
        )
        return dict(row)


async def build_caller_context(phone_hash: str) -> Dict[str, Any]:
    """
    Build a safe context dict from previous sessions.
    Used to inject context into Sage's system prompt.
    Returns a dict that is SAFE — no raw phone, no PII.
    """
    profile = await fetch_one(
        "SELECT total_calls, first_seen_at FROM caller_profiles WHERE phone_hash = $1",
        phone_hash
    )

    if not profile or profile["total_calls"] <= 1:
        return {
            "returning_caller": False,
            "total_calls": 1,
            "previous_inquiries": [],
            "last_course_interest": None,
        }

    # Get last 3 sessions
    sessions = await fetch_one(
        """
        SELECT topics_discussed, inquiry_ref
        FROM caller_sessions
        WHERE phone_hash = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        phone_hash
    )

    # Get recent inquiries
    inquiries = await fetch_one(
        """
        SELECT inquiry_ref, interested_course, class_or_target, status
        FROM student_inquiries
        WHERE caller_hash = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        phone_hash
    )

    last_course = None
    inquiry_ref = None
    if inquiries:
        last_course = inquiries["interested_course"]
        inquiry_ref = inquiries["inquiry_ref"]

    topics = []
    if sessions and sessions["topics_discussed"]:
        topics = sessions["topics_discussed"] if isinstance(sessions["topics_discussed"], list) else []

    return {
        "returning_caller": True,
        "total_calls": profile["total_calls"],
        "previous_topics": topics[:5],  # last 5 topics only
        "last_course_interest": last_course,
        "last_inquiry_ref": inquiry_ref,
    }


async def save_caller_session(
    phone_hash: str,
    call_id: str,
    topics_discussed: list,
    courses_recommended: list,
    inquiry_ref: Optional[str] = None
) -> None:
    """Save a session summary after a call ends."""
    await execute(
        """
        INSERT INTO caller_sessions
            (phone_hash, call_id, topics_discussed, courses_recommended, inquiry_ref, created_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        """,
        phone_hash,
        call_id,
        topics_discussed,
        courses_recommended,
        inquiry_ref,
    )


async def purge_old_sessions(retention_days: int = 90) -> int:
    """Delete sessions older than retention_days. Returns count deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await execute(
        "DELETE FROM caller_sessions WHERE created_at < $1",
        cutoff
    )
    # asyncpg returns "DELETE N" as a string
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0
