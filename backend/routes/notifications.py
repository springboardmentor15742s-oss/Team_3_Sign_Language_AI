"""
Notification & Reminder System routes — roadmap section 12.

    GET  /api/notifications                 list (personal + broadcast), triggers reminder check
    GET  /api/notifications/unread-count     small badge-count endpoint for the navbar bell
    POST /api/notifications/{id}/read        mark one notification read
    POST /api/notifications/read-all         mark everything read
    POST /api/notifications/announcement     Administrator-only — broadcast a platform announcement
"""
from fastapi import APIRouter, Depends

from database import db
from deps import get_current_user, require_roles
from notifications.service import create_announcement, maybe_create_practice_reminder
from schemas.models import AnnouncementCreateRequest

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(current_user=Depends(get_current_user)):
    maybe_create_practice_reminder(current_user["id"])
    notifications = db.list_notifications_for_user(current_user["id"])
    unread_count = db.count_unread_notifications(current_user["id"])
    return {"notifications": notifications, "unread_count": unread_count}


@router.get("/unread-count")
def unread_count(current_user=Depends(get_current_user)):
    return {"unread_count": db.count_unread_notifications(current_user["id"])}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, current_user=Depends(get_current_user)):
    db.mark_notification_read(notification_id, current_user["id"])
    return {"marked_read": notification_id}


@router.post("/read-all")
def mark_all_read(current_user=Depends(get_current_user)):
    db.mark_all_notifications_read(current_user["id"])
    return {"marked_all_read": True}


@router.post("/announcement")
def post_announcement(
    payload: AnnouncementCreateRequest, current_user=Depends(require_roles("Administrator"))
):
    return create_announcement(payload.title, payload.message)
