"""用户模型"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from database import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    email: str = Column(String(255), unique=True, nullable=False)  # type: ignore[assignment]
    password_hash: str = Column(String(255), nullable=False)  # type: ignore[assignment]
    nickname: str = Column(String(50), nullable=False)  # type: ignore[assignment]
    avatar: str | None = Column(String(255), default=None)  # type: ignore[assignment]
    no_show_count: int = Column(Integer, default=0, nullable=False)  # type: ignore[assignment]
    reputation_hidden: bool = Column(Boolean, default=True, nullable=False)  # type: ignore[assignment]
    consecutive_good: int = Column(Integer, default=0, nullable=False)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
