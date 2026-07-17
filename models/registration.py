"""报名模型"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class Registration(Base):
    __tablename__ = "registrations"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)  # type: ignore[assignment]
    activity_id: int = Column(Integer, ForeignKey("activities.id"), nullable=False)  # type: ignore[assignment]
    status: str = Column(String(20), nullable=False, default="pending")  # type: ignore[assignment]
    checked_in: bool = Column(Boolean, default=False, nullable=False)  # type: ignore[assignment]
    no_show_recorded: bool = Column(Boolean, default=False, nullable=False)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)  # type: ignore[assignment]

    # 关系
    user = relationship("User", backref="registrations")
    activity = relationship("Activity", back_populates="registrations")

    def __repr__(self) -> str:
        return (
            f"<Registration(id={self.id}, user_id={self.user_id}, "
            f"activity_id={self.activity_id}, status='{self.status}')>"
        )
