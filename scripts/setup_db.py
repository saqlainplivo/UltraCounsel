"""
setup_db.py
Creates all 16 database tables and seeds course catalog from data/courses.json.

Usage: python scripts/setup_db.py
Requires: DATABASE_URL in .env
"""

import asyncio
import asyncpg
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

COURSES_FILE = Path("data/courses.json")


async def setup():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        return

    print("🔌 Connecting to database...")
    conn = await asyncpg.connect(dsn=database_url)
    print("✅ Connected!\n")

    # ── 1. Assignment-required tables ────────────────────────────────────────

    print("📋 Creating assignment-required tables...")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS call_logs (
            id          SERIAL PRIMARY KEY,
            call_uuid   TEXT UNIQUE NOT NULL,
            caller_hash TEXT NOT NULL,
            caller_masked TEXT,
            to_number   TEXT,
            direction   TEXT DEFAULT 'inbound',
            status      TEXT DEFAULT 'initiated',
            started_at  TIMESTAMPTZ DEFAULT NOW(),
            ended_at    TIMESTAMPTZ,
            duration_seconds INTEGER,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id          SERIAL PRIMARY KEY,
            call_id     TEXT NOT NULL REFERENCES call_logs(call_uuid) ON DELETE CASCADE,
            role        TEXT NOT NULL CHECK (role IN ('agent', 'user')),
            content     TEXT NOT NULL,
            timestamp   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS detected_intents (
            id          SERIAL PRIMARY KEY,
            call_id     TEXT NOT NULL REFERENCES call_logs(call_uuid) ON DELETE CASCADE,
            intent      TEXT NOT NULL,
            confidence  FLOAT,
            raw_text    TEXT,
            detected_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id          SERIAL PRIMARY KEY,
            call_id     TEXT NOT NULL,
            tool_name   TEXT NOT NULL,
            input_data  JSONB,
            output_data JSONB,
            success     BOOLEAN DEFAULT TRUE,
            error_msg   TEXT,
            duration_ms INTEGER,
            called_at   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS call_summaries (
            id               SERIAL PRIMARY KEY,
            call_id          TEXT NOT NULL REFERENCES call_logs(call_uuid) ON DELETE CASCADE,
            primary_intent   TEXT,
            courses_discussed TEXT[],
            inquiry_logged   BOOLEAN DEFAULT FALSE,
            demo_booked      BOOLEAN DEFAULT FALSE,
            sms_sent         BOOLEAN DEFAULT FALSE,
            resolution_status TEXT DEFAULT 'resolved',
            summary_text     TEXT,
            created_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── 2. Course catalog tables ──────────────────────────────────────────────

    print("📚 Creating course catalog tables...")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id                    TEXT PRIMARY KEY,
            name                  TEXT NOT NULL,
            category              TEXT NOT NULL,
            target_class          TEXT NOT NULL,
            board                 TEXT,
            subjects              TEXT[],
            duration              TEXT,
            fee                   INTEGER NOT NULL,
            mode                  TEXT[],
            eligibility           TEXT,
            description           TEXT,
            study_material        TEXT,
            reference_books       TEXT[],
            test_frequency        TEXT,
            installment_available BOOLEAN DEFAULT TRUE,
            installment_plans     TEXT[]
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id                TEXT PRIMARY KEY,
            course_id         TEXT NOT NULL REFERENCES courses(id),
            batch_name        TEXT NOT NULL,
            timing            TEXT NOT NULL,
            days_per_week     INTEGER,
            days              TEXT,
            start_date        DATE,
            total_seats       INTEGER,
            enrolled_students INTEGER DEFAULT 0,
            mode              TEXT,
            branch_id         TEXT,
            is_active         BOOLEAN DEFAULT TRUE,
            note              TEXT
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            id                TEXT PRIMARY KEY,
            name              TEXT NOT NULL,
            qualification     TEXT,
            experience_years  INTEGER,
            subjects          TEXT[],
            assigned_courses  TEXT[],
            specialization    TEXT,
            teaching_style    TEXT,
            past_results      TEXT,
            availability      TEXT
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_topics (
            id               SERIAL PRIMARY KEY,
            course_id        TEXT NOT NULL REFERENCES courses(id),
            sequence_order   INTEGER NOT NULL,
            topic_name       TEXT NOT NULL,
            sub_topics       TEXT[],
            ncert_aligned    BOOLEAN DEFAULT TRUE,
            estimated_weeks  INTEGER,
            difficulty       TEXT CHECK (difficulty IN ('foundation', 'intermediate', 'advanced'))
        )
    """)

    # ── 3. Enrichment tables ──────────────────────────────────────────────────

    print("🏢 Creating enrichment tables...")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id                  TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            city                TEXT NOT NULL,
            area                TEXT,
            address             TEXT,
            contact             TEXT,
            modes_available     TEXT[],
            facilities          TEXT[],
            available_courses   TEXT[]
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS scholarships (
            id                       TEXT PRIMARY KEY,
            name                     TEXT NOT NULL,
            description              TEXT,
            discount_percent         INTEGER,
            discount_flat            INTEGER,
            eligibility              TEXT,
            applicable_courses       TEXT,
            deadline                 TEXT,
            installment_still_available BOOLEAN DEFAULT TRUE
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS demo_slots (
            id           TEXT PRIMARY KEY,
            course_id    TEXT NOT NULL REFERENCES courses(id),
            slot_date    DATE NOT NULL,
            slot_time    TEXT NOT NULL,
            duration_hours INTEGER DEFAULT 2,
            mode         TEXT,
            meeting_link TEXT,
            branch_id    TEXT,
            is_booked    BOOLEAN DEFAULT FALSE,
            topic        TEXT
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS course_outcomes (
            id                    SERIAL PRIMARY KEY,
            course_id             TEXT NOT NULL REFERENCES courses(id),
            avg_score_improvement TEXT,
            selection_rate        TEXT,
            past_rankers          TEXT,
            note                  TEXT
        )
    """)

    # ── 4. CRM and tracking tables ────────────────────────────────────────────

    print("👥 Creating CRM tables...")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS student_inquiries (
            id                SERIAL PRIMARY KEY,
            inquiry_ref       TEXT UNIQUE NOT NULL,
            call_id           TEXT,
            caller_hash       TEXT NOT NULL,
            student_name      TEXT,
            interested_course TEXT,
            class_or_target   TEXT,
            preferred_timing  TEXT,
            preferred_branch  TEXT,
            status            TEXT DEFAULT 'new',
            lead_stage        TEXT DEFAULT 'contacted'
                              CHECK (lead_stage IN ('new', 'contacted', 'demo_scheduled', 'follow_up', 'enrolled', 'lost')),
            notes             TEXT,
            created_at        TIMESTAMPTZ DEFAULT NOW(),
            updated_at        TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS demo_bookings (
            id               SERIAL PRIMARY KEY,
            demo_slot_id     TEXT NOT NULL REFERENCES demo_slots(id),
            inquiry_ref      TEXT REFERENCES student_inquiries(inquiry_ref),
            call_id          TEXT,
            caller_hash      TEXT NOT NULL,
            student_name     TEXT,
            confirmation_sms_sent BOOLEAN DEFAULT FALSE,
            booked_at        TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS communications_sent (
            id           SERIAL PRIMARY KEY,
            call_id      TEXT,
            caller_hash  TEXT,
            channel      TEXT DEFAULT 'sms' CHECK (channel IN ('sms', 'whatsapp', 'email')),
            recipient    TEXT,
            message_type TEXT,
            content      TEXT,
            status       TEXT DEFAULT 'sent',
            sent_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── 5. Session tables ─────────────────────────────────────────────────────

    print("💾 Creating session tables...")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS caller_profiles (
            id            SERIAL PRIMARY KEY,
            phone_hash    TEXT UNIQUE NOT NULL,
            total_calls   INTEGER DEFAULT 1,
            first_seen_at TIMESTAMPTZ DEFAULT NOW(),
            last_seen_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS caller_sessions (
            id                   SERIAL PRIMARY KEY,
            phone_hash           TEXT NOT NULL,
            call_id              TEXT,
            topics_discussed     TEXT[],
            courses_recommended  TEXT[],
            inquiry_ref          TEXT,
            created_at           TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    print("\n✅ All 16 tables created!\n")

    # ── 6. Seed from courses.json ─────────────────────────────────────────────

    if not COURSES_FILE.exists():
        print("⚠️  data/courses.json not found — skipping seed.")
        await conn.close()
        return

    print(f"🌱 Seeding from {COURSES_FILE}...")
    with open(COURSES_FILE) as f:
        data = json.load(f)

    # Courses
    for c in data.get("courses", []):
        await conn.execute("""
            INSERT INTO courses (id, name, category, target_class, board, subjects, duration,
                fee, mode, eligibility, description, study_material, reference_books,
                test_frequency, installment_available, installment_plans)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
            ON CONFLICT (id) DO NOTHING
        """,
        c["id"], c["name"], c["category"], c["target_class"],
        c.get("board"), c.get("subjects"), c.get("duration"),
        c["fee"], c.get("mode"), c.get("eligibility"), c.get("description"),
        c.get("study_material"), c.get("reference_books"),
        c.get("test_frequency"), c.get("installment_available", True),
        c.get("installment_plans"))
    print(f"  ✔ {len(data.get('courses', []))} courses seeded")

    # Batches
    for b in data.get("batches", []):
        await conn.execute("""
            INSERT INTO batches (id, course_id, batch_name, timing, days_per_week, days,
                start_date, total_seats, enrolled_students, mode, branch_id, is_active, note)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
            ON CONFLICT (id) DO NOTHING
        """,
        b["id"], b["course_id"], b["batch_name"], b["timing"],
        b.get("days_per_week"), b.get("days"),
        b.get("start_date"), b.get("total_seats"), b.get("enrolled_students", 0),
        b.get("mode"), b.get("branch_id"), b.get("is_active", True), b.get("note"))
    print(f"  ✔ {len(data.get('batches', []))} batches seeded")

    # Faculty
    for f in data.get("faculty", []):
        await conn.execute("""
            INSERT INTO faculty (id, name, qualification, experience_years, subjects,
                assigned_courses, specialization, teaching_style, past_results, availability)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (id) DO NOTHING
        """,
        f["id"], f["name"], f.get("qualification"), f.get("experience_years"),
        f.get("subjects"), f.get("assigned_courses"), f.get("specialization"),
        f.get("teaching_style"), f.get("past_results"), f.get("availability"))
    print(f"  ✔ {len(data.get('faculty', []))} faculty seeded")

    # Syllabus topics
    for t in data.get("syllabus_topics", []):
        await conn.execute("""
            INSERT INTO syllabus_topics (course_id, sequence_order, topic_name, sub_topics,
                ncert_aligned, estimated_weeks, difficulty)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
        """,
        t["course_id"], t["sequence_order"], t["topic_name"],
        t.get("sub_topics"), t.get("ncert_aligned", True),
        t.get("estimated_weeks"), t.get("difficulty"))
    print(f"  ✔ {len(data.get('syllabus_topics', []))} syllabus topics seeded")

    # Branches
    for br in data.get("branches", []):
        await conn.execute("""
            INSERT INTO branches (id, name, city, area, address, contact,
                modes_available, facilities, available_courses)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (id) DO NOTHING
        """,
        br["id"], br["name"], br["city"], br.get("area"), br.get("address"),
        br.get("contact"), br.get("modes_available"), br.get("facilities"),
        br.get("available_courses"))
    print(f"  ✔ {len(data.get('branches', []))} branches seeded")

    # Scholarships
    for s in data.get("scholarships", []):
        applicable = s.get("applicable_courses")
        if isinstance(applicable, list):
            applicable = ", ".join(applicable)
        await conn.execute("""
            INSERT INTO scholarships (id, name, description, discount_percent, discount_flat,
                eligibility, applicable_courses, deadline, installment_still_available)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (id) DO NOTHING
        """,
        s["id"], s["name"], s.get("description"),
        s.get("discount_percent"), s.get("discount_flat"),
        s.get("eligibility"), applicable,
        s.get("deadline"), s.get("installment_still_available", True))
    print(f"  ✔ {len(data.get('scholarships', []))} scholarships seeded")

    # Demo slots
    for d in data.get("demo_slots", []):
        await conn.execute("""
            INSERT INTO demo_slots (id, course_id, slot_date, slot_time, duration_hours,
                mode, meeting_link, branch_id, is_booked, topic)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (id) DO NOTHING
        """,
        d["id"], d["course_id"], d["slot_date"], d["slot_time"],
        d.get("duration_hours", 2), d.get("mode"), d.get("meeting_link"),
        d.get("branch_id"), d.get("is_booked", False), d.get("topic"))
    print(f"  ✔ {len(data.get('demo_slots', []))} demo slots seeded")

    # Outcomes
    for o in data.get("outcomes", []):
        await conn.execute("""
            INSERT INTO course_outcomes (course_id, avg_score_improvement,
                selection_rate, past_rankers, note)
            VALUES ($1,$2,$3,$4,$5)
        """,
        o["course_id"], o.get("avg_score_improvement"),
        o.get("selection_rate"), o.get("past_rankers"), o.get("note"))
    print(f"  ✔ {len(data.get('outcomes', []))} outcome records seeded")

    await conn.close()

    print("\n🎉 Database setup complete! UltraCounsel is ready.")
    print("   16 tables created + full course catalog seeded.")
    print("\nNext steps:")
    print("  1. Set all variables in .env")
    print("  2. Run: python -m uvicorn main:app --reload")
    print("  3. Configure Plivo webhook to point to /api/webhook/answer")


if __name__ == "__main__":
    asyncio.run(setup())
