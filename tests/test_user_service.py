"""用户模块测试"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.auth_service import AuthService
from services.user_service import UserService


class TestUserServiceUnit:
    """UserService 单元测试"""

    def test_get_user(self, db: Session):
        svc = UserService(db)
        auth = AuthService(db)
        created = auth.register("test@example.com", "password123", "Test")
        user = svc.get_user(created.id)
        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_not_found(self, db: Session):
        svc = UserService(db)
        user = svc.get_user(999)
        assert user is None

    def test_update_profile(self, db: Session):
        svc = UserService(db)
        auth = AuthService(db)
        created = auth.register("test@example.com", "password123", "OldName")
        updated = svc.update_profile(created.id, "NewName")
        assert updated.nickname == "NewName"

    def test_update_profile_whitespace_only(self, db: Session):
        svc = UserService(db)
        auth = AuthService(db)
        created = auth.register("test@example.com", "password123", "OldName")
        updated = svc.update_profile(created.id, "   ")
        assert updated.nickname == "OldName"  # unchanged

    def test_update_profile_none(self, db: Session):
        svc = UserService(db)
        auth = AuthService(db)
        created = auth.register("test@example.com", "password123", "OldName")
        updated = svc.update_profile(created.id, None)
        assert updated.nickname == "OldName"  # unchanged

    def test_get_my_registrations_empty(self, db: Session):
        svc = UserService(db)
        auth = AuthService(db)
        created = auth.register("test@example.com", "password123", "Test")
        result = svc.get_my_registrations(created.id)
        assert result["total"] == 0
        assert result["results"] == []

    def test_get_my_activities_empty(self, db: Session):
        svc = UserService(db)
        auth = AuthService(db)
        created = auth.register("test@example.com", "password123", "Test")
        result = svc.get_my_activities(created.id)
        assert result["total"] == 0
        assert result["results"] == []


class TestUserIntegration:
    """用户模块集成测试"""

    def _register_and_login(self, client: TestClient) -> None:
        """辅助方法：注册并登录"""
        client.post(
            "/auth/register",
            data={
                "email": "usertest@example.com",
                "password": "test1234",
                "nickname": "TestUser",
            },
        )

    def test_profile_page_requires_auth(self, client: TestClient):
        """未登录访问 /users/profile 应重定向"""
        resp = client.get("/users/profile", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["location"]

    def test_profile_page_authenticated(self, client: TestClient):
        """已登录访问 /users/profile 返回 200"""
        self._register_and_login(client)
        resp = client.get("/users/profile")
        assert resp.status_code == 200
        assert "TestUser" in resp.text

    def test_my_registrations_page(self, client: TestClient):
        """已登录访问 /users/my-registrations 返回 200"""
        self._register_and_login(client)
        resp = client.get("/users/my-registrations")
        assert resp.status_code == 200

    def test_my_activities_page(self, client: TestClient):
        """已登录访问 /users/my-activities 返回 200"""
        self._register_and_login(client)
        resp = client.get("/users/my-activities")
        assert resp.status_code == 200
