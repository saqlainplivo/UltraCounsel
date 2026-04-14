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
from api.export import router as export_router

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
app.include_router(export_router)


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
      --acc-soft2: rgba(252, 95, 43, 0.18);
      --acc-border:rgba(252, 95, 43, 0.4);
      --text:      #FAFAFA;
      --sub:       #A1A1AA;
      --muted:     #71717A;
      --light:     #52525B;
    }
    html { scroll-behavior: smooth; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: "Inter", "Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 16px;
      line-height: 1.6;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* ── Layout ── */
    .wrap  { max-width: 1160px; margin: 0 auto; padding: 0 2rem; }
    .wrap-sm { max-width: 800px; margin: 0 auto; padding: 0 2rem; }

    /* ── NAV ── */
    nav {
      position: sticky; top: 0; z-index: 100;
      background: rgba(10,10,10,0.94);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      padding: 0 2rem;
      height: 64px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .nav-brand {
      font-size: 1rem; font-weight: 800; letter-spacing: -0.03em;
      color: var(--text); text-decoration: none;
      display: flex; align-items: center; gap: 0.5rem;
    }
    .nav-brand span { color: var(--acc); }
    .nav-links { list-style: none; display: flex; align-items: center; gap: 0.25rem; }
    .nav-links a {
      color: var(--sub); text-decoration: none; font-size: 0.875rem; font-weight: 500;
      padding: 0.45rem 0.85rem; border-radius: 0.5rem;
      transition: color 0.15s, background 0.15s;
    }
    .nav-links a:hover { color: var(--text); background: var(--bg3); }
    .nav-cta {
      background: var(--acc) !important;
      color: #fff !important;
      font-weight: 700 !important;
      border-radius: 0.65rem !important;
      padding: 0.5rem 1.1rem !important;
      transition: background 0.15s, transform 0.12s !important;
      box-shadow: 0 2px 12px rgba(252,95,43,0.35) !important;
    }
    .nav-cta:hover { background: var(--acc-hover) !important; transform: translateY(-1px) !important; }

    /* ── BUTTONS ── */
    .btn {
      display: inline-flex; align-items: center; gap: 0.5rem;
      font-size: 1rem; font-weight: 700; text-decoration: none;
      border-radius: 0.75rem; padding: 0.85rem 2rem;
      cursor: pointer; border: none;
      transition: background 0.15s, transform 0.12s, box-shadow 0.15s;
    }
    .btn-orange {
      background: var(--acc);
      color: #fff;
      box-shadow: 0 4px 24px rgba(252,95,43,0.4);
    }
    .btn-orange:hover { background: var(--acc-hover); transform: translateY(-2px); box-shadow: 0 8px 30px rgba(252,95,43,0.5); }
    .btn-outline {
      background: var(--bg);
      color: var(--text);
      border: 1.5px solid var(--border2);
      box-shadow: 0 1px 4px rgba(0,0,0,0.4);
    }
    .btn-outline:hover { border-color: var(--acc); color: var(--acc); background: var(--acc-soft); transform: translateY(-1px); }

    /* ── HERO ── */
    .hero {
      min-height: calc(100vh - 64px);
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      text-align: center; padding: 5rem 2rem 4rem;
      background: var(--bg);
      position: relative; overflow: hidden;
    }
    .hero::before {
      content: '';
      position: absolute; inset: 0;
      background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(252,95,43,0.12) 0%, transparent 70%);
      pointer-events: none;
    }
    .hero-eyebrow {
      display: inline-flex; align-items: center; gap: 0.5rem;
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
      color: var(--acc);
      border: 1px solid var(--acc-border);
      background: var(--acc-soft);
      border-radius: 999px; padding: 0.35rem 1rem;
      margin-bottom: 1.75rem;
    }
    .live-dot {
      width: 6px; height: 6px; border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 0 3px rgba(34,197,94,0.2);
      display: inline-block;
      animation: pulse-dot 2s ease-in-out infinite;
    }
    @keyframes pulse-dot { 0%,100%{box-shadow:0 0 0 3px rgba(34,197,94,0.2)} 50%{box-shadow:0 0 0 6px rgba(34,197,94,0.1)} }

    .hero h1 {
      font-size: clamp(3rem, 10vw, 6.5rem);
      font-weight: 900;
      letter-spacing: -0.05em;
      line-height: 1;
      color: var(--text);
      margin-bottom: 0.15em;
    }
    .hero h1 .acc { color: var(--acc); }
    .hero-tagline {
      font-size: clamp(1.1rem, 3vw, 1.65rem);
      font-weight: 500;
      color: var(--sub);
      letter-spacing: -0.01em;
      margin-bottom: 1.4rem;
    }
    .hero-sub {
      font-size: clamp(0.9rem, 1.8vw, 1.1rem);
      color: var(--muted);
      max-width: 500px;
      margin: 0 auto 2.5rem;
      line-height: 1.65;
    }
    .hero-btns { display: flex; gap: 0.9rem; flex-wrap: wrap; justify-content: center; }

    /* ── STATS STRIP ── */
    .stats-strip {
      width: 100%;
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      background: var(--bg2);
      margin-top: 4rem;
    }
    .stats-inner {
      max-width: 900px; margin: 0 auto;
      display: flex; justify-content: space-around; flex-wrap: wrap;
      padding: 1.6rem 2rem; gap: 1.5rem;
    }
    .stat { text-align: center; }
    .stat-n {
      font-size: clamp(1.6rem, 4vw, 2.2rem);
      font-weight: 900; letter-spacing: -0.04em;
      color: var(--acc); line-height: 1;
    }
    .stat-l {
      font-size: 0.78rem; font-weight: 600;
      color: var(--sub); letter-spacing: 0.02em;
      margin-top: 0.3rem; text-transform: uppercase;
    }
    .stat-divider {
      width: 1px; background: var(--border);
      align-self: stretch; margin: 0.25rem 0;
    }

    /* ── TICKER ── */
    .ticker-wrap {
      overflow: hidden;
      background: var(--acc);
      padding: 0.7rem 0;
      white-space: nowrap;
    }
    .ticker {
      display: inline-block;
      animation: ticker 30s linear infinite;
    }
    .ticker span {
      font-size: 0.82rem; font-weight: 700; letter-spacing: 0.06em;
      text-transform: uppercase; color: #fff; margin: 0 2.5rem;
    }
    .ticker span::before { content: '·'; margin-right: 2.5rem; opacity: 0.5; }
    .ticker span:first-child::before { display: none; }
    @keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }

    /* ── SECTION LABELS ── */
    .sec-eyebrow {
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
      color: var(--acc); margin-bottom: 0.6rem;
    }
    .sec-title {
      font-size: clamp(1.75rem, 4vw, 2.75rem);
      font-weight: 900; letter-spacing: -0.03em; line-height: 1.1;
      color: var(--text);
    }
    .sec-sub {
      font-size: 1rem; color: var(--muted);
      margin-top: 0.7rem; max-width: 500px; line-height: 1.65;
    }

    /* ── ABOUT SECTION ── */
    .about {
      padding: 7rem 0;
      background: var(--bg2);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
    }
    .about-grid {
      display: grid; grid-template-columns: 1fr 1fr;
      gap: 5rem; align-items: center; margin-top: 3rem;
    }
    .about-copy p { color: var(--sub); margin-bottom: 1.1rem; font-size: 1rem; line-height: 1.7; }
    .badges { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1.6rem; }
    .badge {
      font-size: 0.78rem; font-weight: 600; color: var(--sub);
      padding: 0.3rem 0.85rem; border-radius: 999px;
      background: var(--bg); border: 1px solid var(--border2);
      transition: border-color 0.15s, color 0.15s;
    }
    .badge:hover { border-color: var(--acc-border); color: var(--acc); }
    .info-card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 1.25rem;
      padding: 2rem 2rem;
      display: flex; flex-direction: column; gap: 1.1rem;
      box-shadow: 0 2px 20px rgba(0,0,0,0.45);
    }
    .info-row { display: flex; align-items: flex-start; gap: 1rem; }
    .info-icon {
      width: 2.5rem; height: 2.5rem; border-radius: 0.65rem; flex-shrink: 0;
      background: var(--acc-soft); border: 1px solid var(--acc-border);
      display: flex; align-items: center; justify-content: center;
      font-size: 1.1rem;
    }
    .info-title { font-size: 0.9rem; font-weight: 700; color: var(--text); }
    .info-desc  { font-size: 0.82rem; color: var(--muted); margin-top: 0.15rem; }

    /* ── COURSES ── */
    .courses { padding: 7rem 0; background: var(--bg); }
    .courses-hd { text-align: center; margin-bottom: 3rem; }
    .courses-hd .sec-sub { margin: 0.7rem auto 0; }
    .course-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.25rem;
    }
    .course-card {
      background: var(--bg);
      border: 1.5px solid var(--border);
      border-radius: 1.1rem;
      padding: 1.75rem 1.5rem;
      transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
      cursor: default;
    }
    .course-card:hover {
      border-color: var(--acc-border);
      box-shadow: 0 6px 30px rgba(252,95,43,0.22);
      transform: translateY(-3px);
    }
    .c-icon-wrap {
      width: 3rem; height: 3rem; border-radius: 0.8rem;
      background: var(--acc-soft); border: 1px solid var(--acc-border);
      display: flex; align-items: center; justify-content: center;
      font-size: 1.4rem; margin-bottom: 1.1rem;
    }
    .c-title { font-size: 1.05rem; font-weight: 800; letter-spacing: -0.02em; color: var(--text); margin-bottom: 0.4rem; }
    .c-desc  { font-size: 0.84rem; color: var(--muted); line-height: 1.6; }
    .c-tag {
      display: inline-block; margin-top: 1.1rem;
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
      padding: 0.25rem 0.75rem; border-radius: 999px;
      background: var(--acc-soft); color: var(--acc); border: 1px solid var(--acc-border);
    }

    /* ── HOW IT WORKS ── */
    .how {
      padding: 7rem 0;
      background: var(--bg2);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
    }
    .how-inner { text-align: center; }
    .steps {
      display: grid; grid-template-columns: repeat(3, 1fr);
      gap: 2rem; margin-top: 3.5rem; position: relative;
    }
    .steps::before {
      content: '';
      position: absolute;
      top: 1.5rem;
      left: calc(50% / 3 + 1rem);
      right: calc(50% / 3 + 1rem);
      height: 1px;
      background: linear-gradient(90deg, var(--acc-border), var(--acc-border));
      z-index: 0;
    }
    .step { display: flex; flex-direction: column; align-items: center; gap: 1rem; }
    .step-num {
      width: 3rem; height: 3rem; border-radius: 50%;
      background: var(--acc);
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; font-size: 1rem; color: #fff;
      position: relative; z-index: 1;
      box-shadow: 0 4px 16px rgba(252,95,43,0.5);
    }
    .step-title { font-size: 1rem; font-weight: 800; color: var(--text); }
    .step-desc  { font-size: 0.85rem; color: var(--muted); max-width: 200px; }

    /* ── PROOF STRIP ── */
    .proof-strip {
      background: var(--bg);
      border-top: 1px solid var(--border);
      padding: 4.5rem 0;
    }
    .proof-grid {
      display: grid; grid-template-columns: repeat(3, 1fr);
      gap: 0; text-align: center;
    }
    .proof-item {
      padding: 2rem;
      border-right: 1px solid var(--border);
    }
    .proof-item:last-child { border-right: none; }
    .proof-n {
      font-size: clamp(2rem, 5vw, 3rem); font-weight: 900; letter-spacing: -0.04em;
      color: var(--acc); line-height: 1; margin-bottom: 0.4rem;
    }
    .proof-label { font-size: 0.9rem; font-weight: 600; color: var(--text); }
    .proof-note  { font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }

    /* ── CTA SECTION ── */
    .cta-sec {
      padding: 7rem 2rem;
      text-align: center;
      background: var(--bg2);
      border-top: 1px solid var(--border);
    }
    .cta-inner { max-width: 620px; margin: 0 auto; }
    .cta-sec h2 {
      font-size: clamp(1.9rem, 5vw, 3.2rem);
      font-weight: 900; letter-spacing: -0.04em; line-height: 1.1;
      color: var(--text); margin-bottom: 1rem;
    }
    .cta-sec h2 .acc { color: var(--acc); }
    .cta-sec p { color: var(--muted); margin-bottom: 2.2rem; font-size: 1rem; }
    .cta-btns { display: flex; gap: 0.9rem; justify-content: center; flex-wrap: wrap; }

    /* ── FOOTER ── */
    footer {
      background: var(--bg);
      border-top: 1px solid var(--border);
      padding: 3.5rem 2rem 2rem;
    }
    .foot-grid {
      max-width: 1160px; margin: 0 auto;
      display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 3rem;
    }
    .foot-brand {
      font-size: 1rem; font-weight: 900; letter-spacing: -0.03em;
      color: var(--text); margin-bottom: 0.7rem;
    }
    .foot-brand span { color: var(--acc); }
    .foot-desc { font-size: 0.84rem; color: var(--muted); max-width: 260px; line-height: 1.7; }
    footer h4 {
      font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em;
      color: var(--muted); margin-bottom: 1rem; font-weight: 700;
    }
    footer ul { list-style: none; display: flex; flex-direction: column; gap: 0.6rem; }
    footer ul a { font-size: 0.875rem; color: var(--sub); text-decoration: none; transition: color 0.15s; }
    footer ul a:hover { color: var(--acc); }
    .foot-bottom {
      max-width: 1160px; margin: 2.5rem auto 0;
      padding-top: 1.5rem; border-top: 1px solid var(--border);
      display: flex; justify-content: space-between; align-items: center;
      font-size: 0.78rem; color: var(--muted); flex-wrap: wrap; gap: 0.5rem;
    }

    /* ── REVEAL ── */
    .reveal { opacity: 0; transform: translateY(1.5rem); transition: opacity 0.7s cubic-bezier(0.25,0.1,0.25,1), transform 0.7s cubic-bezier(0.25,0.1,0.25,1); }
    .reveal.vis { opacity: 1; transform: none; }

    /* ── RESPONSIVE ── */
    @media (max-width: 768px) {
      .nav-links { display: none; }
      .about-grid, .foot-grid { grid-template-columns: 1fr; gap: 2.5rem; }
      .steps { grid-template-columns: 1fr; }
      .steps::before { display: none; }
      .proof-grid { grid-template-columns: 1fr; }
      .proof-item { border-right: none; border-bottom: 1px solid var(--border); }
      .proof-item:last-child { border-bottom: none; }
      .foot-bottom { flex-direction: column; text-align: center; }
      .stat-divider { display: none; }
    }
  </style>
</head>
<body>

<!-- ── NAV ── -->
<nav>
  <a href="/" class="nav-brand">Apex <span>Coaching</span></a>
  <ul class="nav-links">
    <li><a href="#about">About</a></li>
    <li><a href="#courses">Courses</a></li>
    <li><a href="#how">How It Works</a></li>
    <li><a href="/test" class="nav-cta">🎙️ Try Sage</a></li>
  </ul>
</nav>

<!-- ── HERO ── -->
<section class="hero">
  <div class="hero-eyebrow"><span class="live-dot"></span> India's First AI Voice Counsellor</div>
  <h1>Meet <span class="acc">Sage.</span></h1>
  <p class="hero-tagline">Your smartest admission conversation.</p>
  <p class="hero-sub">Ask anything about JEE, NEET, fees, batches, and scholarships. Sage answers instantly — on your phone or in your browser, 24 / 7.</p>
  <div class="hero-btns">
    <a href="/test" class="btn btn-orange">🎙️ Try Sage Now</a>
    <a href="tel:+911234567890" class="btn btn-outline">📞 Call Us</a>
  </div>

  <div class="stats-strip">
    <div class="stats-inner">
      <div class="stat"><div class="stat-n">22</div><div class="stat-l">Branches Across India</div></div>
      <div class="stat-divider"></div>
      <div class="stat"><div class="stat-n">15,000+</div><div class="stat-l">Students Enrolled</div></div>
      <div class="stat-divider"></div>
      <div class="stat"><div class="stat-n">18+</div><div class="stat-l">Years of Excellence</div></div>
      <div class="stat-divider"></div>
      <div class="stat"><div class="stat-n">IIT &amp; AIIMS</div><div class="stat-l">Expert Faculty</div></div>
      <div class="stat-divider"></div>
      <div class="stat"><div class="stat-n">24 / 7</div><div class="stat-l">Sage Available</div></div>
    </div>
  </div>
</section>

<!-- ── TICKER ── -->
<div class="ticker-wrap" aria-hidden="true">
  <div class="ticker">
    <span>72% NEET Qualification Rate</span>
    <span>AIR 201 — JEE Advanced Topper</span>
    <span>22 Cities Across India</span>
    <span>IIT &amp; AIIMS Faculty</span>
    <span>99.7 Percentile — JEE Mains</span>
    <span>Free Demo Class Available</span>
    <span>72% NEET Qualification Rate</span>
    <span>AIR 201 — JEE Advanced Topper</span>
    <span>22 Cities Across India</span>
    <span>IIT &amp; AIIMS Faculty</span>
    <span>99.7 Percentile — JEE Mains</span>
    <span>Free Demo Class Available</span>
  </div>
</div>

<!-- ── ABOUT ── -->
<section class="about reveal" id="about">
  <div class="wrap">
    <div class="sec-eyebrow">Who We Are</div>
    <div class="sec-title">Apex Coaching Institute</div>
    <p class="sec-sub">Shaping toppers since 2005 — IIT &amp; AIIMS faculty, personalised mentorship, and the world's first AI voice counsellor for coaching admissions.</p>
    <div class="about-grid">
      <div class="about-copy">
        <p>Founded in 2005 and headquartered in Pune, Apex Coaching Institute has guided over 15,000 students into IITs, NITs, AIIMS, and top universities across India.</p>
        <p>Our faculty are IITians and AIIMS doctors who've lived the same grind. They don't just teach the syllabus — they teach you how to think under pressure.</p>
        <p>With <strong>Sage</strong>, our AI voice counsellor, you get instant answers about programmes, batches, fees, and admissions any time of day — no hold music, no callbacks needed.</p>
        <div class="badges">
          <span class="badge">🏆 18+ Years</span>
          <span class="badge">🎓 IIT &amp; AIIMS Faculty</span>
          <span class="badge">📍 22 Branches</span>
          <span class="badge">🌐 Pan-India Online</span>
          <span class="badge">⭐ 4.9 / 5 Rating</span>
          <span class="badge">🤖 AI-Powered 24/7</span>
        </div>
      </div>
      <div class="info-card">
        <div class="info-row">
          <div class="info-icon">🏫</div>
          <div><div class="info-title">Established 2005</div><div class="info-desc">18+ years shaping engineers and doctors</div></div>
        </div>
        <div class="info-row">
          <div class="info-icon">👨‍🏫</div>
          <div><div class="info-title">IIT &amp; AIIMS Faculty</div><div class="info-desc">Average 12 years of teaching experience</div></div>
        </div>
        <div class="info-row">
          <div class="info-icon">📍</div>
          <div><div class="info-title">22 Branches in 18 Cities</div><div class="info-desc">Delhi, Bangalore, Hyderabad, Chennai, Kota &amp; more</div></div>
        </div>
        <div class="info-row">
          <div class="info-icon">🤖</div>
          <div><div class="info-title">Sage — AI Voice Counsellor</div><div class="info-desc">Available 24/7 on web and phone. No waiting.</div></div>
        </div>
        <div class="info-row">
          <div class="info-icon">💬</div>
          <div><div class="info-title">Doubt Counter</div><div class="info-desc">Live doubt resolution, 6 days a week</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ── COURSES ── -->
<section class="courses reveal" id="courses">
  <div class="wrap">
    <div class="courses-hd">
      <div class="sec-eyebrow">What We Offer</div>
      <div class="sec-title">Courses &amp; Programmes</div>
      <p class="sec-sub">From Class 8 foundation to dropper batches — the right programme for every stage of your journey.</p>
    </div>
    <div class="course-grid">
      <div class="course-card">
        <div class="c-icon-wrap">⚗️</div>
        <div class="c-title">JEE Preparation</div>
        <div class="c-desc">Comprehensive JEE Main &amp; Advanced prep from Class 11. Small batches, IIT faculty, all-India mock tests.</div>
        <span class="c-tag">Class 11 &amp; 12</span>
      </div>
      <div class="course-card">
        <div class="c-icon-wrap">🩺</div>
        <div class="c-title">NEET Preparation</div>
        <div class="c-desc">Biology, Chemistry &amp; Physics by AIIMS doctors. NCERT deep-dives, daily tests, PYQ analysis.</div>
        <span class="c-tag">Class 11 &amp; 12</span>
      </div>
      <div class="course-card">
        <div class="c-icon-wrap">📚</div>
        <div class="c-title">School Tuition</div>
        <div class="c-desc">CBSE &amp; ICSE tuition for Classes 8–10. Rock-solid fundamentals that carry you into competitive exams.</div>
        <span class="c-tag">Class 8 – 10</span>
      </div>
      <div class="course-card">
        <div class="c-icon-wrap">🔄</div>
        <div class="c-title">Dropper Batch</div>
        <div class="c-desc">One more year, one final push. Intensive JEE / NEET dropper programme with daily mentoring.</div>
        <span class="c-tag">Repeaters</span>
      </div>
    </div>
  </div>
</section>

<!-- ── HOW IT WORKS ── -->
<section class="how reveal" id="how">
  <div class="wrap">
    <div class="how-inner">
      <div class="sec-eyebrow">The Process</div>
      <div class="sec-title">How Sage Works</div>
      <p class="sec-sub" style="margin:0.7rem auto 0; max-width:440px;">Three steps from curious to enrolled — no forms, no waiting rooms.</p>
      <div class="steps">
        <div class="step">
          <div class="step-num">1</div>
          <div class="step-title">Call or Click</div>
          <div class="step-desc">Dial our number or open Sage in your browser — no app needed, instant access.</div>
        </div>
        <div class="step">
          <div class="step-num">2</div>
          <div class="step-title">Talk to Sage</div>
          <div class="step-desc">Ask anything — fees, faculty, batches, syllabus, scholarships. Sage knows it all.</div>
        </div>
        <div class="step">
          <div class="step-num">3</div>
          <div class="step-title">Get Enrolled</div>
          <div class="step-desc">Sage books your demo class and our team follows up within the hour.</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ── PROOF STRIP ── -->
<section class="proof-strip reveal">
  <div class="wrap">
    <div class="proof-grid">
      <div class="proof-item">
        <div class="proof-n">72%</div>
        <div class="proof-label">NEET Students Qualify</div>
        <div class="proof-note">Based on 2023-24 batch data</div>
      </div>
      <div class="proof-item">
        <div class="proof-n">AIR 201</div>
        <div class="proof-label">JEE Advanced Topper</div>
        <div class="proof-note">Kavya, Apex Student 2024</div>
      </div>
      <div class="proof-item">
        <div class="proof-n">₹10K</div>
        <div class="proof-label">Dropper Special Discount</div>
        <div class="proof-note">Flat off on JEE &amp; NEET repeater batches</div>
      </div>
    </div>
  </div>
</section>

<!-- ── CTA ── -->
<section class="cta-sec reveal">
  <div class="cta-inner">
    <h2>Ready to talk to <span class="acc">Sage?</span></h2>
    <p>Get instant answers about JEE, NEET, fees, and admissions — free, right now, no waiting.</p>
    <div class="cta-btns">
      <a href="/test" class="btn btn-orange">🎙️ Try Sage Online</a>
      <a href="tel:+911234567890" class="btn btn-outline">📞 +91 12345 67890</a>
    </div>
  </div>
</section>

<!-- ── FOOTER ── -->
<footer>
  <div class="foot-grid">
    <div>
      <div class="foot-brand">Apex <span>Coaching</span> Institute</div>
      <p class="foot-desc">Shaping India's next generation of engineers and doctors since 2005. IIT &amp; AIIMS faculty. 15,000+ alumni strong.</p>
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
        <li><a href="/api/health">API Health</a></li>
      </ul>
    </div>
  </div>
  <div class="foot-bottom">
    <div>&copy; 2026 Apex Coaching Institute. All rights reserved.</div>
    <div>Powered by <strong>UltraCounsel</strong> &nbsp;&middot;&nbsp; Voice AI by Ultravox</div>
  </div>
</footer>

<script>
  // Scroll reveal
  const io = new IntersectionObserver(
    entries => entries.forEach(e => { if(e.isIntersecting) e.target.classList.add("vis"); }),
    { threshold: 0.08 }
  );
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));
</script>
</body>
</html>"""
