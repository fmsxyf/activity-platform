"""用户路由"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from flash import flash
from models.user import User
from services.user_service import UserService
from templating import templates

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """获取 UserService 实例"""
    return UserService(db)


def get_session_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """获取当前会话用户（可选，用于模板渲染）"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


@router.get("/profile")
async def profile_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    """个人中心页面"""
    return templates.TemplateResponse(request, "users/profile.html", {"user": user})


@router.post("/profile")
async def update_profile(
    request: Request,
    nickname: str = Form(...),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """更新个人信息"""
    try:
        user_service.update_profile(current_user.id, nickname)
        flash(request, "个人信息已更新")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url="/users/profile", status_code=302)


@router.get("/my-registrations")
async def my_registrations(
    request: Request,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """我的报名记录（分页）"""
    result = user_service.get_my_registrations(current_user.id, page)
    return templates.TemplateResponse(
        request,
        "users/profile.html",
        {
            "user": current_user,
            "tab": "registrations",
            "registrations": result,
        },
    )


@router.get("/my-activities")
async def my_activities(
    request: Request,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """我发起的活动（分页）"""
    result = user_service.get_my_activities(current_user.id, page)
    return templates.TemplateResponse(
        request,
        "users/profile.html",
        {
            "user": current_user,
            "tab": "activities",
            "activities": result,
        },
    )
