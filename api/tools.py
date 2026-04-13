"""
api/tools.py
HTTP endpoints for all 10 Ultravox tools.
These are called by Ultravox during a live call when Sage invokes a tool.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from lib.tools.search_courses import search_courses
from lib.tools.get_course_details import get_course_details
from lib.tools.check_batch_availability import check_batch_availability
from lib.tools.find_nearest_branch import find_nearest_branch
from lib.tools.check_scholarship import check_scholarship
from lib.tools.log_student_inquiry import log_student_inquiry
from lib.tools.send_learning_plan import send_learning_plan
from lib.tools.book_demo_class import book_demo_class
from lib.tools.schedule_appointment import schedule_appointment
from lib.tools.get_batch_stats import get_batch_stats

router = APIRouter(prefix="/api/tools", tags=["tools"])


# ── Request models ────────────────────────────────────────────────────────────

class SearchCoursesRequest(BaseModel):
    query: str
    call_id: str


class CourseDetailsRequest(BaseModel):
    course_id: str
    call_id: str


class BatchAvailabilityRequest(BaseModel):
    course_id: str
    call_id: str
    preferred_time: Optional[str] = ""


class NearestBranchRequest(BaseModel):
    city_or_area: str
    course_id: str
    call_id: str


class ScholarshipRequest(BaseModel):
    course_id: str
    call_id: str
    student_profile: Optional[str] = ""


class LogInquiryRequest(BaseModel):
    call_id: str
    student_name: str
    interested_course: str
    class_or_target: str
    preferred_timing: Optional[str] = ""
    preferred_branch: Optional[str] = ""
    caller_number_hash: str


class SendLearningPlanRequest(BaseModel):
    call_id: str
    course_id: str
    recipient_phone: str
    student_name: str


class BookDemoRequest(BaseModel):
    call_id: str
    course_id: str
    preferred_date: Optional[str] = "any"
    student_name: str
    caller_number_hash: str


class ScheduleAppointmentRequest(BaseModel):
    call_id: str
    student_name: str
    caller_hash: str
    course_id: Optional[str] = ""
    preferred_date: str
    preferred_time: str
    branch_or_city: str
    appointment_type: Optional[str] = "counseling"


class BatchStatsRequest(BaseModel):
    course_id: str
    call_id: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/search-courses")
async def tool_search_courses(req: SearchCoursesRequest):
    return await search_courses(req.query, req.call_id)


@router.post("/course-details")
async def tool_course_details(req: CourseDetailsRequest):
    return await get_course_details(req.course_id, req.call_id)


@router.post("/batch-availability")
async def tool_batch_availability(req: BatchAvailabilityRequest):
    return await check_batch_availability(
        req.course_id,
        req.preferred_time or "",
        req.call_id
    )


@router.post("/nearest-branch")
async def tool_nearest_branch(req: NearestBranchRequest):
    return await find_nearest_branch(req.city_or_area, req.course_id, req.call_id)


@router.post("/scholarship")
async def tool_scholarship(req: ScholarshipRequest):
    return await check_scholarship(
        req.course_id,
        req.student_profile or "",
        req.call_id
    )


@router.post("/log-inquiry")
async def tool_log_inquiry(req: LogInquiryRequest):
    return await log_student_inquiry(
        req.call_id,
        req.student_name,
        req.interested_course,
        req.class_or_target,
        req.preferred_timing or "",
        req.preferred_branch or "",
        req.caller_number_hash,
    )


@router.post("/send-learning-plan")
async def tool_send_learning_plan(req: SendLearningPlanRequest):
    return await send_learning_plan(
        req.call_id,
        req.course_id,
        req.recipient_phone,
        req.student_name,
    )


@router.post("/book-demo")
async def tool_book_demo(req: BookDemoRequest):
    return await book_demo_class(
        req.call_id,
        req.course_id,
        req.preferred_date or "any",
        req.student_name,
        req.caller_number_hash,
    )


@router.post("/schedule-appointment")
async def tool_schedule_appointment(req: ScheduleAppointmentRequest):
    return await schedule_appointment(
        req.call_id,
        req.student_name,
        req.caller_hash,
        req.course_id or "",
        req.preferred_date,
        req.preferred_time,
        req.branch_or_city,
        req.appointment_type or "counseling",
    )


@router.post("/batch-stats")
async def tool_batch_stats(req: BatchStatsRequest):
    return await get_batch_stats(req.course_id, req.call_id)
