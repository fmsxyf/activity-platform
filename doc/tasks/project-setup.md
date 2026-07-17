# 项目骨架 — 最小可执行任务

> 对应里程碑：M1（前半部分）
> 依赖：无
> 完成后验收：项目可启动，数据库表自动创建，基础模板可渲染

---

## 1. 项目配置文件

- [x] **1.1** 创建 `config.py`，包含所有配置项：
  - `SECRET_KEY`（从环境变量读取，默认随机生成）
  - `DATABASE_URL`（默认 `sqlite:///./activity.db`）
  - `UPLOAD_DIR`（默认 `./uploads/`，启动时自动创建目录）
  - `SESSION_MAX_AGE`（默认浏览器关闭时过期）
  - `REMEMBER_ME_MAX_AGE`（30 天）
  - `BCRYPT_ROUNDS`（12）

## 2. 数据库 & ORM

- [x] **2.1** 创建 `database.py`：SQLAlchemy 引擎 + `SessionLocal` 工厂 + `Base` 声明基类 + `get_db()` 生成器
- [x] **2.2** 创建 `models/__init__.py`（导入所有模型，确保 `Base.metadata.create_all` 能发现）
- [x] **2.3** 创建 `models/user.py`：[详见详细设计 4.2 节 `users` 表](#)
- [x] **2.4** 创建 `models/activity.py`：`Activity` + `ActivityTag`
- [x] **2.5** 创建 `models/registration.py`：`Registration`
- [x] **2.6** 创建 `models/comment.py`：`Comment`（含 `parent_id` 自引用）
- [x] **2.7** 创建 `models/notification.py`：`Notification`

## 3. 依赖注入

- [x] **3.1** 创建 `dependencies.py`：
  - `get_current_user(request, db)` → 从 Session 读取 `user_id`，查询 User，未登录则重定向
  - `get_db()` → 已在 database.py，可按需在此 re-export

## 4. 基础模板

- [x] **4.1** 创建 `templates/base.html`：
  - Tailwind CDN 引入
  - 顶部导航栏（Logo、搜索框、通知红点占位、用户菜单占位）
  - `{% block content %}` + `{% block title %}`
  - 页脚
  - 占位 JS block（供倒计时等脚本注入）
- [x] **4.2** 创建 `static/js/main.js`：导航栏交互基础框架

## 5. 应用入口

- [x] **5.1** 创建 `main.py`：
  - FastAPI 实例化
  - `lifespan`：启动时创建 `uploads/` 目录 + 建表，关闭时清理资源
  - `SessionMiddleware` 挂载
  - 静态文件挂载（`/static` → `static/`，`/uploads` → `uploads/`）
  - 注册所有 Router（先预留 import，后续模块逐步取消注释）
  - `uvicorn.run(...)` 入口

## 6. 测试基础设施

- [x] **6.1** 创建 `tests/conftest.py`：
  - `engine` ↔ SQLite 内存数据库
  - `TestingSessionLocal` + `get_test_db()` override
  - `client: TestClient` fixture
  - ~~无需认证的 `auth_client` fixture~~（auth 模块创建后补充）
- [x] **6.2** 创建 `tests/__init__.py`

## 7. 验证

- [x] **7.1** 执行 `uv run python main.py`，确认服务启动无报错
- [x] **7.2** 访问 `http://localhost:8000`，确认返回基础页面（即使空白）
- [x] **7.3** 确认 `activity.db` 和 `uploads/` 自动创建
