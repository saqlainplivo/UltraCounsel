# UltraCounsel — Problem Statement

## Use Case

**Apex Coaching Institute** is a coaching institute in Pune, India offering tuition classes for school students (Class 8-10, CBSE and ICSE boards) and competitive exam preparation for IIT-JEE (Mains, Advanced, Dropper) and NEET (2-Year, 1-Year, Repeater batches).

Every day, the institute receives dozens of inbound phone calls from:
- Parents of Class 8-10 students looking for tuition support
- Class 11-12 students researching JEE and NEET preparation
- Droppers evaluating whether to rejoin coaching
- Callers asking about fees, batches, faculty, scholarships, and facilities

**The problem:** These calls are handled by a small admissions team. During peak admission season (April–June), the team is overwhelmed. Calls go unanswered or are handled inconsistently. Important leads are missed. Information given is sometimes incorrect or incomplete.

---

## Solution

**Sage** — an AI voice counsellor powered by Ultravox + Plivo — handles all inbound counselling calls autonomously.

Sage:
- Answers calls 24/7 with zero wait time
- Helps callers find the right course based on their class, goals, and timing
- Explains course syllabus in depth (including topic sequences, NCERT alignment, difficulty progression)
- Checks real-time batch availability and personalises recommendations based on timing preference
- Suggests the nearest Apex branch based on caller's city/area
- Proactively surfaces scholarship options when fee concerns arise
- Logs genuine student inquiries to a CRM for admissions team follow-up
- Books free demo class slots on the spot
- Sends personalised SMS learning plans at the student's request

---

## Features Built

| Feature | Description |
|---------|-------------|
| 8 custom tools | Course search, details, batch availability, branch finder, scholarship, CRM inquiry, learning plan SMS, demo booking |
| Deep syllabus intelligence | 60+ topic entries with sequence, difficulty, NCERT alignment |
| Batch personalization | Timing-fit scoring, school-hour conflict detection |
| Location-aware branches | 4 branches (Pune HQ, Wakad, Mumbai, Online) with facilities |
| 5 scholarship types | Merit, Sibling, Early Bird, Need-based, Dropper Special |
| Full CRM pipeline | Lead stages: new → contacted → demo_scheduled → enrolled |
| Demo class booking | Real slot inventory, confirmation SMS |
| Session restoration | Returning callers recognized by hashed phone, prior context injected |
| Security | Prompt injection detection, phone hashing, no raw PII stored |
| Analytics | Call logs, transcripts, intent detection, tool usage stats, lead funnel |

---

## Technical Architecture

```
Caller
  │
  ▼ (inbound call)
Plivo ──────────────────────────► /api/webhook/answer
                                        │
                                        ├─ hash phone number
                                        ├─ load session context
                                        ├─ create Ultravox session
                                        └─ return Stream XML
                                               │
                                               ▼
                              Ultravox (Sage) ◄──► WebSocket audio
                                        │
                              (tool calls) │
                                        ▼
                              /api/tools/* ──► PostgreSQL (courses DB)
                                                  + Plivo SMS API
                                                  + demo_slots table
```

---

## Course Catalog (Seeded Data)

12 courses × 7 batches × 8 faculty × 60+ syllabus topics × 4 branches × 5 scholarships × 12 demo slots

---

## Assignment Compliance

See README.md for full compliance table.
