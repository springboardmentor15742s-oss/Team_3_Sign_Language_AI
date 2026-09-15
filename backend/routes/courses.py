"""
Course & Content Service (Sign Language Course Management + Gesture/Content
delivery via video lessons) — the "watch like YouTube" module from the
architecture diagram's Microservices layer.

Browsing the catalog is open to any authenticated user (Learner, Instructor,
Accessibility Trainer, Administrator). Creating courses/lessons is gated to
Instructor / Accessibility Trainer / Administrator via require_roles(),
reusing the same RBAC pattern as the rest of the app (see deps.py).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from config import COURSE_CATEGORIES, COURSE_LEVELS, COURSE_MANAGER_ROLES
from database import db
from deps import get_current_user, require_roles
from notifications.service import notify_course_completion
from schemas.models import (
    CourseCreateRequest,
    CourseDetailOut,
    CourseOut,
    CourseProgressOut,
    EnrollmentOut,
    LessonCreateRequest,
    LessonOut,
)

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/meta")
def get_course_meta():
    """Category & level options for filter dropdowns and the course-creation form."""
    return {"categories": COURSE_CATEGORIES, "levels": COURSE_LEVELS}


@router.get("", response_model=list[CourseOut])
def list_courses(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
):
    return db.list_courses(category=category, level=level, search=search)


@router.get("/my-enrollments", response_model=list[EnrollmentOut])
def my_enrollments(current_user=Depends(get_current_user)):
    return db.list_my_enrollments(current_user["id"])


@router.get("/{course_id}", response_model=CourseDetailOut)
def get_course_detail(course_id: int, current_user=Depends(get_current_user)):
    course = db.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    lessons = db.list_lessons(course_id)
    watched_ids = db.get_lesson_progress_map(current_user["id"], course_id)
    lessons_out = [
        {**lesson, "watched": lesson["id"] in watched_ids} for lesson in lessons
    ]
    progress = db.get_course_progress(current_user["id"], course_id)
    return {
        **course,
        "lesson_count": len(lessons),
        "lessons": lessons_out,
        "is_enrolled": db.is_enrolled(current_user["id"], course_id),
        "progress_percent": progress["percent"],
        "watched_lessons": progress["watched_lessons"],
    }


@router.post("/{course_id}/enroll")
def enroll_in_course(course_id: int, current_user=Depends(get_current_user)):
    course = db.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    db.enroll_user(current_user["id"], course_id)
    return {"enrolled": True, "course_id": course_id}


@router.post("/lessons/{lesson_id}/watched", response_model=CourseProgressOut)
def mark_lesson_watched(lesson_id: int, current_user=Depends(get_current_user)):
    lesson = db.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")

    progress_before = db.get_course_progress(current_user["id"], lesson["course_id"])
    progress = db.mark_lesson_watched(current_user["id"], lesson_id)
    db.log_practice_activity(current_user["id"], f"Watched lesson: {lesson['title']}")

    if progress_before["percent"] < 100 and progress["percent"] >= 100:
        course = db.get_course(lesson["course_id"])
        if course:
            notify_course_completion(current_user["id"], course["title"])

    return progress


@router.post("", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseCreateRequest,
    current_user=Depends(require_roles(*COURSE_MANAGER_ROLES)),
):
    if payload.category not in COURSE_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid course category.")
    if payload.level not in COURSE_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid course level.")
    course_id = db.create_course(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        level=payload.level,
        thumbnail_emoji=payload.thumbnail_emoji,
        created_by=current_user["id"],
    )
    course = db.get_course(course_id)
    return {**course, "lesson_count": 0}


@router.post("/{course_id}/lessons", response_model=LessonOut, status_code=201)
def add_lesson(
    course_id: int,
    payload: LessonCreateRequest,
    current_user=Depends(require_roles(*COURSE_MANAGER_ROLES)),
):
    course = db.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    lesson_id = db.create_lesson(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        video_id=payload.video_id,
        duration_seconds=payload.duration_seconds,
    )
    lesson = db.get_lesson(lesson_id)
    return {**lesson, "watched": False}
