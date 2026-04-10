"""
main.py
UltraCounsel — Apex Coaching Institute Voice Counsellor Agent
Built with Ultravox + Plivo + FastAPI

Sage is a voice AI counsellor who helps students find the right coaching
course, understand the syllabus, check batch availability, explore
scholarships, and book free demo classes.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from lib.db import create_pool, close_pool
from api.webhook.answer import router as answer_router
from api.webhook.events import router as events_router
from api.tools import router as tools_router
from api.calls import router as calls_router
from api.test import router as test_router

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB pool. Shutdown: close pool."""
    logger.info("🚀 UltraCounsel starting up...")

    # Connect to database
    await create_pool()
    logger.info("✅ Database pool ready")

    yield

    # Cleanup
    await close_pool()
    logger.info("👋 UltraCounsel shut down cleanly")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="UltraCounsel — Apex Coaching Institute",
    description="Voice AI counsellor for Apex Coaching Institute. Powered by Ultravox + Plivo.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(answer_router)
app.include_router(events_router)
app.include_router(tools_router)
app.include_router(calls_router)
app.include_router(test_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    """Health check endpoint for Vercel and monitoring."""
    return {
        "status": "healthy",
        "service": "UltraCounsel",
        "agent": "Sage",
        "institute": os.getenv("INSTITUTE_NAME", "Apex Coaching Institute"),
        "version": "1.0.0",
        "app_base_url": os.getenv("APP_BASE_URL", "NOT SET"),
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=LANDING_PAGE_HTML)


# ── Landing page HTML ─────────────────────────────────────────────────────────

LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sage — AI Counsellor | Apex Coaching Institute</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:       #07070f;
      --surf:     #0e0e1c;
      --surf2:    #14142a;
      --border:   #1f1f38;
      --acc:      #7c3aed;
      --acc2:     #2563eb;
      --gold:     #f59e0b;
      --text:     #f0f0fa;
      --muted:    #7070a0;
      --card:     rgba(14,14,28,0.85);
    }
    html { scroll-behavior: smooth; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      line-height: 1.65;
      overflow-x: hidden;
    }

    /* ── Blobs ── */
    .blobs { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
    .blob  { position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.16; }
    .b1    { width:700px;height:700px;background:var(--acc); top:-250px;left:-200px;animation:drift 20s ease-in-out infinite alternate; }
    .b2    { width:600px;height:600px;background:var(--acc2);bottom:-200px;right:-150px;animation:drift 25s ease-in-out infinite alternate-reverse; }
    .b3    { width:400px;height:400px;background:var(--gold);top:42%;left:58%;animation:drift 16s ease-in-out infinite alternate; }
    @keyframes drift { to { transform: translate(50px,50px) scale(1.1); } }

    /* ── Shared layout ── */
    section, header, footer, nav { position: relative; z-index: 1; }
    .inner { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; }

    /* ── Nav ── */
    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      padding: 1rem 2rem;
      display: flex; align-items: center; justify-content: space-between;
      backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
      background: rgba(7,7,15,0.72);
      border-bottom: 1px solid var(--border);
    }
    .nav-brand {
      font-size: 1.05rem; font-weight: 900; letter-spacing: -0.02em;
      background: linear-gradient(90deg,#fff,var(--acc));
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
      text-decoration: none;
    }
    .nav-links { list-style:none; display:flex; gap:2rem; }
    .nav-links a { color:var(--muted); text-decoration:none; font-size:0.9rem; transition:color 0.2s; }
    .nav-links a:hover { color:var(--text); }
    .nav-cta {
      background: linear-gradient(135deg, var(--acc), #9333ea);
      color: #fff !important;
      padding: 0.5rem 1.2rem;
      border-radius: 0.55rem;
      font-weight: 700;
      text-decoration: none !important;
      font-size: 0.88rem;
      transition: opacity 0.2s, transform 0.15s;
    }
    .nav-cta:hover { opacity: 0.85; transform: translateY(-1px); }

    /* ── Hero ── */
    .hero {
      min-height: 100vh;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      text-align: center;
      padding: 8rem 1.5rem 5rem;
    }
    .hero-badge {
      display: inline-flex; align-items: center; gap: 0.45rem;
      font-size: 0.75rem; letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--muted); background: var(--surf); border: 1px solid var(--border);
      border-radius: 999px; padding: 0.38rem 1rem; margin-bottom: 2rem;
    }
    .live-dot { width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 7px #22c55e;display:inline-block; }
    .hero h1 {
      font-size: clamp(3rem,9vw,6.5rem);
      font-weight: 900; letter-spacing: -0.05em; line-height: 1;
      background: linear-gradient(135deg,#fff 0%,#c4b5fd 45%,var(--acc) 100%);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    }
    .hero-sub-head {
      font-size: clamp(1.4rem,4vw,2.8rem);
      font-weight: 800; letter-spacing: -0.03em;
      color: #a78bfa; margin-top: 0.2rem;
    }
    .hero-desc {
      font-size: clamp(0.95rem,2vw,1.2rem);
      color: var(--muted); max-width: 540px; margin: 1.2rem auto 2.5rem;
    }
    .hero-desc .hl { color: #a78bfa; font-weight: 600; }
    .cursor { display:inline-block;width:2px;height:1em;background:var(--acc);margin-left:2px;vertical-align:middle;animation:cur 0.9s step-end infinite; }
    @keyframes cur { 50%{opacity:0;} }
    .hero-btns { display:flex; gap:1rem; flex-wrap:wrap; justify-content:center; }
    .btn-main {
      display:inline-flex; align-items:center; gap:0.55rem;
      padding: 0.95rem 2.3rem;
      background: linear-gradient(135deg,var(--acc),#9333ea);
      color: #fff; border-radius: 0.8rem; font-weight: 700; font-size: 1.05rem;
      text-decoration: none;
      box-shadow: 0 8px 34px rgba(124,58,237,0.45);
      transition: transform 0.15s, box-shadow 0.15s;
    }
    .btn-main:hover { transform:translateY(-3px); box-shadow:0 14px 44px rgba(124,58,237,0.55); }
    .btn-ghost {
      display:inline-flex; align-items:center; gap:0.55rem;
      padding: 0.95rem 2rem;
      color: var(--text); border: 1.5px solid var(--border);
      border-radius: 0.8rem; font-weight: 600; font-size: 1.05rem;
      text-decoration: none;
      transition: border-color 0.2s, background 0.2s, transform 0.15s;
    }
    .btn-ghost:hover { border-color:var(--acc); background:rgba(124,58,237,0.08); transform:translateY(-2px); }

    /* ── Stats ── */
    .stats {
      display: flex; justify-content: center; flex-wrap: wrap; gap: 3rem;
      padding: 2.5rem 1.5rem; margin-top: 2rem;
    }
    .stat-n {
      font-size: clamp(1.8rem,4vw,2.6rem); font-weight: 900; letter-spacing:-0.04em;
      background: linear-gradient(90deg,var(--gold),#fbbf24);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    }
    .stat-l { font-size:0.8rem; color:var(--muted); letter-spacing:0.05em; margin-top:0.2rem; }
    .stat   { text-align:center; }

    /* ── Section util ── */
    .sec-label { font-size:0.73rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:var(--acc);margin-bottom:0.6rem; }
    .sec-title { font-size:clamp(1.8rem,4vw,2.8rem);font-weight:900;letter-spacing:-0.03em;line-height:1.1; }
    .sec-desc  { color:var(--muted);max-width:520px;margin-top:0.75rem;font-size:1rem; }

    /* ── About ── */
    .about { padding: 7rem 0; }
    .about-grid { display:grid;grid-template-columns:1fr 1fr;gap:4.5rem;align-items:center;margin-top:3rem; }
    .about-copy p { color:var(--muted);margin-bottom:1rem; }
    .badges { display:flex;flex-wrap:wrap;gap:0.65rem;margin-top:1.5rem; }
    .badge {
      font-size:0.78rem; font-weight:600;
      padding:0.3rem 0.85rem; border-radius:999px;
      background:var(--surf2); border:1px solid var(--border); color:var(--text);
    }
    .info-card {
      background:var(--surf); border:1px solid var(--border); border-radius:1.4rem; padding:2rem;
      display:flex; flex-direction:column; gap:1.1rem;
      box-shadow: 0 0 50px rgba(124,58,237,0.06);
    }
    .info-row { display:flex; align-items:flex-start; gap:1rem; }
    .info-icon { font-size:1.6rem; width:2.4rem; flex-shrink:0; margin-top:0.1rem; }
    .info-title { font-size:0.95rem; font-weight:700; color:var(--text); }
    .info-desc  { font-size:0.83rem; color:var(--muted); }

    /* ── Courses ── */
    .courses { padding: 7rem 0; }
    .courses-hd { text-align:center; margin-bottom:3rem; }
    .courses-hd .sec-desc { margin:0.75rem auto 0; }
    .course-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:1.5rem; }
    .course-card {
      background:var(--card); border:1px solid var(--border); border-radius:1.3rem;
      padding:1.8rem 1.5rem; position:relative; overflow:hidden;
      transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
      cursor: default;
    }
    .course-card::after {
      content:''; position:absolute; inset:0;
      background: radial-gradient(circle at 80% 20%, rgba(124,58,237,0.12), transparent 65%);
      opacity:0; transition:opacity 0.3s;
    }
    .course-card:hover { border-color:var(--acc); transform:translateY(-5px); box-shadow:0 12px 40px rgba(124,58,237,0.15); }
    .course-card:hover::after { opacity:1; }
    .c-icon  { font-size:2.3rem; margin-bottom:1rem; }
    .c-title { font-size:1.12rem; font-weight:800; letter-spacing:-0.02em; margin-bottom:0.4rem; }
    .c-desc  { font-size:0.83rem; color:var(--muted); line-height:1.55; }
    .c-tag   {
      display:inline-block; margin-top:1rem;
      font-size:0.73rem; font-weight:700; padding:0.22rem 0.7rem;
      border-radius:999px;
      background:rgba(124,58,237,0.14); color:#c4b5fd; border:1px solid rgba(124,58,237,0.28);
    }

    /* ── How ── */
    .how { padding:7rem 0; background:var(--surf); border-top:1px solid var(--border); border-bottom:1px solid var(--border); }
    .how-inner { text-align:center; max-width:850px; margin:0 auto; padding:0 1.5rem; }
    .steps { display:grid; grid-template-columns:repeat(3,1fr); gap:2rem; margin-top:3.5rem; position:relative; }
    .steps::before {
      content:''; position:absolute;
      top:2.4rem; left:calc(16.66% + 1.5rem); right:calc(16.66% + 1.5rem);
      height:2px; background:linear-gradient(90deg,var(--acc),var(--acc2)); opacity:0.25;
    }
    .step { display:flex; flex-direction:column; align-items:center; gap:1rem; padding:1rem; }
    .step-n {
      width:3rem;height:3rem;border-radius:50%;
      background:linear-gradient(135deg,var(--acc),#9333ea);
      display:flex;align-items:center;justify-content:center;
      font-weight:900;font-size:1.1rem;color:#fff;
      box-shadow:0 4px 18px rgba(124,58,237,0.45);
      position:relative;z-index:1;
    }
    .step-title { font-size:1.05rem; font-weight:700; }
    .step-desc  { font-size:0.83rem; color:var(--muted); }

    /* ── CTA ── */
    .cta-sec { padding:8rem 1.5rem; text-align:center; max-width:680px; margin:0 auto; }
    .cta-sec h2 {
      font-size:clamp(2rem,5.5vw,3.8rem);
      font-weight:900; letter-spacing:-0.04em; line-height:1.08;
      background:linear-gradient(135deg,#fff,var(--acc));
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    }
    .cta-sec p { color:var(--muted); margin:1rem auto 2.5rem; max-width:460px; }
    .cta-btns  { display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; }

    /* ── Footer ── */
    footer { background:var(--surf); border-top:1px solid var(--border); padding:3.5rem 1.5rem; }
    .foot-grid { max-width:1100px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr;gap:3rem; }
    .foot-brand { font-size:1.05rem;font-weight:900;background:linear-gradient(90deg,#fff,var(--acc));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:0.7rem; }
    .foot-desc  { font-size:0.83rem;color:var(--muted);max-width:270px;line-height:1.65; }
    footer h4   { font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--muted);margin-bottom:0.9rem; }
    footer ul   { list-style:none;display:flex;flex-direction:column;gap:0.55rem; }
    footer ul a { font-size:0.88rem;color:var(--muted);text-decoration:none;transition:color 0.2s; }
    footer ul a:hover { color:var(--text); }
    .foot-bottom {
      max-width:1100px;margin:2rem auto 0;padding-top:1.5rem;
      border-top:1px solid var(--border);
      display:flex;justify-content:space-between;align-items:center;
      font-size:0.78rem;color:var(--muted);flex-wrap:wrap;gap:0.5rem;
    }

    /* ── Reveal animation ── */
    .reveal { opacity:0; transform:translateY(28px); transition:opacity 0.65s ease,transform 0.65s ease; }
    .reveal.vis { opacity:1; transform:none; }

    /* ── Responsive ── */
    @media(max-width:768px){
      .nav-links { display:none; }
      .about-grid { grid-template-columns:1fr; gap:2.5rem; }
      .steps { grid-template-columns:1fr; }
      .steps::before { display:none; }
      .foot-grid { grid-template-columns:1fr; gap:2rem; }
      .foot-bottom { flex-direction:column; text-align:center; }
    }
  </style>
</head>
<body>

<!-- Background blobs -->
<div class="blobs"><div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div></div>

<!-- Nav -->
<nav>
  <a href="/" class="nav-brand">Apex Coaching</a>
  <ul class="nav-links">
    <li><a href="#about">About</a></li>
    <li><a href="#courses">Courses</a></li>
    <li><a href="#how">How it works</a></li>
    <li><a href="/test" class="nav-cta">🎙️ Try Sage</a></li>
  </ul>
</nav>

<!-- ── HERO ── -->
<section class="hero">
  <div class="hero-badge"><span class="live-dot"></span> AI Counsellor — Available 24 / 7</div>
  <h1>Meet Sage</h1>
  <div class="hero-sub-head">Your AI Counsellor</div>
  <p class="hero-desc">
    Ask anything about <span class="hl">JEE</span>, <span class="hl">NEET</span>,
    fees, batches &amp; admissions — Sage answers instantly.<span class="cursor"></span>
  </p>
  <div class="hero-btns">
    <a href="/test" class="btn-main">🎙️ Try Sage Online</a>
    <a href="tel:+911234567890" class="btn-ghost">📞 Call Us Now</a>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat-n">18+</div><div class="stat-l">Years of Excellence</div></div>
    <div class="stat"><div class="stat-n">10K+</div><div class="stat-l">Students Enrolled</div></div>
    <div class="stat"><div class="stat-n">IIT &amp; AIIMS</div><div class="stat-l">Expert Faculty</div></div>
    <div class="stat"><div class="stat-n">24 / 7</div><div class="stat-l">Sage Available</div></div>
  </div>
</section>

<!-- ── ABOUT ── -->
<section class="about reveal" id="about">
  <div class="inner">
    <div class="sec-label">Who We Are</div>
    <div class="sec-title">Apex Coaching Institute</div>
    <p class="sec-desc">Shaping toppers since 2006 — IIT &amp; AIIMS faculty, personalised mentorship, and India's first AI voice counsellor.</p>
    <div class="about-grid">
      <div class="about-copy">
        <p>Founded in 2006, Apex Coaching Institute has guided over 10,000 students to IITs, NITs, AIIMS and top universities across India.</p>
        <p>Our faculty are IITians and doctors who've been through the same grind — they don't just teach the syllabus, they teach you how to think under pressure.</p>
        <p>With Sage, our AI voice counsellor, you get instant answers about programmes, batches, fees, and the admission process — any time, any day.</p>
        <div class="badges">
          <span class="badge">🏆 18+ Years</span>
          <span class="badge">🎓 IIT &amp; AIIMS Faculty</span>
          <span class="badge">📍 Pune &amp; Mumbai</span>
          <span class="badge">🌐 Online Pan-India</span>
          <span class="badge">⭐ 4.9 / 5 Rating</span>
        </div>
      </div>
      <div class="info-card">
        <div class="info-row"><span class="info-icon">🏫</span><div><div class="info-title">Established 2006</div><div class="info-desc">18+ years shaping engineers and doctors</div></div></div>
        <div class="info-row"><span class="info-icon">👨‍🏫</span><div><div class="info-title">IIT &amp; AIIMS Faculty</div><div class="info-desc">Average 12 years teaching experience</div></div></div>
        <div class="info-row"><span class="info-icon">📊</span><div><div class="info-title">Proven Track Record</div><div class="info-desc">Top 500 IIT JEE selections every year</div></div></div>
        <div class="info-row"><span class="info-icon">🤖</span><div><div class="info-title">AI Counsellor — Sage</div><div class="info-desc">Voice AI available 24 / 7 on web &amp; phone</div></div></div>
        <div class="info-row"><span class="info-icon">💬</span><div><div class="info-title">Doubt Counter</div><div class="info-desc">6 days a week, live doubt resolution</div></div></div>
      </div>
    </div>
  </div>
</section>

<!-- ── COURSES ── -->
<section class="courses reveal" id="courses">
  <div class="inner">
    <div class="courses-hd">
      <div class="sec-label">What We Offer</div>
      <div class="sec-title">Courses &amp; Programmes</div>
      <p class="sec-desc">From Class 8 foundation to dropper batches — the right programme for every stage of your journey.</p>
    </div>
    <div class="course-grid">
      <div class="course-card">
        <div class="c-icon">⚗️</div>
        <div class="c-title">JEE Preparation</div>
        <div class="c-desc">Comprehensive JEE Main &amp; Advanced prep from Class 11. Small batches, IIT faculty, weekly mock tests.</div>
        <span class="c-tag">Class 11 &amp; 12</span>
      </div>
      <div class="course-card">
        <div class="c-icon">🩺</div>
        <div class="c-title">NEET Preparation</div>
        <div class="c-desc">Biology, Chemistry &amp; Physics by AIIMS doctors. NCERT deep-dives, daily tests, PYQ analysis.</div>
        <span class="c-tag">Class 11 &amp; 12</span>
      </div>
      <div class="course-card">
        <div class="c-icon">📚</div>
        <div class="c-title">School Tuition</div>
        <div class="c-desc">CBSE &amp; ICSE tuition for Classes 8–10. Build rock-solid fundamentals that carry you into competitive exams.</div>
        <span class="c-tag">Class 8 – 10</span>
      </div>
      <div class="course-card">
        <div class="c-icon">🔄</div>
        <div class="c-title">Dropper Batch</div>
        <div class="c-desc">One more year, one final push. Intensive 12-month JEE / NEET dropper programme with daily mentoring.</div>
        <span class="c-tag">Repeaters</span>
      </div>
    </div>
  </div>
</section>

<!-- ── HOW IT WORKS ── -->
<section class="how reveal" id="how">
  <div class="how-inner">
    <div class="sec-label">The Process</div>
    <div class="sec-title">How Sage Works</div>
    <p class="sec-desc" style="margin:0.8rem auto 0;">Three steps from curious to enrolled.</p>
    <div class="steps">
      <div class="step">
        <div class="step-n">1</div>
        <div class="step-title">Call or Click</div>
        <div class="step-desc">Dial our number or open Sage in your browser — no app, no form, instant access.</div>
      </div>
      <div class="step">
        <div class="step-n">2</div>
        <div class="step-title">Talk to Sage</div>
        <div class="step-desc">Ask anything — fees, faculty, batches, syllabus, scholarships. Sage knows it all.</div>
      </div>
      <div class="step">
        <div class="step-n">3</div>
        <div class="step-title">Get Enrolled</div>
        <div class="step-desc">Sage books your demo class and our team follows up within the hour.</div>
      </div>
    </div>
  </div>
</section>

<!-- ── CTA ── -->
<section class="reveal">
  <div class="cta-sec">
    <h2>Ready to talk to Sage?</h2>
    <p>Get instant answers about JEE, NEET, fees, and admissions — free, right now, no waiting.</p>
    <div class="cta-btns">
      <a href="/test" class="btn-main">🎙️ Try Sage Online</a>
      <a href="tel:+911234567890" class="btn-ghost">📞 +91 12345 67890</a>
    </div>
  </div>
</section>

<!-- ── FOOTER ── -->
<footer>
  <div class="foot-grid">
    <div>
      <div class="foot-brand">Apex Coaching Institute</div>
      <p class="foot-desc">Shaping India's next generation of engineers and doctors since 2006. IIT &amp; AIIMS faculty. 10,000+ alumni strong.</p>
    </div>
    <div>
      <h4>Courses</h4>
      <ul>
        <li><a href="#courses">JEE Preparation</a></li>
        <li><a href="#courses">NEET Preparation</a></li>
        <li><a href="#courses">School Tuition (8–10)</a></li>
        <li><a href="#courses">Dropper Batch</a></li>
      </ul>
    </div>
    <div>
      <h4>Contact</h4>
      <ul>
        <li><a href="tel:+911234567890">+91 12345 67890</a></li>
        <li><a href="mailto:admissions@apexcoaching.in">admissions@apexcoaching.in</a></li>
        <li><a href="/test">Talk to Sage (AI)</a></li>
        <li><a href="/docs">API Docs</a></li>
      </ul>
    </div>
  </div>
  <div class="foot-bottom">
    <div>&copy; 2025 Apex Coaching Institute. All rights reserved.</div>
    <div>Powered by <strong>UltraCounsel</strong> &nbsp;&middot;&nbsp; Voice AI by Ultravox</div>
  </div>
</footer>

<script>
  // Scroll reveal
  const io = new IntersectionObserver(
    entries => entries.forEach(e => { if(e.isIntersecting) e.target.classList.add("vis"); }),
    { threshold: 0.1 }
  );
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));
</script>
</body>
</html>"""
