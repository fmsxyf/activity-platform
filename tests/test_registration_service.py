"""报名模块测试"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from services.activity_service import ActivityService
from services.auth_service import AuthService
from services.registration_service import RegistrationService


def _reg_data(**overrides: object) -> dict[str, object]:
    now = datetime.utcnow()
    return {
        "title": "Test",
        "description": "D",
        "category": "运动",
        "start_time": now + timedelta(days=1),
        "end_time": now + timedelta(days=1, hours=2),
        "location": "L",
        "status": "published",
        **overrides,
    }


class TestRegistrationService:
    def test_register_success(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        user = auth.register("user@t.com", "pwd12345", "User")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _reg_data())
        svc = RegistrationService(db)
        reg = svc.register(user.id, act.id)
        assert reg.status in ("pending", "waitlist")

    def test_register_own_activity(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _reg_data())
        svc = RegistrationService(db)
        with __import__("pytest").raises(ValueError, match="自己"):
            svc.register(org.id, act.id)

    def test_approve(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        user = auth.register("user@t.com", "pwd12345", "User")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _reg_data())
        svc = RegistrationService(db)
        reg = svc.register(user.id, act.id)
        approved = svc.approve(reg.id, org.id)
        assert approved.status == "approved"

    def test_reject(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        user = auth.register("user@t.com", "pwd12345", "User")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _reg_data())
        svc = RegistrationService(db)
        reg = svc.register(user.id, act.id)
        rejected = svc.reject(reg.id, org.id)
        assert rejected.status == "rejected"

    def test_cancel(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        user = auth.register("user@t.com", "pwd12345", "User")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _reg_data())
        svc = RegistrationService(db)
        reg = svc.register(user.id, act.id)
        cancelled = svc.cancel(reg.id, user.id)
        assert cancelled.status == "cancelled"

    def test_check_in(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        user = auth.register("user@t.com", "pwd12345", "User")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _reg_data())
        svc = RegistrationService(db)
        reg = svc.register(user.id, act.id)
        svc.approve(reg.id, org.id)
        checked = svc.check_in(reg.id, org.id)
        assert checked.checked_in
