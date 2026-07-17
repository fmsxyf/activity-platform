"""认证 Service"""

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import BCRYPT_ROUNDS
from models.user import User


def hash_password(password: str) -> str:
    """bcrypt 哈希密码"""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class AuthService:
    """认证服务：注册、登录、密码管理"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, email: str, password: str, nickname: str) -> User:
        """注册新用户。密码 bcrypt 哈希后存储。邮箱唯一性校验。"""
        # 校验密码长度
        if len(password) < 6:
            raise ValueError("密码长度不能少于 6 位")

        # 校验昵称
        if not nickname or not nickname.strip():
            raise ValueError("昵称不能为空")

        # 检查邮箱唯一性
        existing = self.db.execute(
            select(User).where(User.email == email.strip().lower())  # type: ignore[arg-type]
        ).scalar_one_or_none()
        if existing:
            raise ValueError("该邮箱已被注册")

        # 创建用户
        user = User(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            nickname=nickname.strip(),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        """验证邮箱密码，成功返回 User，失败返回 None"""
        user = self.db.execute(
            select(User).where(User.email == email.strip().lower())  # type: ignore[arg-type]
        ).scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def change_password(self, user_id: int, old_pw: str, new_pw: str) -> bool:
        """修改密码"""
        if len(new_pw) < 6:
            raise ValueError("新密码长度不能少于 6 位")

        user = self.db.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        if not verify_password(old_pw, user.password_hash):
            return False

        user.password_hash = hash_password(new_pw)
        self.db.commit()
        return True
