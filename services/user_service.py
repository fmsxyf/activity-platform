"""用户 Service"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.activity import Activity
from models.registration import Registration
from models.user import User

PAGE_SIZE = 10


class UserService:
    """用户服务：个人信息管理、历史记录查询"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user(self, user_id: int) -> User | None:
        """获取用户信息"""
        return self.db.get(User, user_id)

    def update_profile(self, user_id: int, nickname: str | None) -> User:
        """更新个人信息（不含邮箱和密码）"""
        user = self.db.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")
        if nickname and nickname.strip():
            user.nickname = nickname.strip()
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_my_registrations(self, user_id: int, page: int = 1) -> dict[str, Any]:
        """我报名的活动列表（分页）"""
        offset = (page - 1) * PAGE_SIZE
        total = (
            self.db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(
                    Registration.user_id == user_id  # type: ignore[arg-type]
                )
            )
            or 0
        )
        registrations = (
            self.db.execute(
                select(Registration)
                .where(Registration.user_id == user_id)  # type: ignore[arg-type]
                .order_by(Registration.created_at.desc())  # type: ignore[attr-defined]
                .offset(offset)
                .limit(PAGE_SIZE)
            )
            .scalars()
            .all()
        )
        return {
            "results": list(registrations),
            "total": total,
            "page": page,
            "total_pages": max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        }

    def get_my_activities(self, user_id: int, page: int = 1) -> dict[str, Any]:
        """我发起的活动列表（分页）"""
        offset = (page - 1) * PAGE_SIZE
        total = (
            self.db.scalar(
                select(func.count())
                .select_from(Activity)
                .where(
                    Activity.creator_id == user_id  # type: ignore[arg-type]
                )
            )
            or 0
        )
        activities = (
            self.db.execute(
                select(Activity)
                .where(Activity.creator_id == user_id)  # type: ignore[arg-type]
                .order_by(Activity.created_at.desc())  # type: ignore[attr-defined]
                .offset(offset)
                .limit(PAGE_SIZE)
            )
            .scalars()
            .all()
        )
        return {
            "results": list(activities),
            "total": total,
            "page": page,
            "total_pages": max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        }
