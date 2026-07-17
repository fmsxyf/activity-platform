"""活动模块测试"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.activity_service import ActivityService
from services.auth_service import AuthService


def _make_data(**overrides: object) -> dict[str, object]:
    now = datetime.now()
    return {
        "title": "测试活动",
        "description": "测试描述",
        "category": "运动",
        "start_time": now + timedelta(days=1),
        "end_time": now + timedelta(days=1, hours=2),
        "location": "测试地点",
        "max_participants": 10,
        "fee": 0,
        "tags": ["户外"],
        "status": "published",
        **overrides,
    }


class TestActivityServiceUnit:
    """ActivityService 单元测试"""

    def test_create_activity(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Organizer")
        svc = ActivityService(db)
        data = _make_data()
        act = svc.create(user.id, data)
        assert act.id is not None
        assert act.title == "测试活动"
        assert act.status == "published"
        assert len(act.tags) == 1
        assert act.tags[0].tag_name == "户外"

    def test_create_draft(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Org")
        svc = ActivityService(db)
        data = _make_data(status="draft")
        act = svc.create(user.id, data)
        assert act.status == "draft"

    def test_publish_draft(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Org")
        svc = ActivityService(db)
        act = svc.create(user.id, _make_data(status="draft"))
        published = svc.publish(act.id, user.id)
        assert published.status == "published"

    def test_cancel_activity(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Org")
        svc = ActivityService(db)
        act = svc.create(user.id, _make_data())
        cancelled = svc.cancel(act.id, user.id)
        assert cancelled.status == "cancelled"

    def test_cancel_wrong_user(self, db: Session):
        auth = AuthService(db)
        u1 = auth.register("u1@test.com", "password123", "U1")
        u2 = auth.register("u2@test.com", "password123", "U2")
        svc = ActivityService(db)
        act = svc.create(u1.id, _make_data())
        with pytest.raises(ValueError, match="无权"):
            svc.cancel(act.id, u2.id)

    def test_get_by_id(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Org")
        svc = ActivityService(db)
        act = svc.create(user.id, _make_data())
        found = svc.get_by_id(act.id)
        assert found is not None
        assert found.title == "测试活动"

    def test_search_by_keyword(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Org")
        svc = ActivityService(db)
        svc.create(user.id, _make_data(title="登山活动"))
        svc.create(user.id, _make_data(title="读书会"))
        result = svc.search(keyword="登山")
        assert result["total"] == 1

    def test_search_by_category(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Org")
        svc = ActivityService(db)
        svc.create(user.id, _make_data(category="运动"))
        svc.create(user.id, _make_data(category="读书"))
        result = svc.search(category="运动")
        assert result["total"] == 1

    def test_update_statuses(self, db: Session):
        auth = AuthService(db)
        user = auth.register("org@test.com", "password123", "Org")
        svc = ActivityService(db)
        now = datetime.utcnow()
        svc.create(
            user.id,
            _make_data(
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=1),
            ),
        )
        svc.create(
            user.id,
            _make_data(
                status="ongoing",
                start_time=now - timedelta(hours=2),
                end_time=now - timedelta(hours=1),
            ),
        )
        result = svc.update_statuses()
        assert result["published_to_ongoing"] >= 1
        assert result["ongoing_to_ended"] >= 1


class TestActivityIntegration:
    """活动模块集成测试"""

    def _reg(self, client: TestClient):
        client.post(
            "/auth/register",
            data={"email": "act@test.com", "password": "test1234", "nickname": "Test"},
        )

    def test_create_page_requires_auth(self, client: TestClient):
        resp = client.get("/activities/create", follow_redirects=False)
        assert resp.status_code == 302

    def test_create_page_authenticated(self, client: TestClient):
        self._reg(client)
        resp = client.get("/activities/create")
        assert resp.status_code == 200

    def test_index_page(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
