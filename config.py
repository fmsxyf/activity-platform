"""应用配置模块"""

import os
import secrets
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 安全密钥（从环境变量读取，默认随机生成，生产环境务必设置环境变量）
SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))

# 数据库
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'activity.db'}")

# 上传目录
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))

# Session 配置（单位：秒）
SESSION_MAX_AGE: int = 0  # 0 表示浏览器关闭时过期
REMEMBER_ME_MAX_AGE: int = 30 * 24 * 60 * 60  # 30 天

# 密码哈希
BCRYPT_ROUNDS: int = 12
