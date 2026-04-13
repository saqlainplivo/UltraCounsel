"""
api/export.py
CSV export endpoints for student inquiries and appointments.
Acts like a receptionist log — downloadable and opens in Excel.
"""

import csv
import io
import logging
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from lib.db import get_pool

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/export/students")
async def export_students():
    """Download all student inquiries as CSV (opens in Excel)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                si.inquiry_ref,
                si.student_name,
                si.interested_course,
                si.class_or_target,
                si.preferred_timing,
                si.preferred_branch,
                si.lead_stage,
                si.status,
                si.created_at,
                db.booked_at          AS demo_booked_at,
                ds.slot_date          AS demo_date,
                ds.slot_time          AS demo_time,
                ds.mode               AS demo_mode,
                b.name                AS demo_branch,
                cs.sent_at            AS sms_sent_at
            FROM student_inquiries si
            LEFT JOIN demo_bookings db     ON db.inquiry_ref = si.inquiry_ref
            LEFT JOIN demo_slots ds        ON ds.id          = db.demo_slot_id
            LEFT JOIN branches b           ON b.id           = ds.branch_id
            LEFT JOIN communications_sent cs ON cs.call_id   = si.call_id
                                            AND cs.channel   = 'sms'
            ORDER BY si.created_at DESC
        """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Inquiry Ref", "Student Name", "Course Interest", "Class / Target Exam",
        "Preferred Timing", "Preferred Branch", "Lead Stage", "Status",
        "Inquiry Date", "Demo Booked At", "Demo Date", "Demo Time",
        "Demo Mode", "Demo Branch", "SMS Sent At"
    ])
    for r in rows:
        writer.writerow([
            r["inquiry_ref"] or "",
            r["student_name"] or "",
            r["interested_course"] or "",
            r["class_or_target"] or "",
            r["preferred_timing"] or "",
            r["preferred_branch"] or "",
            r["lead_stage"] or "",
            r["status"] or "",
            r["created_at"].strftime("%d-%m-%Y %H:%M") if r["created_at"] else "",
            r["demo_booked_at"].strftime("%d-%m-%Y %H:%M") if r["demo_booked_at"] else "Not booked",
            str(r["demo_date"]) if r["demo_date"] else "",
            r["demo_time"] or "",
            r["demo_mode"] or "",
            r["demo_branch"] or "",
            r["sms_sent_at"].strftime("%d-%m-%Y %H:%M") if r["sms_sent_at"] else "Not sent",
        ])

    filename = f"apex_students_{datetime.now().strftime('%Y%m%d')}.csv"
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/api/export/appointments")
async def export_appointments():
    """Download all scheduled appointments as CSV (opens in Excel)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                ca.id,
                ca.student_name,
                ca.appt_type,
                ca.appt_date,
                ca.appt_time,
                ca.mode,
                ca.status,
                ca.notes,
                ca.created_at,
                ca.confirmed_at,
                b.name   AS branch_name,
                b.city   AS branch_city,
                c.name   AS course_name,
                ca.inquiry_ref,
                ca.meeting_link
            FROM custom_appointments ca
            LEFT JOIN branches b ON b.id = ca.branch_id
            LEFT JOIN courses  c ON c.id = ca.course_id
            ORDER BY ca.appt_date DESC, ca.appt_time DESC
        """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Appointment ID", "Student Name", "Type", "Date", "Time", "Mode",
        "Status", "Branch / Location", "City", "Course", "Inquiry Ref",
        "Meeting Link", "Notes", "Created At", "Confirmed At"
    ])
    for r in rows:
        writer.writerow([
            f"APT-{r['id']:05d}",
            r["student_name"] or "",
            (r["appt_type"] or "").replace("_", " ").title(),
            str(r["appt_date"]) if r["appt_date"] else "",
            r["appt_time"] or "",
            r["mode"] or "",
            r["status"] or "",
            r["branch_name"] or "Online",
            r["branch_city"] or "Pan-India",
            r["course_name"] or "",
            r["inquiry_ref"] or "",
            r["meeting_link"] or "",
            r["notes"] or "",
            r["created_at"].strftime("%d-%m-%Y %H:%M") if r["created_at"] else "",
            r["confirmed_at"].strftime("%d-%m-%Y %H:%M") if r["confirmed_at"] else "",
        ])

    filename = f"apex_appointments_{datetime.now().strftime('%Y%m%d')}.csv"
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
