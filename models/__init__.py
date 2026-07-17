"""SQLAlchemy ORM 模型（确保 Base.metadata.create_all 能发现所有模型）"""

from models.activity import Activity, ActivityTag  # noqa: F401
from models.comment import Comment  # noqa: F401
from models.notification import Notification  # noqa: F401
from models.registration import Registration  # noqa: F401
from models.user import User  # noqa: F401
