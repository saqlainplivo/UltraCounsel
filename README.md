# UltraCounsel 🎓

**Sage — AI Voice Counsellor for Apex Coaching Institute**

An intelligent voice agent that handles all inbound student counselling calls for a coaching institute offering Class 8-10 tuitions and IIT-JEE / NEET preparation. Built with **Ultravox**, **Plivo**, and **FastAPI**.

---

## What Sage Does

- Helps students find the right course (Class 8-10, JEE, NEET)
- Explains syllabus in depth — topic sequence, NCERT alignment, difficulty progression
- Checks batch availability with personalised timing recommendations
- Suggests nearest branch based on student's city
- Proactively surfaces scholarships when fee concerns arise
- Logs serious inquiries to a CRM for admissions follow-up
- Books free demo class slots on the spot
- Sends SMS learning plans at the student's request
- Recognises returning callers by hashed phone number

---

## Architecture

```
Inbound Call (Plivo)
    │
    ▼
POST /api/webhook/answer
    ├── Hash caller phone (SHA-256 + salt)
    ├── Load prior session context
    ├── Create Ultravox session (Sage's prompt + 8 tools)
    └── Return <Stream> XML to Plivo
                │
                ▼
        Ultravox WebSocket (Sage)
                │
        (tool invocations)
                │
    ┌───────────┴────────────────────┐
    │    POST /api/tools/*           │
    │  (search, details, batch,      │
    │   branch, scholarship, CRM,    │
    │   SMS, demo booking)           │
    └───────────┬────────────────────┘
                ▼
        PostgreSQL (16 tables)
        + Plivo SMS API
```

---

## Assignment Compliance

| Requirement | Implementation |
|-------------|---------------|
| Ultravox voice agent | `lib/ultravox.py` — Sage's 10-section prompt, session via REST API |
| Plivo telephony | `api/webhook/answer.py` — Plivo XML `<Stream>` bidirectional WebSocket |
| 5+ custom tools | **8 tools** registered as `temporaryTool` in Ultravox session |
| Tool call logging | `tool_calls` table — every invocation logged with input/output/latency |
| Call transcription | `transcripts` table — saved on `call_ended` event |
| Intent detection | `detected_intents` table — categorized per call |
| Call analytics | `GET /api/calls`, `GET /api/analytics`, `GET /api/inquiries` |
| Session restoration | SHA-256+salt phone hash, `caller_profiles` + `caller_sessions` |
| PostgreSQL database | asyncpg pool, 16 tables |
| Security | Prompt injection detection, phone hashing, no PII stored |
| Vercel deployment | `vercel.json`, Python runtime |
| `.env.example` | 16 documented variables |

---

## 8 Custom Tools

| Tool | Description |
|------|-------------|
| `search_courses` | Search course catalog by class, exam, board, keyword |
| `get_course_details` | Full details: syllabus, faculty, outcomes, study material |
| `check_batch_availability` | Batches with timing personalization + school-hour conflict detection |
| `find_nearest_branch` | Location-aware branch discovery (Pune HQ, Wakad, Mumbai, Online) |
| `check_scholarship` | Scholarship eligibility + installment plans |
| `log_student_inquiry` | CRM: log interest with lead stage, generates APX-YYYYMMDD-XXXXX ref |
| `send_learning_plan` | SMS with course summary, batch date, fee, scholarship info |
| `book_demo_class` | Book free 2-hour demo slot, send confirmation SMS |

---

## Database (16 Tables)

**Assignment-required (5):** `call_logs`, `transcripts`, `detected_intents`, `tool_calls`, `call_summaries`

**Course catalog (4):** `courses`, `batches`, `faculty`, `syllabus_topics`

**Enrichment (4):** `branches`, `scholarships`, `demo_slots`, `course_outcomes`

**CRM + Comms (3):** `student_inquiries`, `demo_bookings`, `communications_sent`

**Session (2):** `caller_profiles`, `caller_sessions`

---

## Course Catalog

| Course | Category | Fee |
|--------|----------|-----|
| Class 8 Foundation CBSE | School Tuition | Rs 45,000/yr |
| Class 8 Foundation ICSE | School Tuition | Rs 48,000/yr |
| Class 9 Foundation CBSE | School Tuition | Rs 48,000/yr |
| Class 9 Foundation ICSE | School Tuition | Rs 50,000/yr |
| Class 10 Board Excellence CBSE | School Tuition | Rs 55,000/yr |
| Class 10 Board Excellence ICSE | School Tuition | Rs 58,000/yr |
| JEE Mains Preparation (2-Year) | IIT-JEE | Rs 1,20,000 |
| JEE Advanced Intensive (1-Year) | IIT-JEE | Rs 95,000 |
| JEE Dropper Batch | IIT-JEE | Rs 85,000 |
| NEET 2-Year Foundation | NEET | Rs 1,10,000 |
| NEET 1-Year Intensive | NEET | Rs 80,000 |
| NEET Repeater Crash Course | NEET | Rs 65,000 |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
- `PLIVO_AUTH_ID`, `PLIVO_AUTH_TOKEN`, `PLIVO_PHONE_NUMBER`
- `ULTRAVOX_API_KEY`
- `DATABASE_URL`
- `SECRET_HASH_SALT`
- `APP_BASE_URL` (your ngrok or Vercel URL)

### 3. Set up database

```bash
python scripts/setup_db.py
```

This creates all 16 tables and seeds the complete course catalog.

### 4. Run locally

```bash
python -m uvicorn main:app --reload --port 8000
```

### 5. Expose with ngrok (for Plivo webhooks)

```bash
ngrok http 8000
# Copy the https URL to APP_BASE_URL in .env
```

### 6. Configure Plivo

1. Buy an Indian number (+91 xxx) at console.plivo.com
2. Set Answer URL: `https://your-ngrok.ngrok.io/api/webhook/answer`
3. Set Event URL: `https://your-ngrok.ngrok.io/api/webhook/events`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/webhook/answer` | Plivo inbound call webhook |
| POST | `/api/webhook/events` | Ultravox event webhook |
| POST | `/api/tools/search-courses` | Search course catalog |
| POST | `/api/tools/course-details` | Full course details |
| POST | `/api/tools/batch-availability` | Batch timings + availability |
| POST | `/api/tools/nearest-branch` | Branch by location |
| POST | `/api/tools/scholarship` | Scholarship eligibility |
| POST | `/api/tools/log-inquiry` | CRM inquiry logging |
| POST | `/api/tools/send-learning-plan` | SMS learning plan |
| POST | `/api/tools/book-demo` | Demo class booking |
| GET | `/api/calls` | List all calls (paginated) |
| GET | `/api/calls/{uuid}` | Full call detail |
| GET | `/api/analytics` | Aggregate metrics |
| GET | `/api/inquiries` | CRM inquiry list |
| GET | `/api/health` | Health check |

---

## Deployment (Vercel)

```bash
vercel --prod
```

Set all `.env` variables as Vercel environment variables in the project settings.

---

## Project Structure

```
UltraCounsel/
├── main.py                      # FastAPI app entry point
├── requirements.txt
├── vercel.json
├── .env.example
├── data/
│   └── courses.json             # Full course catalog (seeded at setup)
├── docs/
│   └── PROBLEM_STATEMENT.md
├── lib/
│   ├── db.py                    # asyncpg pool
│   ├── security.py              # Phone hashing + injection detection
│   ├── session_manager.py       # Caller session context
│   ├── plivo_client.py          # XML + SMS helpers
│   ├── ultravox.py              # Sage's system prompt + session creator
│   └── tools/                   # 8 tool implementations
├── api/
│   ├── tools.py                 # Tool HTTP endpoints
│   ├── calls.py                 # Analytics endpoints
│   └── webhook/
│       ├── answer.py            # Plivo inbound webhook
│       └── events.py            # Ultravox events webhook
└── scripts/
    └── setup_db.py              # DB setup + data seeding
```

---

## Security

- Phone numbers are **never stored in plain text**. Hashed with SHA-256 + secret salt.
- Prompt injection detection covers 12+ attack patterns.
- All tool endpoints validate call_id before processing.
- No student PII is logged in plaintext — masked number format only.

---

*Built with Ultravox + Plivo + FastAPI for the Ultravox Engineering Assignment.*
