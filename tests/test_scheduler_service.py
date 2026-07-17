"""调度模块测试"""

from sqlalchemy.orm import Session

from services.activity_service import ActivityService
from services.registration_service import RegistrationService
from services.reputation_service import ReputationService
from services.scheduler_service import SchedulerService


class TestSchedulerService:
    def test_scheduler_init(self, db: Session):
        """验证调度器可以初始化"""
        svc = SchedulerService(
            db_factory=lambda: db,
            activity_service_class=ActivityService,
            registration_service_class=RegistrationService,
            reputation_service_class=ReputationService,
        )
        assert svc is not None
