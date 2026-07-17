"""评论 Service"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.comment import Comment
from models.registration import Registration
from services.notification_service import NotificationService

PAGE_SIZE = 20


class CommentService:
    """评论服务"""

    def __init__(
        self,
        db: Session,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.db = db
        self.notification_service = notification_service

    def create(
        self, user_id: int, activity_id: int, content: str, parent_id: int | None = None
    ) -> Comment:
        """发表评论。仅通过审核的参与者或活动组织者可评论。"""
        # 检查权限
        allowed = False
        activity = self.db.execute(
            select(Registration).where(
                Registration.user_id == user_id,  # type: ignore[arg-type]
                Registration.activity_id == activity_id,  # type: ignore[arg-type]
                Registration.status == "approved",  # type: ignore[arg-type]
            )
        ).scalar_one_or_none()
        if activity:
            allowed = True

        if not allowed:
            from models.activity import Activity

            act = self.db.get(Activity, activity_id)
            if act and act.creator_id == user_id:
                allowed = True

        if not allowed:
            raise ValueError("只有已通过审核的参与者或活动组织者可以评论")

        if not content or not content.strip():
            raise ValueError("评论内容不能为空")

        comment = Comment(
            user_id=user_id,
            activity_id=activity_id,
            content=content.strip(),
            parent_id=parent_id,
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)

        # 通知组织者
        if self.notification_service:
            act2 = self.db.get(
                __import__("models.activity", fromlist=["Activity"]).Activity,
                activity_id,
            )
            if act2 and act2.creator_id != user_id:
                self.notification_service.notify_new_comment(
                    act2.creator_id, act2.title
                )
        return comment

    def delete(self, comment_id: int, user_id: int) -> bool:
        """删除评论（仅作者或活动组织者）"""
        comment = self.db.get(Comment, comment_id)
        if not comment:
            return False
        from models.activity import Activity

        act = self.db.get(Activity, comment.activity_id)
        if comment.user_id != user_id and (not act or act.creator_id != user_id):
            raise ValueError("无权删除此评论")
        self.db.delete(comment)
        self.db.commit()
        return True

    def get_by_activity(self, activity_id: int, page: int = 1) -> dict[str, Any]:
        """获取活动评论列表（树形结构）"""
        offset = (page - 1) * PAGE_SIZE
        total = (
            self.db.scalar(
                select(func.count())
                .select_from(Comment)
                .where(
                    Comment.activity_id == activity_id,  # type: ignore[arg-type]
                    Comment.parent_id == None,  # type: ignore[arg-type] # noqa: E711
                )
            )
            or 0
        )
        comments = (
            self.db.execute(
                select(Comment)
                .where(
                    Comment.activity_id == activity_id,  # type: ignore[arg-type]
                    Comment.parent_id == None,  # type: ignore[arg-type] # noqa: E711
                )
                .order_by(Comment.created_at.desc())  # type: ignore[attr-defined]
                .offset(offset)
                .limit(PAGE_SIZE)
            )
            .scalars()
            .all()
        )
        return {
            "results": list(comments),
            "total": total,
            "page": page,
            "total_pages": max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        }
