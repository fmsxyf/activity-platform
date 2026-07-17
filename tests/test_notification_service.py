"""通知模块测试"""

from sqlalchemy.orm import Session

from services.auth_service import AuthService
from services.notification_service import NotificationService


class TestNotificationService:
    def test_create_notification(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = NotificationService(db)
        notif = svc.create(user.id, "test", "Title", "Content")
        assert notif.id is not None
        assert notif.title == "Title"

    def test_unread_count(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = NotificationService(db)
        svc.create(user.id, "test", "T", "C")
        svc.create(user.id, "test", "T2", "C2")
        assert svc.get_unread_count(user.id) == 2

    def test_mark_read(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = NotificationService(db)
        notif = svc.create(user.id, "test", "T", "C")
        svc.mark_read(notif.id, user.id)
        assert svc.get_unread_count(user.id) == 0

    def test_mark_all_read(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = NotificationService(db)
        svc.create(user.id, "test", "T1", "C1")
        svc.create(user.id, "test", "T2", "C2")
        svc.mark_all_read(user.id)
        assert svc.get_unread_count(user.id) == 0

    def test_get_notifications(self, db: Session):
        auth = AuthService(db)
        user = auth.register("u@t.com", "pwd12345", "U")
        svc = NotificationService(db)
        svc.create(user.id, "test", "T", "C")
        result = svc.get_notifications(user.id)
        assert result["total"] == 1
