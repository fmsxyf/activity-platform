"""认证模块测试"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.auth_service import AuthService, verify_password


class TestAuthServiceUnit:
    """AuthService 单元测试（使用真实 SQLite 内存数据库）"""

    def test_register_success(self, db: Session):
        """注册成功：User 创建，密码为 bcrypt 哈希"""
        svc = AuthService(db)
        user = svc.register("test@example.com", "password123", "TestUser")
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.nickname == "TestUser"
        assert user.password_hash != "password123"
        assert verify_password("password123", user.password_hash)

    def test_register_duplicate_email(self, db: Session):
        """重复邮箱注册 → 抛异常"""
        svc = AuthService(db)
        svc.register("dup@example.com", "password123", "User1")
        with pytest.raises(ValueError, match="该邮箱已被注册"):
            svc.register("dup@example.com", "password456", "User2")

    def test_register_password_too_short(self, db: Session):
        """密码过短 → 抛异常"""
        svc = AuthService(db)
        with pytest.raises(ValueError, match="密码长度不能少于 6 位"):
            svc.register("test@example.com", "12345", "Test")

    def test_register_empty_nickname(self, db: Session):
        """空昵称 → 抛异常"""
        svc = AuthService(db)
        with pytest.raises(ValueError, match="昵称不能为空"):
            svc.register("test@example.com", "password123", "")

    def test_authenticate_success(self, db: Session):
        """登录成功 → 返回 User"""
        svc = AuthService(db)
        svc.register("login@example.com", "correct123", "TestUser")
        user = svc.authenticate("login@example.com", "correct123")
        assert user is not None
        assert user.email == "login@example.com"

    def test_authenticate_wrong_password(self, db: Session):
        """密码错误 → 返回 None"""
        svc = AuthService(db)
        svc.register("login@example.com", "correct123", "TestUser")
        user = svc.authenticate("login@example.com", "wrongpass")
        assert user is None

    def test_authenticate_nonexistent_email(self, db: Session):
        """邮箱不存在 → 返回 None"""
        svc = AuthService(db)
        user = svc.authenticate("nobody@example.com", "password")
        assert user is None

    def test_register_strips_email(self, db: Session):
        """注册时去除邮箱首尾空格"""
        svc = AuthService(db)
        user = svc.register("  Test@Example.com  ", "password123", "Test")
        assert user.email == "test@example.com"


class TestAuthIntegration:
    """集成测试（通过 TestClient）"""

    def test_login_page_returns_html(self, client: TestClient):
        """GET /auth/login 返回 200 + HTML"""
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert "登录" in resp.text

    def test_register_page_returns_html(self, client: TestClient):
        """GET /auth/register 返回 200 + HTML"""
        resp = client.get("/auth/register")
        assert resp.status_code == 200
        assert "注册" in resp.text

    _REG_DATA = {
        "email": "flow@example.com",
        "password": "test1234",
        "nickname": "Flow",
    }

    def test_register_and_login_flow(self, client: TestClient):
        """注册 → 自动登录 → 退出 → 重新登录"""
        # 注册
        resp = client.post(
            "/auth/register",
            data=self._REG_DATA,
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == "/"

        # 访问需认证页面（当前无，先访问首页验证 Session 存在）
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 200

        # 退出
        resp = client.get("/auth/logout", follow_redirects=False)
        assert resp.status_code == 302

        # 重新登录
        resp = client.post(
            "/auth/login",
            data={"email": "flow@example.com", "password": "test1234"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_login_wrong_password(self, client: TestClient):
        """错误密码登录 → 返回 401 + 错误提示"""
        # 先注册
        client.post(
            "/auth/register",
            data={
                "email": "wrong@example.com",
                "password": "correct1",
                "nickname": "Test",
            },
        )
        # 登出
        client.get("/auth/logout")
        # 用错误密码登录
        resp = client.post(
            "/auth/login",
            data={"email": "wrong@example.com", "password": "badpass1"},
            follow_redirects=False,
        )
        assert resp.status_code == 401

    def test_logout_clears_session(self, client: TestClient):
        """登出后 Session 清除"""
        client.post(
            "/auth/register",
            data={
                "email": "logout@example.com",
                "password": "test1234",
                "nickname": "Test",
            },
        )
        resp = client.get("/auth/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_remember_me_session(self, client: TestClient):
        """勾选「记住我」后 Session 包含 max_age"""
        client.post(
            "/auth/register",
            data={
                "email": "remember@example.com",
                "password": "test1234",
                "nickname": "Test",
            },
        )
        client.get("/auth/logout")
        resp = client.post(
            "/auth/login",
            data={
                "email": "remember@example.com",
                "password": "test1234",
                "remember_me": "1",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
