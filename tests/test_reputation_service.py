"""信誉模块测试"""

from sqlalchemy.orm import Session

from services.auth_service import AuthService
from services.reputation_service import ReputationService


class TestReputationService:
    def test_get_reputation_info_default(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = ReputationService(db)
        info = svc.get_reputation_info(user.id)
        assert info["no_show_count"] == 0
        assert info["is_visible"] is False

    def test_record_good_attendance(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = ReputationService(db)
        svc.record_good_attendance(user.id)
        info = svc.get_reputation_info(user.id)
        assert info["consecutive_good"] == 1

    def test_no_show_count(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = ReputationService(db)
        assert svc.get_no_show_count(user.id) == 0
