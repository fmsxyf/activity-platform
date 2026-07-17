"""信誉 Service"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.activity import Activity
from models.registration import Registration
from models.user import User


class ReputationService:
    """信誉服务：失约计算、信誉标记判断"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def settle_no_shows(self, activity_id: int) -> int:
        """结算指定活动的失约：已通过但未签到且未记录的记为失约"""
        activity = self.db.get(Activity, activity_id)
        if not activity:
            return 0

        no_shows = (
            self.db.execute(
                select(Registration).where(
                    Registration.activity_id == activity_id,  # type: ignore[arg-type]
                    Registration.status == "approved",  # type: ignore[arg-type]
                    Registration.checked_in == False,  # type: ignore[arg-type] # noqa: E712
                    Registration.no_show_recorded == False,  # type: ignore[arg-type] # noqa: E712
                )
            )
            .scalars()
            .all()
        )

        count = 0
        for reg in no_shows:
            reg.no_show_recorded = True
            reg.user.no_show_count += 1
            if reg.user.no_show_count >= 3:
                reg.user.reputation_hidden = False
            reg.user.consecutive_good = 0
            count += 1

        if count:
            self.db.commit()
        return count

    def is_reputation_visible(self, user_id: int) -> bool:
        """判断失约标记是否应展示"""
        user = self.db.get(User, user_id)
        if not user:
            return False
        return not user.reputation_hidden

    def get_no_show_count(self, user_id: int) -> int:
        """获取累计失约次数"""
        user = self.db.get(User, user_id)
        if not user:
            return 0
        return user.no_show_count

    def record_good_attendance(self, user_id: int) -> None:
        """记录一次正常签到"""
        user = self.db.get(User, user_id)
        if not user:
            return
        user.consecutive_good += 1
        if user.consecutive_good >= 3 and not user.reputation_hidden:
            user.reputation_hidden = True
        self.db.commit()

    def get_reputation_info(self, user_id: int) -> dict[str, Any]:
        """获取信誉信息"""
        user = self.db.get(User, user_id)
        if not user:
            return {"no_show_count": 0, "is_visible": False, "consecutive_good": 0}
        return {
            "no_show_count": user.no_show_count,
            "is_visible": not user.reputation_hidden,
            "consecutive_good": user.consecutive_good,
        }
