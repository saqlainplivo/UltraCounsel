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
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0A0A0A;
      --bg2:       #111111;
      --bg3:       #1A1A1A;
      --border:    #27272A;
      --border2:   #3F3F46;
      --acc:       #FC5F2B;
      --acc-hover: #E54E1F;
      --acc-soft:  rgba(252, 95, 43, 0.12);
      --acc-border:rgba(252, 95, 43, 0.4);
      --text:      #FAFAFA;
      --sub:       #A1A1AA;
      --muted:     #71717A;
      --success:   #22c55e;
      --danger:    #ef4444;
      --warning:   #f59e0b;
    }

    html, body {
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: "Inter", "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 16px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    /* ── NAV (matches homepage) ── */
    nav {
      position: sticky; top: 0; z-index: 100;
      background: rgba(10,10,10,0.94);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      padding: 0 2rem;
      height: 64px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .nav-logo {
      font-size: 1.05rem; font-weight: 800; color: var(--text);
      text-decoration: none; letter-spacing: -0.02em;
    }
    .nav-logo span { color: var(--acc); }
    .nav-home {
      font-size: 0.85rem; font-weight: 500; color: var(--sub);
      text-decoration: none; display: flex; align-items: center; gap: 0.3rem;
      transition: color 0.2s;
    }
    .nav-home:hover { color: var(--text); }

    /* ── PAGE SHELL ── */
    .page {
      min-height: calc(100vh - 64px);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem 1rem;
      gap: 1.5rem;
    }

    /* ── PHONE CARD ── */
    .phone-card {
      width: 100%;
      max-width: 380px;
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 2rem;
      box-shadow: 0 24px 64px rgba(0,0,0,0.6);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* ── PHONE TOP BAR ── */
    .phone-topbar {
      display: flex; align-items: center; justify-content: space-between;
      padding: 1rem 1.25rem 0.85rem;
      border-bottom: 1px solid var(--border);
      background: var(--bg3);
    }
    .status-pill {
      display: inline-flex; align-items: center; gap: 0.45rem;
      background: var(--bg2); border: 1px solid var(--border);
      border-radius: 999px; padding: 0.28rem 0.8rem;
      font-size: 0.75rem; font-weight: 600; color: var(--sub);
    }
    .status-dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--muted); flex-shrink: 0;
      transition: background 0.3s;
    }
    .status-pill.connecting .status-dot { background: var(--warning); animation: blink 0.9s step-end infinite; }
    .status-pill.connected  .status-dot { background: var(--success); }
    .status-pill.ended      .status-dot { background: var(--danger); }
    @keyframes blink { 50% { opacity: 0; } }

    .call-timer {
      font-size: 0.75rem; font-weight: 700; color: var(--muted);
      font-variant-numeric: tabular-nums; letter-spacing: 0.04em;
    }
    .call-timer.running { color: var(--success); }

    /* ── CALLER ID ── */
    .caller-id {
      display: flex; flex-direction: column; align-items: center;
      padding: 1.5rem 1.25rem 1rem;
      gap: 0.6rem;
    }
    .caller-avatar {
      width: 64px; height: 64px; border-radius: 50%;
      background: var(--acc);
      display: flex; align-items: center; justify-content: center;
      font-size: 1.6rem; font-weight: 900; color: #fff;
      flex-shrink: 0;
      transition: box-shadow 0.3s;
    }
    .caller-avatar.speaking {
      box-shadow: 0 0 0 4px var(--acc-soft), 0 0 0 8px var(--acc-border);
      animation: ring-pulse 1.1s ease-in-out infinite;
    }
    @keyframes ring-pulse {
      0%,100% { box-shadow: 0 0 0 4px var(--acc-soft), 0 0 0 8px var(--acc-border); }
      50%      { box-shadow: 0 0 0 7px var(--acc-soft), 0 0 0 14px transparent; }
    }
    .caller-name {
      font-size: 1.2rem; font-weight: 800; color: var(--text);
      letter-spacing: -0.02em;
    }
    .caller-sub {
      font-size: 0.78rem; font-weight: 500; color: var(--muted);
    }

    /* ── CHAT WINDOW ── */
    .chat-window {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
      padding: 1rem;
      min-height: 260px;
      max-height: 340px;
      scroll-behavior: smooth;
    }
    .chat-empty {
      margin: auto;
      text-align: center;
      color: var(--muted);
      font-size: 0.82rem;
      font-style: italic;
      line-height: 1.5;
      padding: 1rem;
    }

    /* Message rows */
    .msg-row { display: flex; align-items: flex-end; gap: 0.5rem; }
    .msg-row.sage { justify-content: flex-start; }
    .msg-row.user { justify-content: flex-end; }

    /* Small "S" avatar on Sage rows */
    .msg-av {
      width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
      background: var(--acc);
      display: flex; align-items: center; justify-content: center;
      font-size: 0.65rem; font-weight: 900; color: #fff;
    }

    /* Column: meta label + bubble */
    .msg-col { display: flex; flex-direction: column; max-width: 75%; }
    .msg-row.user .msg-col { align-items: flex-end; }

    .msg-meta {
      font-size: 0.62rem; color: var(--muted);
      padding: 0 0.3rem 0.18rem;
    }

    .msg-bubble {
      padding: 0.6rem 0.85rem;
      border-radius: 1rem;
      font-size: 0.875rem;
      line-height: 1.5;
      word-break: break-word;
    }
    /* Sage bubble — dark card */
    .msg-row.sage .msg-bubble {
      background: var(--bg3);
      border: 1px solid var(--border);
      border-bottom-left-radius: 0.2rem;
      color: var(--text);
    }
    /* Streaming pulse */
    .msg-row.sage .msg-bubble.streaming::after {
      content: " ●";
      color: var(--acc);
      animation: dot-pulse 1s ease-in-out infinite;
    }
    /* User bubble — orange */
    .msg-row.user .msg-bubble {
      background: var(--acc);
      color: #fff;
      border-bottom-right-radius: 0.2rem;
    }
    @keyframes dot-pulse { 0%,100%{opacity:1} 50%{opacity:0.25} }

    /* ── ACTION BAR (bottom of phone card) ── */
    .action-bar {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1.5rem;
      padding: 1.25rem 1.5rem 1.5rem;
      border-top: 1px solid var(--border);
      background: var(--bg3);
    }
    .call-btn {
      width: 64px; height: 64px; border-radius: 50%;
      border: none; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.5rem;
      transition: transform 0.12s, box-shadow 0.2s, opacity 0.2s;
      flex-shrink: 0;
    }
    .call-btn:active { transform: scale(0.93); }
    .call-btn:disabled { opacity: 0.35; cursor: not-allowed; transform: none !important; }

    .call-btn.start {
      background: var(--acc);
      box-shadow: 0 6px 24px rgba(252,95,43,0.45);
    }
    .call-btn.start:hover:not(:disabled) {
      box-shadow: 0 8px 32px rgba(252,95,43,0.6);
      transform: translateY(-2px);
    }
    .call-btn.end {
      background: var(--danger);
      box-shadow: 0 6px 24px rgba(239,68,68,0.35);
    }
    .call-btn.end:hover {
      box-shadow: 0 8px 32px rgba(239,68,68,0.5);
      transform: translateY(-2px);
    }
    .btn-label {
      font-size: 0.7rem; font-weight: 600; color: var(--muted);
      text-align: center; margin-top: 0.3rem;
    }
    .btn-wrap { display: flex; flex-direction: column; align-items: center; }

    /* ── ERROR BOX ── */
    .err-box {
      max-width: 380px; width: 100%;
      background: rgba(239,68,68,0.08);
      border: 1px solid rgba(239,68,68,0.28);
      border-left: 3px solid var(--danger);
      border-radius: 0.65rem;
      padding: 0.7rem 1rem;
      font-size: 0.82rem;
      color: #fca5a5;
      display: none;
    }

    /* ── NOTE ── */
    .page-note {
      font-size: 0.73rem; color: var(--muted); text-align: center;
    }

    @media (max-width: 420px) {
      .phone-card { border-radius: 1.5rem; }
      .chat-window { max-height: 260px; }
    }
  </style>
</head>
<body>

<!-- NAV -->
<nav>
  <a href="/" class="nav-logo">Apex <span>Coaching</span></a>
  <a href="/" class="nav-home">← Home</a>
</nav>

<div class="page">

  <!-- PHONE CARD -->
  <div class="phone-card">

    <!-- Top bar: status + timer -->
    <div class="phone-topbar">
      <div class="status-pill" id="statusPill">
        <div class="status-dot"></div>
        <span id="statusText">Ready</span>
      </div>
      <span class="call-timer" id="callTimer">00:00</span>
    </div>

    <!-- Caller ID -->
    <div class="caller-id">
      <div class="caller-avatar" id="callerAvatar">S</div>
      <div class="caller-name">Sage</div>
      <div class="caller-sub">AI Counsellor · Apex Coaching Institute</div>
    </div>

    <!-- Chat window -->
    <div class="chat-window" id="chat">
      <div class="chat-empty" id="chatEmpty">Tap the call button to connect with Sage 📞</div>
    </div>

    <!-- Action bar -->
    <div class="action-bar">
      <div class="btn-wrap">
        <button class="call-btn start" id="talkBtn" onclick="startCall()">📞</button>
        <div class="btn-label">Call Sage</div>
      </div>
      <div class="btn-wrap" id="endWrap" style="display:none">
        <button class="call-btn end" id="endBtn" onclick="endCall()">✕</button>
        <div class="btn-label">End Call</div>
      </div>
    </div>

  </div>

  <!-- Error box (outside phone card) -->
  <div class="err-box" id="errBox"></div>

  <p class="page-note">Requires microphone access · Best in Chrome or Edge</p>

</div>

<script type="module">
  import { UltravoxSession } from "https://esm.sh/ultravox-client";

  // ── State ──────────────────────────────────────────────────────────────────
  let uv        = null;
  let timerInt  = null;
  let timerSecs = 0;

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const talkBtn    = document.getElementById("talkBtn");
  const endBtn     = document.getElementById("endBtn");
  const endWrap    = document.getElementById("endWrap");
  const pill       = document.getElementById("statusPill");
  const statusTxt  = document.getElementById("statusText");
  const timerEl    = document.getElementById("callTimer");
  const chat       = document.getElementById("chat");
  const chatEmpty  = document.getElementById("chatEmpty");
  const errBox     = document.getElementById("errBox");
  const avatar     = document.getElementById("callerAvatar");

  // ── Helpers ────────────────────────────────────────────────────────────────
  function setStatus(text, cls) {
    statusTxt.textContent = text;
    pill.className = "status-pill " + (cls || "");
  }

  function showErr(msg) {
    errBox.textContent = "⚠  " + msg;
    errBox.style.display = "block";
  }
  function clearErr() { errBox.style.display = "none"; }

  function startTimer() {
    timerSecs = 0;
    timerEl.className = "call-timer running";
    timerInt = setInterval(() => {
      timerSecs++;
      const m = String(Math.floor(timerSecs / 60)).padStart(2, "0");
      const s = String(timerSecs % 60).padStart(2, "0");
      timerEl.textContent = m + ":" + s;
    }, 1000);
  }
  function stopTimer() {
    clearInterval(timerInt);
    timerEl.className = "call-timer";
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // ── upsertTurn — chat bubble logic ─────────────────────────────────────────
  function upsertTurn(role, text, isFinal) {
    const isAgent = (role === "agent");

    // Hide the empty placeholder once we have content
    if (chatEmpty) chatEmpty.style.display = "none";

    // Look for an in-progress row for this role (data-final="0")
    const rowClass = isAgent ? "sage" : "user";
    let row = chat.querySelector(".msg-row." + rowClass + "[data-final='0']");

    if (!row) {
      // Build new row
      row = document.createElement("div");
      row.className = "msg-row " + rowClass;
      row.dataset.role  = role;
      row.dataset.final = "0";

      if (isAgent) {
        // Small avatar circle
        const av = document.createElement("div");
        av.className = "msg-av";
        av.textContent = "S";
        row.appendChild(av);
      }

      const col = document.createElement("div");
      col.className = "msg-col";

      const meta = document.createElement("div");
      meta.className = "msg-meta";
      meta.textContent = isAgent ? "Sage" : "You";
      col.appendChild(meta);

      const bubble = document.createElement("div");
      bubble.className = "msg-bubble" + (isFinal ? "" : " streaming");
      bubble.textContent = text;
      col.appendChild(bubble);

      row.appendChild(col);
      chat.appendChild(row);
    } else {
      // Update existing streaming row
      const bubble = row.querySelector(".msg-bubble");
      bubble.textContent = text;
      if (isFinal) bubble.classList.remove("streaming");
    }

    if (isFinal) row.dataset.final = "1";
    chat.scrollTop = chat.scrollHeight;
  }

  // ── startCall ──────────────────────────────────────────────────────────────
  window.startCall = async function () {
    clearErr();
    talkBtn.disabled = true;
    setStatus("Requesting mic…");

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (_) {
      showErr("Microphone access denied. Please allow mic and try again.");
      talkBtn.disabled = false;
      setStatus("Ready");
      return;
    }

    setStatus("Connecting…", "connecting");

    let joinUrl;
    try {
      const res  = await fetch("/api/test-session", { method: "POST" });
      const data = await res.json();
      if (!res.ok || !data.joinUrl) throw new Error(data.error || "No joinUrl returned");
      joinUrl = data.joinUrl;
    } catch (e) {
      showErr("Could not start session: " + e.message);
      talkBtn.disabled = false;
      setStatus("Ready");
      return;
    }

    uv = new UltravoxSession();

    uv.addEventListener("status", () => {
      const s = uv.status;
      if (s === "connected") {
        setStatus("On Call", "connected");
        // Show end button, hide start button
        document.getElementById("talkBtn").parentElement.style.display = "none";
        endWrap.style.display = "";
        startTimer();
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
      // Toggle speaking ring on caller avatar
      avatar.classList.toggle("speaking", role === "agent" && !t.isFinal);
    });

    try {
      await uv.joinCall(joinUrl);
    } catch (e) {
      showErr("Connection failed: " + e.message);
      uv = null;
      talkBtn.disabled = false;
      document.getElementById("talkBtn").parentElement.style.display = "";
      endWrap.style.display = "none";
      setStatus("Ready");
    }
  };

  // ── endCall ────────────────────────────────────────────────────────────────
  window.endCall = function () {
    if (uv) { try { uv.leaveCall(); } catch (_) {} uv = null; }
    onEnded();
  };

  function onEnded() {
    uv = null;
    stopTimer();
    avatar.classList.remove("speaking");
    setStatus("Call Ended", "ended");
    talkBtn.disabled = false;
    document.getElementById("talkBtn").parentElement.style.display = "";
    endWrap.style.display = "none";
  }
</script>
</body>
</html>"""
