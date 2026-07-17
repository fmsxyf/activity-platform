"""评论路由"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from flash import flash
from models.user import User
from services.comment_service import CommentService

router = APIRouter(tags=["comments"])


def get_comment_service(db: Session = Depends(get_db)) -> CommentService:
    return CommentService(db)


@router.post("/activities/{activity_id}/comments")
async def create_comment(
    request: Request,
    activity_id: int,
    content: str = Form(...),
    user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
):
    """发表评论"""
    try:
        svc.create(user.id, activity_id, content)
        flash(request, "评论成功")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url=f"/activities/{activity_id}", status_code=302)


@router.post("/comments/{comment_id}/reply")
async def reply_comment(
    request: Request,
    comment_id: int,
    content: str = Form(...),
    user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
):
    """回复评论"""
    comment = svc.db.get(
        __import__("models.comment", fromlist=["Comment"]).Comment, comment_id
    )
    if not comment:
        flash(request, "评论不存在", "error")
        return RedirectResponse(url="/", status_code=302)
    try:
        svc.create(user.id, comment.activity_id, content, parent_id=comment_id)
        flash(request, "回复成功")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url=f"/activities/{comment.activity_id}", status_code=302)


@router.post("/comments/{comment_id}/delete")
async def delete_comment(
    request: Request,
    comment_id: int,
    user: User = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
):
    """删除评论"""
    comment = svc.db.get(
        __import__("models.comment", fromlist=["Comment"]).Comment, comment_id
    )
    activity_id = comment.activity_id if comment else 0
    try:
        svc.delete(comment_id, user.id)
        flash(request, "评论已删除")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url=f"/activities/{activity_id}", status_code=302)
