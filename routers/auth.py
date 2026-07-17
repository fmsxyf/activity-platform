"""认证路由"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import REMEMBER_ME_MAX_AGE
from database import get_db
from dependencies import get_optional_user
from flash import flash
from services.auth_service import AuthService
from templating import templates

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """获取 AuthService 实例（依赖注入）"""
    return AuthService(db)


@router.get("/login")
async def login_page(request: Request, user=Depends(get_optional_user)):
    """登录页面"""
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "auth/login.html")


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(default=False),
    auth_service: AuthService = Depends(get_auth_service),
):
    """提交登录"""
    user = auth_service.authenticate(email, password)
    if not user:
        flash(request, "邮箱或密码错误", "error")
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"email": email, "remember_me": remember_me},
            status_code=401,
        )

    # 写入 Session
    request.session["user_id"] = user.id
    if remember_me:
        request.session["_max_age"] = REMEMBER_ME_MAX_AGE

    flash(request, f"欢迎回来，{user.nickname}！")
    return RedirectResponse(url="/", status_code=302)


@router.get("/register")
async def register_page(request: Request, user=Depends(get_optional_user)):
    """注册页面"""
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "auth/register.html")


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nickname: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    """提交注册"""
    try:
        user = auth_service.register(email, password, nickname)
    except ValueError as e:
        flash(request, str(e), "error")
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"email": email, "nickname": nickname},
            status_code=400,
        )

    # 自动登录
    request.session["user_id"] = user.id
    flash(request, f"注册成功！欢迎 {user.nickname}！")
    return RedirectResponse(url="/", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    """退出登录"""
    request.session.clear()
    flash(request, "已安全退出")
    return RedirectResponse(url="/", status_code=302)
