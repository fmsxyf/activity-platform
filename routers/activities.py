"""活动路由"""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from config import UPLOAD_DIR
from database import get_db
from dependencies import get_current_user, get_optional_user
from flash import flash
from models.user import User
from services.activity_service import ActivityService
from templating import templates

router = APIRouter(prefix="/activities", tags=["activities"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
CATEGORIES = ["运动", "读书", "聚会", "旅行", "学习", "其他"]


def get_activity_service(db: Session = Depends(get_db)) -> ActivityService:
    return ActivityService(db)


# ────────────────────────── 辅助函数 ──────────────────────────


def _parse_form_data(form: FormData) -> dict[str, object]:
    """从表单数据构建活动 dict"""
    data: dict[str, object] = {}
    for key in ("title", "description", "category", "location"):
        val = form.get(key)
        data[key] = str(val) if val else ""

    data["start_time"] = datetime.fromisoformat(str(form.get("start_time", "")))
    data["end_time"] = datetime.fromisoformat(str(form.get("end_time", "")))
    data["max_participants"] = int(str(form.get("max_participants", "0")))
    data["fee"] = int(str(form.get("fee", "0")))

    deadline = form.get("registration_deadline")
    data["registration_deadline"] = (
        datetime.fromisoformat(str(deadline)) if deadline and str(deadline) else None
    )
    data["status"] = str(form.get("action", "published"))

    # 标签
    tags_raw = str(form.get("tags", ""))
    data["tags"] = [t.strip() for t in tags_raw.split(",") if t.strip()]
    return data


def _save_cover(file: UploadFile | None) -> str | None:
    """保存封面图片"""
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的图片格式：{ext}")
    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise ValueError("图片大小不能超过 2MB")
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)
    return filename


# ────────────────────────── 路由 ──────────────────────────


@router.get("/create")
async def create_page(request: Request, user: User = Depends(get_current_user)):
    """创建活动页面"""
    return templates.TemplateResponse(
        request, "activities/create.html", {"user": user, "categories": CATEGORIES}
    )


@router.post("/create")
async def create(
    request: Request,
    user: User = Depends(get_current_user),
    svc: ActivityService = Depends(get_activity_service),
):
    """提交创建活动"""
    try:
        form = await request.form()
        data = _parse_form_data(form)
        cover = form.get("cover_image")
        if hasattr(cover, "filename"):
            data["cover_image"] = _save_cover(cover)  # type: ignore[arg-type]
        svc.create(user.id, data)
        flash(request, "活动创建成功！")
        return RedirectResponse(url="/", status_code=302)
    except ValueError as e:
        flash(request, str(e), "error")
        return templates.TemplateResponse(
            request, "activities/create.html", {"user": user, "categories": CATEGORIES}
        )


@router.get("/{activity_id}")
async def detail(
    request: Request,
    activity_id: int,
    user=Depends(get_optional_user),
    svc: ActivityService = Depends(get_activity_service),
):
    """活动详情页"""
    activity = svc.get_by_id(activity_id)
    if not activity:
        return templates.TemplateResponse(
            request, "error.html", {"error": "活动不存在", "code": 404}
        )
    counts = getattr(activity, "_counts", {"approved": 0, "pending": 0, "waitlist": 0})
    # 直接查库获取已通过报名者（避免 ORM 关系在 Session 关闭后失效）
    from models.registration import Registration
    from models.user import User as UserModel

    approved_regs = svc.db.execute(
        select(Registration)
        .where(
            Registration.activity_id == activity_id,  # type: ignore[arg-type]
            Registration.status == "approved",  # type: ignore[arg-type]
        )
    ).scalars().all()
    participants: list[dict[str, object]] = []
    for r in approved_regs:
        u = svc.db.get(UserModel, r.user_id)
        participants.append({
            "nickname": u.nickname if u else "未知",
            "checked_in": r.checked_in,
        })
    return templates.TemplateResponse(
        request, "activities/detail.html",
        {
            "user": user, "activity": activity,
            "counts": {activity.id: counts},
            "participants": participants,
        },
    )


@router.get("/{activity_id}/edit")
async def edit_page(
    request: Request,
    activity_id: int,
    user: User = Depends(get_current_user),
    svc: ActivityService = Depends(get_activity_service),
):
    """编辑活动页面"""
    activity = svc.get_by_id(activity_id)
    if not activity or activity.creator_id != user.id:
        flash(request, "无权编辑此活动", "error")
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        request,
        "activities/edit.html",
        {"user": user, "activity": activity, "categories": CATEGORIES},
    )


@router.post("/{activity_id}/edit")
async def edit(
    request: Request,
    activity_id: int,
    user: User = Depends(get_current_user),
    svc: ActivityService = Depends(get_activity_service),
):
    """提交编辑活动"""
    try:
        form = await request.form()
        data = _parse_form_data(form)
        cover = form.get("cover_image")
        if hasattr(cover, "filename"):
            data["cover_image"] = _save_cover(cover)  # type: ignore[arg-type]
        svc.update(activity_id, user.id, data)
        flash(request, "活动已更新")
        return RedirectResponse(url=f"/activities/{activity_id}", status_code=302)
    except ValueError as e:
        flash(request, str(e), "error")
        activity = svc.get_by_id(activity_id)
        return templates.TemplateResponse(
            request,
            "activities/edit.html",
            {"user": user, "activity": activity, "categories": CATEGORIES},
        )


@router.post("/{activity_id}/publish")
async def publish(
    request: Request,
    activity_id: int,
    user: User = Depends(get_current_user),
    svc: ActivityService = Depends(get_activity_service),
):
    """发布草稿"""
    try:
        svc.publish(activity_id, user.id)
        flash(request, "活动已发布")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url=f"/activities/{activity_id}", status_code=302)


@router.post("/{activity_id}/cancel")
async def cancel(
    request: Request,
    activity_id: int,
    user: User = Depends(get_current_user),
    svc: ActivityService = Depends(get_activity_service),
):
    """取消活动"""
    try:
        svc.cancel(activity_id, user.id)
        flash(request, "活动已取消")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url=f"/activities/{activity_id}", status_code=302)
