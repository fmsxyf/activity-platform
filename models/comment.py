"""评论模型"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)  # type: ignore[assignment]
    activity_id: int = Column(Integer, ForeignKey("activities.id"), nullable=False)  # type: ignore[assignment]
    parent_id: int | None = Column(Integer, ForeignKey("comments.id"), default=None)  # type: ignore[assignment]
    content: str = Column(Text, nullable=False)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)  # type: ignore[assignment]

    # 关系
    user = relationship("User", backref="comments")
    activity = relationship("Activity", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.id", backref="replies")

    def __repr__(self) -> str:
        return (
            f"<Comment(id={self.id}, user_id={self.user_id}, "
            f"activity_id={self.activity_id})>"
        )
