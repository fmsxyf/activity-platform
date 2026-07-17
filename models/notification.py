"""通知模型"""

from datetime import datetime

from sqlalchemy import (  # noqa: E501
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)  # type: ignore[assignment]
    type: str = Column(String(30), nullable=False)  # type: ignore[assignment]
    title: str = Column(String(100), nullable=False)  # type: ignore[assignment]
    content: str = Column(Text, nullable=False)  # type: ignore[assignment]
    link: str | None = Column(String(255), default=None)  # type: ignore[assignment]
    is_read: bool = Column(Boolean, default=False, nullable=False)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)  # type: ignore[assignment]

    # 关系
    user = relationship("User", backref="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}')>"
        )
