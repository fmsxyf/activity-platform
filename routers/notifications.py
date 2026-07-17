"""通知路由"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from services.notification_service import NotificationService
from templating import templates

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get("")
async def list_notifications(
    request: Request,
    page: int = 1,
    user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    """通知列表"""
    result = svc.get_notifications(user.id, page)
    return templates.TemplateResponse(
        request, "notifications/list.html", {"user": user, "notifications": result}
    )


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    """未读数（JSON）"""
    count = svc.get_unread_count(user.id)
    return JSONResponse({"count": count})


@router.post("/{notification_id}/read")
async def mark_read(
    request: Request,
    notification_id: int,
    user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    """标记已读"""
    svc.mark_read(notification_id, user.id)
    return RedirectResponse(url="/notifications", status_code=302)


@router.post("/read-all")
async def mark_all_read(
    request: Request,
    user: User = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    """全部已读"""
    svc.mark_all_read(user.id)
    return RedirectResponse(url="/notifications", status_code=302)
