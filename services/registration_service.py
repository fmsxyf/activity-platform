"""报名 Service"""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.activity import Activity
from models.registration import Registration
from services.notification_service import NotificationService
from services.reputation_service import ReputationService

PAGE_SIZE = 20


class RegistrationService:
    """报名服务：报名、审核、候补、签到、导出"""

    def __init__(
        self,
        db: Session,
        notification_service: NotificationService | None = None,
        reputation_service: ReputationService | None = None,
    ) -> None:
        self.db = db
        self.notification_service = notification_service
        self.reputation_service = reputation_service

    def register(self, user_id: int, activity_id: int) -> Registration:
        """报名活动"""
        activity = self.db.get(Activity, activity_id)
        if not activity:
            raise ValueError("活动不存在")
        if activity.status not in ("published", "ongoing"):
            raise ValueError("活动当前不可报名")
        if activity.creator_id == user_id:
            raise ValueError("不能报名自己发起的活动")

        # 检查重复报名
        existing = self.db.execute(
            select(Registration).where(
                Registration.user_id == user_id,  # type: ignore[arg-type]
                Registration.activity_id == activity_id,  # type: ignore[arg-type]
            )
        ).scalar_one_or_none()
        if existing and existing.status != "cancelled":
            raise ValueError("您已报名此活动")

        # 检查报名截止时间
        deadline_ok = activity.registration_deadline
        if deadline_ok and deadline_ok < datetime.utcnow():
            raise ValueError("报名已截止")

        # 检查名额
        approved_count = self._count_approved(activity_id)
        max_p = activity.max_participants
        status = "waitlist" if max_p > 0 and approved_count >= max_p else "pending"

        reg = Registration(user_id=user_id, activity_id=activity_id, status=status)
        self.db.add(reg)
        self.db.commit()
        self.db.refresh(reg)
        return reg

    def cancel(self, registration_id: int, user_id: int) -> Registration:
        """取消报名"""
        reg = self.db.get(Registration, registration_id)
        if not reg:
            raise ValueError("报名记录不存在")
        if reg.user_id != user_id:
            raise ValueError("无权取消他人报名")
        reg.status = "cancelled"
        self.db.commit()
        self.db.refresh(reg)
        return reg

    def approve(self, registration_id: int, organizer_id: int) -> Registration:
        """审核通过"""
        reg = self._get_for_organizer(registration_id, organizer_id)
        if reg.status != "pending":
            raise ValueError("只能审核待审核的报名")
        # 再次检查名额
        approved_count = self._count_approved(reg.activity_id)
        max_p = reg.activity.max_participants
        if max_p > 0 and approved_count >= max_p:
            raise ValueError("活动名额已满")
        reg.status = "approved"
        self.db.commit()
        self.db.refresh(reg)
        if self.notification_service:
            act = self.db.get(Activity, reg.activity_id)
            title = act.title if act else "未知活动"
            self.notification_service.notify_registration_result(
                reg.user_id, title, "approved"
            )
        return reg

    def reject(self, registration_id: int, organizer_id: int) -> Registration:
        """审核拒绝"""
        reg = self._get_for_organizer(registration_id, organizer_id)
        if reg.status != "pending":
            raise ValueError("只能审核待审核的报名")
        reg.status = "rejected"
        self.db.commit()
        self.db.refresh(reg)
        if self.notification_service:
            act = self.db.get(Activity, reg.activity_id)
            title = act.title if act else "未知活动"
            self.notification_service.notify_registration_result(
                reg.user_id, title, "rejected"
            )
        # 触发候补递补
        self.promote_from_waitlist(reg.activity_id)
        return reg

    def check_in(self, registration_id: int, organizer_id: int) -> Registration:
        """手动签到"""
        reg = self._get_for_organizer(registration_id, organizer_id)
        if reg.status != "approved":
            raise ValueError("只能为已通过的报名签到")
        if reg.checked_in:
            raise ValueError("该用户已签到")
        reg.checked_in = True
        self.db.commit()
        self.db.refresh(reg)
        if self.reputation_service:
            self.reputation_service.record_good_attendance(reg.user_id)
        return reg

    def get_by_activity(
        self, activity_id: int, status: str | None = None, page: int = 1
    ) -> dict[str, Any]:
        """按活动查询报名列表"""
        offset = (page - 1) * PAGE_SIZE
        query = select(Registration).where(
            Registration.activity_id == activity_id  # type: ignore[arg-type]
        )
        count_q = (
            select(func.count())
            .select_from(Registration)
            .where(
                Registration.activity_id == activity_id  # type: ignore[arg-type]
            )
        )
        if status:
            query = query.where(Registration.status == status)  # type: ignore[arg-type]
            count_q = count_q.where(Registration.status == status)  # type: ignore[arg-type]
        total = self.db.scalar(count_q) or 0
        registrations = (
            self.db.execute(
                query.order_by(Registration.created_at.asc())  # type: ignore[attr-defined]
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

    def export_csv(self, activity_id: int, organizer_id: int) -> str:
        """导出已通过名单为 CSV"""
        activity = self.db.get(Activity, activity_id)
        if not activity or activity.creator_id != organizer_id:
            raise ValueError("无权导出")
        regs = (
            self.db.execute(
                select(Registration).where(
                    Registration.activity_id == activity_id,  # type: ignore[arg-type]
                    Registration.status == "approved",  # type: ignore[arg-type]
                )
            )
            .scalars()
            .all()
        )
        lines = ["昵称,邮箱,签到,报名时间"]
        for r in regs:
            checked = "是" if r.checked_in else "否"
            lines.append(f"{r.user.nickname},{r.user.email},{checked},{r.created_at}")
        return "\n".join(lines)

    def promote_from_waitlist(self, activity_id: int) -> int:
        """候补递补，返回递补人数"""
        activity = self.db.get(Activity, activity_id)
        if not activity:
            return 0
        promoted = 0
        while True:
            approved_count = self._count_approved(activity_id)
            max_p = activity.max_participants
            if max_p > 0 and approved_count >= max_p:
                break
            first_waiting = (
                self.db.execute(
                    select(Registration)
                    .where(
                        Registration.activity_id == activity_id,  # type: ignore[arg-type]
                        Registration.status == "waitlist",  # type: ignore[arg-type]
                    )
                    .order_by(Registration.created_at.asc())  # type: ignore[attr-defined]
                )
                .scalars()
                .first()
            )
            if not first_waiting:
                break
            first_waiting.status = "pending"
            promoted += 1
            if self.notification_service:
                self.notification_service.notify_waitlist_promoted(
                    first_waiting.user_id, activity.title
                )
        if promoted:
            self.db.commit()
        return promoted

    def _count_approved(self, activity_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(
                    Registration.activity_id == activity_id,  # type: ignore[arg-type]
                    Registration.status == "approved",  # type: ignore[arg-type]
                )
            )
            or 0
        )

    def _get_for_organizer(
        self, registration_id: int, organizer_id: int
    ) -> Registration:
        reg = self.db.get(Registration, registration_id)
        if not reg:
            raise ValueError("报名记录不存在")
        activity = self.db.get(Activity, reg.activity_id)
        if not activity or activity.creator_id != organizer_id:
            raise ValueError("无权操作")
        return reg
