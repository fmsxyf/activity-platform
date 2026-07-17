"""评论模块测试"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from services.activity_service import ActivityService
from services.auth_service import AuthService
from services.comment_service import CommentService


def _act_data(**overrides: object) -> dict[str, object]:
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


class TestCommentService:
    def test_comment_by_organizer(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _act_data())
        svc = CommentService(db)
        comment = svc.create(org.id, act.id, "Great activity!")
        assert comment.content == "Great activity!"

    def test_comment_not_allowed(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        user = auth.register("user@t.com", "pwd12345", "User")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _act_data())
        svc = CommentService(db)
        with __import__("pytest").raises(ValueError, match="只有"):
            svc.create(user.id, act.id, "bad comment")

    def test_delete_own_comment(self, db: Session):
        auth = AuthService(db)
        org = auth.register("org@t.com", "pwd12345", "Org")
        act_svc = ActivityService(db)
        act = act_svc.create(org.id, _act_data())
        svc = CommentService(db)
        comment = svc.create(org.id, act.id, "Hello")
        assert svc.delete(comment.id, org.id) is True
