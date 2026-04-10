"""
api/test.py
Browser-based voice chat test page for UltraCounsel.

GET  /test              → serves the browser voice chat UI
POST /api/test-session  → creates an Ultravox session and returns joinUrl
"""

import logging
import os
import time

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from lib.ultravox import create_ultravox_session

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Mock caller context (no DB, no phone number needed) ───────────────────────

MOCK_CALLER_CONTEXT = {
    "returning_caller": False,
    "total_calls": 1,
    "previous_topics": [],
    "last_course_interest": None,
    "last_inquiry_ref": None,
    "source": "browser_test",
}


# ── POST /api/test-session ────────────────────────────────────────────────────

@router.post("/api/test-session")
async def create_test_session():
    """
    Create an Ultravox session for browser-based WebRTC calling.
    Returns the joinUrl (wss://) that the ultravox-client SDK connects to.
    No phone number or DB required — uses mock caller context.
    """
    try:
        base_url = os.getenv("APP_BASE_URL", "https://ultracounsel.vercel.app")
        call_uuid = f"browser-test-{int(time.time())}"
        join_url = await create_ultravox_session(MOCK_CALLER_CONTEXT, base_url, call_uuid)
        return JSONResponse({"joinUrl": join_url})
    except Exception as exc:
        logger.error(f"Failed to create browser test session: {exc}", exc_info=True)
        return JSONResponse({"error": str(exc)}, status_code=500)


# ── GET /test ─────────────────────────────────────────────────────────────────

@router.get("/test", response_class=HTMLResponse)
async def test_page():
    """Serves the browser-based voice chat UI for testing Sage."""
    return HTMLResponse(content=TEST_PAGE_HTML)


# ── HTML ──────────────────────────────────────────────────────────────────────

TEST_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Talk to Sage — Apex Coaching Institute</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:           #0a0a0f;
      --surface:      #13131c;
      --surface2:     #1a1a26;
      --border:       #25253a;
      --accent:       #7c3aed;
      --accent-light: #a855f7;
      --accent-glow:  rgba(124, 58, 237, 0.4);
      --text:         #eeeef8;
      --muted:        #888899;
      --success:      #22c55e;
      --danger:       #ef4444;
      --warning:      #f59e0b;
    }

    html, body {
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      line-height: 1.6;
    }

    /* grid background */
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
      z-index: 0;
    }

    .app {
      position: relative;
      z-index: 1;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem 1.25rem;
      gap: 1.5rem;
    }

    /* ── Header ── */
    .header { text-align: center; }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.75rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 0.35rem 1rem;
      margin-bottom: 1rem;
    }
    .eyebrow-dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--accent-light);
      box-shadow: 0 0 8px var(--accent-light);
    }

    h1 {
      font-size: clamp(2rem, 6vw, 3.2rem);
      font-weight: 900;
      letter-spacing: -0.04em;
      background: linear-gradient(135deg, #fff 0%, var(--accent-light) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .subtitle { color: var(--muted); font-size: 0.95rem; margin-top: 0.4rem; }

    /* ── Card ── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 1.5rem;
      padding: 2.5rem 2rem;
      width: 100%;
      max-width: 520px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1.5rem;
      box-shadow: 0 0 60px rgba(124,58,237,0.07);
    }

    /* ── Orb ── */
    .orb {
      width: 110px; height: 110px;
      border-radius: 50%;
      background: radial-gradient(circle at 38% 38%, var(--accent-light), var(--accent) 55%, #160830);
      display: flex; align-items: center; justify-content: center;
      font-size: 2.8rem;
      flex-shrink: 0;
      transition: box-shadow 0.3s;
    }
    .orb.speaking {
      animation: orb-pulse 1.1s ease-out infinite;
    }
    @keyframes orb-pulse {
      0%   { box-shadow: 0 0 0 0   var(--accent-glow); }
      70%  { box-shadow: 0 0 0 22px rgba(124,58,237,0); }
      100% { box-shadow: 0 0 0 0   rgba(124,58,237,0); }
    }

    /* ── Status ── */
    .status {
      display: inline-flex; align-items: center; gap: 0.5rem;
      font-size: 0.82rem;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 0.3rem 0.9rem;
    }
    .status-dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--muted);
      transition: background 0.3s;
    }
    .status.connecting .status-dot { background: var(--warning); animation: blink 0.9s step-end infinite; }
    .status.connected  .status-dot { background: var(--success); }
    .status.ended      .status-dot { background: var(--danger); }
    @keyframes blink { 50% { opacity: 0; } }

    /* ── Transcript ── */
    .transcript {
      width: 100%;
      min-height: 150px; max-height: 300px;
      overflow-y: auto;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 0.85rem;
      padding: 1rem 1.1rem;
      font-size: 0.88rem;
      line-height: 1.65;
      scroll-behavior: smooth;
    }
    .transcript:empty::before {
      content: "Transcript will appear here once connected…";
      color: var(--muted);
      font-style: italic;
    }
    .turn { margin-bottom: 0.8rem; }
    .turn-label {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.09em;
      margin-bottom: 0.15rem;
    }
    .turn.sage .turn-label { color: var(--accent-light); }
    .turn.user .turn-label { color: var(--muted); }
    .turn-text { color: var(--text); }

    /* ── Buttons ── */
    .btn {
      display: inline-flex; align-items: center; gap: 0.5rem;
      padding: 0.85rem 2rem;
      border-radius: 0.75rem;
      font-size: 0.95rem;
      font-weight: 700;
      cursor: pointer;
      border: none;
      transition: transform 0.12s, opacity 0.12s, box-shadow 0.12s;
    }
    .btn:active { transform: scale(0.97); }
    .btn-primary {
      background: linear-gradient(135deg, var(--accent), var(--accent-light));
      color: #fff;
      box-shadow: 0 4px 22px var(--accent-glow);
    }
    .btn-primary:hover { box-shadow: 0 6px 32px var(--accent-glow); transform: translateY(-1px); }
    .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; transform: none; box-shadow: none; }
    .btn-end {
      background: var(--surface2);
      border: 1.5px solid var(--danger);
      color: var(--danger);
    }
    .btn-end:hover { background: rgba(239,68,68,0.1); }

    .btn-row { display: flex; gap: 0.75rem; align-items: center; }

    /* ── Error ── */
    .err {
      width: 100%;
      background: rgba(239,68,68,0.08);
      border: 1px solid rgba(239,68,68,0.3);
      border-radius: 0.6rem;
      padding: 0.7rem 1rem;
      font-size: 0.84rem;
      color: #fca5a5;
      display: none;
    }

    /* ── Note ── */
    .note { font-size: 0.76rem; color: var(--muted); text-align: center; }

    /* ── Back link ── */
    .back {
      color: var(--muted); font-size: 0.82rem; text-decoration: none;
      display: inline-flex; align-items: center; gap: 0.3rem;
      transition: color 0.2s;
    }
    .back:hover { color: var(--text); }

    @media (max-width: 480px) {
      .card { padding: 1.75rem 1.1rem; }
    }
  </style>
</head>
<body>
<div class="app">

  <!-- Header -->
  <div class="header">
    <div class="eyebrow"><span class="eyebrow-dot"></span> Apex Coaching Institute</div>
    <h1>Talk to Sage</h1>
    <p class="subtitle">AI Voice Counsellor &nbsp;·&nbsp; Powered by Ultravox</p>
  </div>

  <!-- Card -->
  <div class="card">
    <div class="orb" id="orb">🎓</div>

    <div class="status" id="statusBadge">
      <div class="status-dot"></div>
      <span id="statusText">Ready to connect</span>
    </div>

    <div class="transcript" id="transcript"></div>

    <div class="err" id="errBox"></div>

    <div class="btn-row">
      <button class="btn btn-primary" id="talkBtn" onclick="startCall()">
        🎙️ Talk to Sage
      </button>
      <button class="btn btn-end" id="endBtn" style="display:none" onclick="endCall()">
        ✕ End Call
      </button>
    </div>

    <p class="note">Requires microphone access &nbsp;·&nbsp; Best in Chrome / Edge</p>
  </div>

  <a href="/" class="back">← Back to home</a>
</div>

<script type="module">
  import { UltravoxSession } from "https://esm.sh/ultravox-client";

  // ── State ──────────────────────────────────────────────────────────────────
  let uv = null;

  // ── DOM ────────────────────────────────────────────────────────────────────
  const talkBtn   = document.getElementById("talkBtn");
  const endBtn    = document.getElementById("endBtn");
  const badge     = document.getElementById("statusBadge");
  const statusTxt = document.getElementById("statusText");
  const transcript= document.getElementById("transcript");
  const errBox    = document.getElementById("errBox");
  const orb       = document.getElementById("orb");

  // ── Helpers ────────────────────────────────────────────────────────────────
  function setStatus(text, cls) {
    statusTxt.textContent = text;
    badge.className = "status " + (cls || "");
  }

  function showErr(msg) {
    errBox.textContent = "⚠ " + msg;
    errBox.style.display = "block";
  }

  function clearErr() {
    errBox.style.display = "none";
  }

  function esc(s) {
    return String(s)
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;");
  }

  function upsertTurn(role, text, isFinal) {
    // find last pending turn for this role
    const last = transcript.lastElementChild;
    if (last && last.dataset.role === role && last.dataset.final === "0") {
      last.querySelector(".turn-text").textContent = text;
    } else {
      const div = document.createElement("div");
      div.className = "turn " + (role === "agent" ? "sage" : "user");
      div.dataset.role  = role;
      div.dataset.final = "0";
      div.innerHTML =
        "<div class=\\"turn-label\\">" + (role === "agent" ? "Sage" : "You") + "</div>" +
        "<div class=\\"turn-text\\">" + esc(text) + "</div>";
      transcript.appendChild(div);
    }
    if (isFinal) {
      transcript.lastElementChild.dataset.final = "1";
    }
    transcript.scrollTop = transcript.scrollHeight;
  }

  // ── startCall ──────────────────────────────────────────────────────────────
  window.startCall = async function () {
    clearErr();
    talkBtn.disabled = true;
    setStatus("Requesting microphone…");

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (_) {
      showErr("Microphone access denied. Please allow mic and try again.");
      talkBtn.disabled = false;
      setStatus("Ready to connect");
      return;
    }

    setStatus("Creating session…", "connecting");

    let joinUrl;
    try {
      const res  = await fetch("/api/test-session", { method: "POST" });
      const data = await res.json();
      if (!res.ok || !data.joinUrl) throw new Error(data.error || "No joinUrl returned");
      joinUrl = data.joinUrl;
    } catch (e) {
      showErr("Could not start session: " + e.message);
      talkBtn.disabled = false;
      setStatus("Ready to connect");
      return;
    }

    setStatus("Connecting to Sage…", "connecting");
    uv = new UltravoxSession();

    uv.addEventListener("status", () => {
      const s = uv.status;
      if (s === "connected") {
        setStatus("Connected", "connected");
        talkBtn.style.display = "none";
        endBtn.style.display  = "";
      } else if (s === "disconnected" || s === "idle" || s === "ended") {
        onEnded();
      }
    });

    uv.addEventListener("transcripts", () => {
      const txs = uv.transcripts;
      if (!txs || !txs.length) return;
      const t = txs[txs.length - 1];
      if (!t || !t.text) return;
      const role = (t.role === "agent") ? "agent" : "user";
      upsertTurn(role, t.text, !!t.isFinal);
      orb.classList.toggle("speaking", role === "agent" && !t.isFinal);
    });

    try {
      await uv.joinCall(joinUrl);
    } catch (e) {
      showErr("Connection failed: " + e.message);
      uv = null;
      talkBtn.disabled = false;
      talkBtn.style.display = "";
      endBtn.style.display  = "none";
      setStatus("Ready to connect");
    }
  };

  // ── endCall ────────────────────────────────────────────────────────────────
  window.endCall = function () {
    if (uv) { try { uv.leaveCall(); } catch (_) {} uv = null; }
    onEnded();
  };

  function onEnded() {
    uv = null;
    orb.classList.remove("speaking");
    setStatus("Call ended", "ended");
    talkBtn.disabled = false;
    talkBtn.style.display = "";
    endBtn.style.display  = "none";
  }
</script>
</body>
</html>"""
