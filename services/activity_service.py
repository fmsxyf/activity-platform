"""活动 Service"""

from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from models.activity import Activity, ActivityTag
from models.registration import Registration

PAGE_SIZE = 12


class ActivityService:
    """活动服务：CRUD、搜索、筛选、状态管理"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, creator_id: int, data: dict[str, Any]) -> Activity:
        """创建活动（草稿或直接发布）"""
        activity = Activity(
            creator_id=creator_id,
            title=data["title"],
            description=data["description"],
            category=data["category"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            location=data["location"],
            max_participants=data.get("max_participants", 0),
            fee=data.get("fee", 0),
            registration_deadline=data.get("registration_deadline"),
            cover_image=data.get("cover_image"),
            status=data.get("status", "published"),
        )
        self.db.add(activity)
        self.db.flush()

        # 处理标签
        tags: list[str] = data.get("tags", [])
        for tag_name in tags[:5]:
            if tag_name.strip():
                self.db.add(
                    ActivityTag(activity_id=activity.id, tag_name=tag_name.strip())
                )

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def update(self, activity_id: int, user_id: int, data: dict[str, Any]) -> Activity:
        """编辑活动。如已有报名者，拒绝修改。"""
        activity = self._get_owned(activity_id, user_id)

        # 检查是否有报名者
        reg_count = (
            self.db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(
                    Registration.activity_id == activity_id,  # type: ignore[arg-type]
                    Registration.status != "cancelled",  # type: ignore[arg-type]
                )
            )
            or 0
        )
        if reg_count > 0:
            raise ValueError("已有用户报名，无法修改活动信息")

        # 更新字段
        for field in (
            "title",
            "description",
            "category",
            "start_time",
            "end_time",
            "location",
            "cover_image",
        ):
            if field in data:
                setattr(activity, field, data[field])
        if "max_participants" in data:
            activity.max_participants = data["max_participants"]
        if "fee" in data:
            activity.fee = data["fee"]
        if "registration_deadline" in data:
            activity.registration_deadline = data["registration_deadline"]

        # 更新标签
        if "tags" in data:
            # 删除旧标签
            for tag in activity.tags:
                self.db.delete(tag)
            # 添加新标签
            for tag_name in data["tags"][:5]:
                if tag_name.strip():
                    self.db.add(
                        ActivityTag(activity_id=activity.id, tag_name=tag_name.strip())
                    )

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def publish(self, activity_id: int, user_id: int) -> Activity:
        """发布草稿"""
        activity = self._get_owned(activity_id, user_id)
        if activity.status != "draft":
            raise ValueError("只有草稿状态的活动可以发布")
        activity.status = "published"
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def cancel(self, activity_id: int, user_id: int) -> Activity:
        """取消活动（仅组织者）"""
        activity = self._get_owned(activity_id, user_id)
        if activity.status == "cancelled":
            raise ValueError("活动已取消")
        if activity.status == "ended":
            raise ValueError("已结束的活动无法取消")
        activity.status = "cancelled"
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def get_by_id(self, activity_id: int) -> Activity | None:
        """获取活动详情（含标签、创建者、报名列表和报名者信息）"""
        from sqlalchemy.orm import joinedload

        activity = (
            self.db.execute(
                select(Activity)
                .options(
                    joinedload(Activity.tags),
                    joinedload(Activity.creator),
                    joinedload(Activity.registrations).joinedload(Registration.user),
                )
                .where(Activity.id == activity_id)  # type: ignore[arg-type]
            )
            .unique()
            .scalar_one_or_none()
        )
        if activity:
            activity._counts = self._get_counts(activity_id)  # type: ignore[attr-defined]
        return activity

    def _get_counts(self, activity_id: int) -> dict[str, int]:
        """获取活动的报名人数统计"""
        pending = (
            self.db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(
                    Registration.activity_id == activity_id,  # type: ignore[arg-type]
                    Registration.status == "pending",  # type: ignore[arg-type]
                )
            )
            or 0
        )
        approved = (
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
        waitlist = (
            self.db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(
                    Registration.activity_id == activity_id,  # type: ignore[arg-type]
                    Registration.status == "waitlist",  # type: ignore[arg-type]
                )
            )
            or 0
        )
        return {"pending": pending, "approved": approved, "waitlist": waitlist}

    def search(
        self,
        keyword: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        """搜索 & 筛选活动"""
        offset = (page - 1) * PAGE_SIZE
        query = select(Activity).options(joinedload(Activity.tags))
        count_query = select(func.count()).select_from(Activity)

        # 默认只显示已发布和进行中的活动
        if status:
            query = query.where(Activity.status == status)  # type: ignore[arg-type]
            count_query = count_query.where(Activity.status == status)  # type: ignore[arg-type]
        else:
            query = query.where(
                Activity.status.in_(["published", "ongoing"])  # type: ignore[attr-defined]
            )
            count_query = count_query.where(
                Activity.status.in_(["published", "ongoing"])  # type: ignore[attr-defined]
            )

        if keyword:
            like_pat = f"%{keyword}%"
            query = query.where(
                or_(
                    Activity.title.ilike(like_pat),  # type: ignore[attr-defined]
                    Activity.description.ilike(like_pat),  # type: ignore[attr-defined]
                )
            )
            count_query = count_query.where(
                or_(
                    Activity.title.ilike(like_pat),  # type: ignore[attr-defined]
                    Activity.description.ilike(like_pat),  # type: ignore[attr-defined]
                )
            )

        if category:
            query = query.where(Activity.category == category)  # type: ignore[arg-type]
            count_query = count_query.where(Activity.category == category)  # type: ignore[arg-type]

        if date_from:
            query = query.where(Activity.start_time >= date_from)  # type: ignore[arg-type]
            count_query = count_query.where(Activity.start_time >= date_from)  # type: ignore[arg-type]

        if date_to:
            query = query.where(Activity.start_time <= date_to)  # type: ignore[arg-type]
            count_query = count_query.where(Activity.start_time <= date_to)  # type: ignore[arg-type]

        # 标签筛选（子查询）
        if tag:
            tag_subquery = (
                select(ActivityTag.activity_id).where(ActivityTag.tag_name == tag)  # type: ignore[call-overload]
            ).subquery()
            query = query.where(Activity.id.in_(tag_subquery))  # type: ignore[attr-defined]
            count_query = count_query.where(Activity.id.in_(tag_subquery))  # type: ignore[attr-defined]

        total = self.db.scalar(count_query) or 0
        activities = (
            self.db.execute(
                query.order_by(Activity.start_time.asc())  # type: ignore[attr-defined]
                .offset(offset)
                .limit(PAGE_SIZE)
            )
            .scalars()
            .unique()
            .all()
        )

        # 为每个活动附加报名人数统计
        for act in activities:
            act._counts = self._get_counts(act.id)  # type: ignore[attr-defined]

        return {
            "results": list(activities),
            "total": total,
            "page": page,
            "total_pages": max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        }

    def get_by_creator(self, creator_id: int, page: int = 1) -> dict[str, Any]:
        """某用户发起的活动列表"""
        offset = (page - 1) * PAGE_SIZE
        total = (
            self.db.scalar(
                select(func.count())
                .select_from(Activity)
                .where(
                    Activity.creator_id == creator_id  # type: ignore[arg-type]
                )
            )
            or 0
        )
        activities = (
            self.db.execute(
                select(Activity)
                .where(Activity.creator_id == creator_id)  # type: ignore[arg-type]
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

    def update_statuses(self) -> dict[str, int]:
        """批量更新活动状态（由 Scheduler 调用）"""
        now = datetime.utcnow()
        result = {"published_to_ongoing": 0, "ongoing_to_ended": 0}

        # published → ongoing（开始时间已到）
        to_ongoing = (
            self.db.execute(
                select(Activity).where(
                    Activity.status == "published",  # type: ignore[arg-type]
                    Activity.start_time <= now,  # type: ignore[arg-type]
                )
            )
            .scalars()
            .all()
        )
        for act in to_ongoing:
            act.status = "ongoing"
            result["published_to_ongoing"] += 1

        # ongoing → ended（结束时间已到）
        to_ended = (
            self.db.execute(
                select(Activity).where(
                    Activity.status == "ongoing",  # type: ignore[arg-type]
                    Activity.end_time <= now,  # type: ignore[arg-type]
                )
            )
            .scalars()
            .all()
        )
        for act in to_ended:
            act.status = "ended"
            result["ongoing_to_ended"] += 1

        if result["published_to_ongoing"] or result["ongoing_to_ended"]:
            self.db.commit()

        return result

    def _get_owned(self, activity_id: int, user_id: int) -> Activity:
        """获取活动并校验所有权"""
        activity = self.get_by_id(activity_id)
        if not activity:
            raise ValueError("活动不存在")
        if activity.creator_id != user_id:
            raise ValueError("无权操作此活动")
        return activity
