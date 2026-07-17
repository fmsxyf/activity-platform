"""通知 Service"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.notification import Notification
from services.email_service import EmailService

PAGE_SIZE = 20


class NotificationService:
    """通知服务：站内通知 + 邮件"""

    def __init__(
        self,
        db: Session,
        email_service: EmailService | None = None,
    ) -> None:
        self.db = db
        self.email_service = email_service

    def create(
        self, user_id: int, type: str, title: str, content: str, link: str | None = None
    ) -> Notification:
        """创建站内通知"""
        notif = Notification(
            user_id=user_id, type=type, title=title, content=content, link=link
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def notify_registration_result(
        self, user_id: int, activity_title: str, result: str
    ) -> None:
        """报名审核结果通知"""
        label = "通过" if result == "approved" else "未通过"
        self.create(
            user_id,
            "registration_result",
            "报名审核结果",
            f"您在「{activity_title}」的报名已{label}审核",
            link="/users/my-registrations",
        )
        if self.email_service:
            self.email_service.send(
                "user@example.com",
                f"报名审核结果 - {activity_title}",
                f"您的报名已{label}审核。",
            )

    def notify_waitlist_promoted(self, user_id: int, activity_title: str) -> None:
        """候补转正通知"""
        self.create(
            user_id,
            "waitlist_promoted",
            "候补转正",
            f"您在「{activity_title}」的候补已转正，请等待审核",
            link="/users/my-registrations",
        )

    def notify_activity_cancelled(
        self, user_ids: list[int], activity_title: str
    ) -> None:
        """活动取消通知（批量）"""
        for uid in user_ids:
            self.create(
                uid,
                "activity_cancelled",
                "活动已取消",
                f"「{activity_title}」已被组织者取消",
                link="/",
            )

    def notify_new_comment(self, organizer_id: int, activity_title: str) -> None:
        """新评论通知"""
        self.create(
            organizer_id,
            "new_comment",
            "新评论",
            f"您的活动「{activity_title}」收到了新评论",
        )

    def get_unread_count(self, user_id: int) -> int:
        """获取未读通知数"""
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == user_id,  # type: ignore[arg-type]
                    Notification.is_read == False,  # type: ignore[arg-type] # noqa: E712
                )
            )
            or 0
        )

    def get_notifications(self, user_id: int, page: int = 1) -> dict[str, Any]:
        """获取通知列表"""
        offset = (page - 1) * PAGE_SIZE
        total = (
            self.db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == user_id  # type: ignore[arg-type]
                )
            )
            or 0
        )
        notifs = (
            self.db.execute(
                select(Notification)
                .where(Notification.user_id == user_id)  # type: ignore[arg-type]
                .order_by(Notification.created_at.desc())  # type: ignore[attr-defined]
                .offset(offset)
                .limit(PAGE_SIZE)
            )
            .scalars()
            .all()
        )
        return {
            "results": list(notifs),
            "total": total,
            "page": page,
            "total_pages": max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        }

    def mark_read(self, notification_id: int, user_id: int) -> None:
        """标记已读"""
        notif = self.db.get(Notification, notification_id)
        if notif and notif.user_id == user_id:
            notif.is_read = True
            self.db.commit()

    def mark_all_read(self, user_id: int) -> None:
        """全部标记已读"""
        self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,  # type: ignore[arg-type]
                Notification.is_read == False,  # type: ignore[arg-type] # noqa: E712
            )
        )
        unread = (
            self.db.execute(
                select(Notification).where(
                    Notification.user_id == user_id,  # type: ignore[arg-type]
                    Notification.is_read == False,  # type: ignore[arg-type] # noqa: E712
                )
            )
            .scalars()
            .all()
        )
        for n in unread:
            n.is_read = True
        self.db.commit()
