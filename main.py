"""活动报名平台 — FastAPI 应用入口"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from config import SECRET_KEY, UPLOAD_DIR
from database import Base, engine, get_db
from models.user import User
from templating import templates

# ────────────────────────── lifespan ──────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理：启动时建表 & 创建上传目录，关闭时释放资源"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # 导入所有模型以确保 Base.metadata 包含全部表
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


# ────────────────────────── 创建应用 ──────────────────────────

app = FastAPI(
    title="活动报名平台",
    description="活动组织者可以发起活动，用户可以浏览、搜索、报名活动",
    version="0.1.0",
    lifespan=lifespan,
)

# Session 中间件
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 静态文件挂载
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ────────────────────────── 注册路由 ──────────────────────────

from routers.activities import router as activities_router  # noqa: E402
from routers.auth import router as auth_router  # noqa: E402
from routers.comments import router as comments_router  # noqa: E402
from routers.notifications import router as notifications_router  # noqa: E402
from routers.registrations import router as registrations_router  # noqa: E402
from routers.users import router as users_router  # noqa: E402

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(activities_router)
app.include_router(registrations_router)
app.include_router(comments_router)
app.include_router(notifications_router)


# ────────────────────────── 首页 ──────────────────────────────


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """从 Session 获取可选用户"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


@app.get("/")
async def index(
    request: Request,
    user: User | None = Depends(get_optional_user),
    keyword: str = "",
    category: str = "",
    tag: str = "",
    page: int = 1,
):
    """首页活动广场"""
    from services.activity_service import ActivityService

    svc = ActivityService(next(get_db()))
    result = svc.search(
        keyword=keyword or None, category=category or None, tag=tag or None, page=page
    )
    # 构建活动ID到人数的映射
    zero = {"approved": 0, "pending": 0, "waitlist": 0}
    counts: dict[int, dict[str, int]] = {}
    for act in result["results"]:
        counts[act.id] = getattr(act, "_counts", zero.copy())
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "activities": result,
            "counts": counts,
            "keyword": keyword,
            "category": category,
            "tag": tag,
        },
    )


# ────────────────────────── 入口 ──────────────────────────────

if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
