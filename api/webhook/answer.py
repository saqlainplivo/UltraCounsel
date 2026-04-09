"""
api/webhook/answer.py
Plivo inbound call webhook — entry point for every call to Apex Coaching Institute.

Flow:
1. Plivo sends form params for the inbound call
2. We hash the caller's number and check for prior sessions
3. We create an Ultravox session for Sage with session context
4. We return Plivo XML to stream call audio to the Ultravox WebSocket
"""

import os
import logging
from fastapi import APIRouter, Form, Response
from typing import Optional

from lib.security import hash_phone_number, mask_phone
from lib.session_manager import get_or_create_caller, build_caller_context
from lib.ultravox import create_ultravox_session
from lib.plivo_client import build_stream_xml, build_hangup_xml
from lib.db import execute

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/answer")
async def handle_answer(
    CallUUID: str = Form(...),
    From:     str = Form(...),
    To:       Optional[str] = Form(None),
    Direction: Optional[str] = Form(None),
):
    """
    Handles Plivo inbound call webhook.
    Returns Plivo XML to stream audio to Ultravox.
    """
    base_url = os.getenv("APP_BASE_URL", "https://your-deployment.vercel.app")

    try:
        # 1. Hash the caller's phone number — NEVER store raw
        phone_hash = hash_phone_number(From)
        masked_phone = mask_phone(From)

        logger.info(f"Inbound call {CallUUID} from {masked_phone}")

        # 2. Get or create caller profile (increments call count)
        await get_or_create_caller(From)

        # 3. Build context from prior sessions
        caller_context = await build_caller_context(phone_hash)

        # 4. Log the call (with masked number only)
        await execute(
            """
            INSERT INTO call_logs (call_uuid, caller_hash, caller_masked, to_number,
                direction, status, started_at)
            VALUES ($1, $2, $3, $4, $5, 'in-progress', NOW())
            ON CONFLICT (call_uuid) DO NOTHING
            """,
            CallUUID,
            phone_hash,
            masked_phone,
            To or "",
            Direction or "inbound",
        )

        # 5. Create Ultravox session for Sage
        websocket_url = await create_ultravox_session(
            caller_context=caller_context,
            base_url=base_url,
            call_uuid=CallUUID,
        )

        logger.info(f"Ultravox session created for call {CallUUID}")

        # 6. Return stream XML to Plivo
        xml_response = build_stream_xml(websocket_url)
        return Response(content=xml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error handling call {CallUUID}: {e}", exc_info=True)

        # Update call status on error
        try:
            await execute(
                "UPDATE call_logs SET status = 'error' WHERE call_uuid = $1",
                CallUUID
            )
        except Exception:
            pass

        # Return graceful hangup XML
        hangup_xml = build_hangup_xml(
            "Thank you for calling Apex Coaching Institute. We're experiencing a technical issue right now. "
            "Please try again in a few minutes or WhatsApp us directly."
        )
        return Response(content=hangup_xml, media_type="application/xml")
