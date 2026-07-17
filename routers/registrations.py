"""报名路由"""

from io import StringIO

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from flash import flash
from models.user import User
from services.registration_service import RegistrationService
from templating import templates

router = APIRouter(tags=["registrations"])


def get_registration_service(db: Session = Depends(get_db)) -> RegistrationService:
    return RegistrationService(db)


@router.post("/activities/{activity_id}/register")
async def register_activity(
    request: Request,
    activity_id: int,
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """报名活动"""
    try:
        svc.register(user.id, activity_id)
        flash(request, "报名成功！")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url=f"/activities/{activity_id}", status_code=302)


@router.post("/registrations/{registration_id}/cancel")
async def cancel_registration(
    request: Request,
    registration_id: int,
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """取消报名"""
    try:
        svc.cancel(registration_id, user.id)
        flash(request, "已取消报名")
    except ValueError as e:
        flash(request, str(e), "error")
    return RedirectResponse(url="/users/my-registrations", status_code=302)


@router.get("/activities/{activity_id}/registrations")
async def manage_registrations(
    request: Request,
    activity_id: int,
    status: str = "",
    page: int = 1,
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """报名管理页"""
    result = svc.get_by_activity(activity_id, status=status or None, page=page)
    return templates.TemplateResponse(
        request,
        "registrations/manage.html",
        {
            "user": user,
            "registrations": result,
            "activity_id": activity_id,
            "current_status": status,
        },
    )


@router.post("/registrations/{registration_id}/approve")
async def approve(
    request: Request,
    registration_id: int,
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """审核通过"""
    try:
        reg = svc.approve(registration_id, user.id)
        flash(request, "已通过")
        return RedirectResponse(
            url=f"/activities/{reg.activity_id}/registrations", status_code=302
        )
    except ValueError as e:
        flash(request, str(e), "error")
        return RedirectResponse(url="/", status_code=302)


@router.post("/registrations/{registration_id}/reject")
async def reject(
    request: Request,
    registration_id: int,
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """审核拒绝"""
    try:
        reg = svc.reject(registration_id, user.id)
        flash(request, "已拒绝")
        return RedirectResponse(
            url=f"/activities/{reg.activity_id}/registrations", status_code=302
        )
    except ValueError as e:
        flash(request, str(e), "error")
        return RedirectResponse(url="/", status_code=302)


@router.post("/registrations/{registration_id}/check-in")
async def check_in(
    request: Request,
    registration_id: int,
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """签到"""
    try:
        reg = svc.check_in(registration_id, user.id)
        flash(request, "签到成功")
        return RedirectResponse(
            url=f"/activities/{reg.activity_id}/registrations", status_code=302
        )
    except ValueError as e:
        flash(request, str(e), "error")
        return RedirectResponse(url="/", status_code=302)


@router.get("/activities/{activity_id}/registrations.json")
async def registrations_json(
    activity_id: int,
    status: str = "",
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """报名列表 JSON（供前端轮询）"""
    result = svc.get_by_activity(activity_id, status=status or None, page=1)
    items = []
    for reg in result["results"]:
        items.append(
            {
                "id": reg.id,
                "nickname": reg.user.nickname,
                "email": reg.user.email,
                "status": reg.status,
                "checked_in": reg.checked_in,
                "created_at": reg.created_at.strftime("%m/%d %H:%M"),
                "no_show_count": reg.user.no_show_count,
            }
        )
    return JSONResponse({"items": items, "total": result["total"]})


@router.get("/activities/{activity_id}/export")
async def export_csv(
    activity_id: int,
    user: User = Depends(get_current_user),
    svc: RegistrationService = Depends(get_registration_service),
):
    """导出 CSV"""
    try:
        csv_data = svc.export_csv(activity_id, user.id)
        return StreamingResponse(
            StringIO(csv_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f"attachment; filename=activity_{activity_id}.csv"
                ),
            },
        )
    except ValueError as e:
        return {"error": str(e)}
