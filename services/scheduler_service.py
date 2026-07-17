"""调度 Service"""

import asyncio
from collections.abc import Callable

from sqlalchemy.orm import Session

from services.activity_service import ActivityService
from services.registration_service import RegistrationService
from services.reputation_service import ReputationService


class SchedulerService:
    """后台定时任务调度"""

    def __init__(
        self,
        db_factory: Callable[[], Session],
        activity_service_class: type[ActivityService],
        registration_service_class: type[RegistrationService],
        reputation_service_class: type[ReputationService],
    ) -> None:
        self.db_factory = db_factory
        self.activity_service_class = activity_service_class
        self.registration_service_class = registration_service_class
        self.reputation_service_class = reputation_service_class

    async def run_loop(self, interval: int = 300) -> None:
        """后台循环（默认5分钟）"""
        while True:
            try:
                db = self.db_factory()
                try:
                    activity_svc = self.activity_service_class(db)
                    rep_svc = self.reputation_service_class(db)
                    reg_svc = self.registration_service_class(db)

                    # 1. 更新活动状态
                    activity_svc.update_statuses()

                    # 2. 对结束的活动结算失约
                    from sqlalchemy import select

                    from models.activity import Activity

                    ended_activities = (
                        db.execute(
                            select(Activity).where(
                                Activity.status == "ended"  # type: ignore[arg-type]
                            )
                        )
                        .scalars()
                        .all()
                    )
                    for act in ended_activities:
                        rep_svc.settle_no_shows(act.id)

                    # 3. 候补递补
                    ongoing = (
                        db.execute(
                            select(Activity).where(
                                Activity.status.in_(["published", "ongoing"])  # type: ignore[attr-defined]
                            )
                        )
                        .scalars()
                        .all()
                    )
                    for act in ongoing:
                        reg_svc.promote_from_waitlist(act.id)

                    db.commit()
                finally:
                    db.close()
            except Exception:
                pass  # 异常不中断循环

            await asyncio.sleep(interval)
