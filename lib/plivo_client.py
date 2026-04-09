"""
lib/plivo_client.py
Plivo client helpers: XML builders and async SMS sender for UltraCounsel.
"""

import os
import asyncio
import plivo
from functools import lru_cache


@lru_cache(maxsize=1)
def get_plivo_client() -> plivo.RestClient:
    """Return a cached Plivo REST client."""
    return plivo.RestClient(
        auth_id=os.getenv("PLIVO_AUTH_ID"),
        auth_token=os.getenv("PLIVO_AUTH_TOKEN"),
    )


def build_stream_xml(websocket_url: str) -> str:
    """
    Build Plivo XML to stream call audio to an Ultravox WebSocket.
    bidirectional=true allows Ultravox to send audio back to the caller.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Stream keepCallAlive="true" bidirectional="true" contentType="audio/x-mulaw;rate=8000">
    {websocket_url}
  </Stream>
</Response>"""


def build_hangup_xml(message: str = "") -> str:
    """Build Plivo XML to speak a message and hang up."""
    if message:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Speak voice="Polly.Aditi" language="en-IN">{message}</Speak>
  <Hangup/>
</Response>"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Hangup/>
</Response>"""


async def send_sms(to_number: str, message: str) -> dict:
    """
    Send an SMS via Plivo. Runs the blocking SDK call in a thread pool.
    Returns the Plivo API response dict.
    """
    client = get_plivo_client()
    from_number = os.getenv("PLIVO_PHONE_NUMBER")

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.messages.create(
            src=from_number,
            dst=to_number,
            text=message,
        )
    )
    return response
