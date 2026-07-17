"""活动模型"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    creator_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)  # type: ignore[assignment]
    title: str = Column(String(100), nullable=False)  # type: ignore[assignment]
    description: str = Column(Text, nullable=False)  # type: ignore[assignment]
    cover_image: str | None = Column(String(255), default=None)  # type: ignore[assignment]
    category: str = Column(String(20), nullable=False)  # type: ignore[assignment]
    start_time: datetime = Column(DateTime, nullable=False)  # type: ignore[assignment]
    end_time: datetime = Column(DateTime, nullable=False)  # type: ignore[assignment]
    location: str = Column(String(255), nullable=False)  # type: ignore[assignment]
    max_participants: int = Column(Integer, nullable=False, default=0)  # type: ignore[assignment]
    fee: int = Column(Integer, nullable=False, default=0)  # type: ignore[assignment]
    registration_deadline: datetime | None = Column(DateTime, default=None)  # type: ignore[assignment]
    status: str = Column(String(20), nullable=False, default="draft")  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)  # type: ignore[assignment]
    updated_at: datetime = Column(  # type: ignore[assignment]
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关系
    creator = relationship("User", backref="activities")
    tags = relationship(  # noqa: E501
        "ActivityTag", back_populates="activity", cascade="all, delete-orphan"
    )
    registrations = relationship(  # noqa: E501
        "Registration", back_populates="activity", cascade="all, delete-orphan"
    )
    comments = relationship(  # noqa: E501
        "Comment", back_populates="activity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, title='{self.title}')>"


class ActivityTag(Base):
    __tablename__ = "activity_tags"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    activity_id: int = Column(Integer, ForeignKey("activities.id"), nullable=False)  # type: ignore[assignment]
    tag_name: str = Column(String(30), nullable=False)  # type: ignore[assignment]

    activity = relationship("Activity", back_populates="tags")

    def __repr__(self) -> str:
        return f"<ActivityTag(tag_name='{self.tag_name}')>"
