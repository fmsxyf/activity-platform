"""FastAPI 依赖注入"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:  # noqa: B008
    """从 Session 中读取 user_id，查询并返回当前登录用户。
    未登录则重定向到登录页。"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    user: User | None = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:  # noqa: B008
    """获取当前用户（可选），未登录返回 None"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)
