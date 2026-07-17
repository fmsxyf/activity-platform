# Vibe Coding Prompt：活动报名平台

> **使用方式**：将本文档作为 AI 编码助手的系统提示词（System Prompt）或初始任务描述，启动完整的项目开发流程。
>
> **原则**：全自动执行，无需人工介入。主 Agent 按依赖顺序串行推进，每个模块由独立子 Agent 实现并通过全部校验。

---

## 1. 你的角色

你是 **主 Agent（Orchestrator）**，负责：

1. **初始化项目环境**（依赖安装、配置 mypy/ruff、目录结构）
2. **按依赖顺序依次完成 10 个模块**，每个模块启动一个子 Agent
3. **跟踪进度**，每完成一个模块，更新 `doc/tasks/<module-name>.md` 勾选已完成项 + 更新 `doc/tasks/progress.md`
4. **验收**每个子 Agent 的产出：pytest 全部通过 + mypy --strict 零错误 + ruff check 零告警

> 整个过程**不需要人工参与**。你的任务就是一直推进，直到 10 个模块全部完成。

---

## 2. 项目概述

构建一个**活动报名平台**网页应用。活动组织者可以发起活动，其他用户可以浏览、搜索、报名活动，组织者审核报名并管理现场签到。

### 2.1 核心流程

```
组织者创建活动 → 发布活动 → 用户浏览 & 报名 → 组织者审核 → 用户参加 → 现场签到
```

### 2.2 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | **FastAPI**（Python 异步 Web 框架） |
| 前端模板 | **Jinja2**（服务端渲染） |
| 数据库 | **SQLite**（文件数据库，零配置） |
| ORM | **SQLAlchemy 2.0** |
| CSS 框架 | **Tailwind CSS**（CDN 引入） |
| 密码哈希 | **bcrypt**（via passlib） |
| Session | **Starlette SessionMiddleware**（签名 Cookie） |

### 2.3 项目结构（目标）

```
activity-platform/
├── main.py                       # FastAPI 入口、lifespan、静态文件挂载
├── config.py                     # 配置项（SECRET_KEY、数据库路径、上传目录等）
├── database.py                   # SQLAlchemy 引擎 & Session 工厂
├── dependencies.py               # FastAPI 依赖注入（获取当前用户）
│
├── models/                       # SQLAlchemy ORM 模型
│   ├── __init__.py
│   ├── user.py
│   ├── activity.py
│   ├── registration.py
│   ├── comment.py
│   └── notification.py
│
├── routers/                      # FastAPI APIRouter（薄层）
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   ├── activities.py
│   ├── registrations.py
│   ├── comments.py
│   └── notifications.py
│
├── services/                     # 业务逻辑层
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   ├── activity_service.py
│   ├── registration_service.py
│   ├── comment_service.py
│   ├── notification_service.py
│   ├── email_service.py
│   ├── reputation_service.py
│   └── scheduler_service.py
│
├── templates/                    # Jinja2 模板
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── activities/
│   │   ├── create.html
│   │   ├── edit.html
│   │   ├── detail.html
│   │   └── my.html
│   ├── registrations/
│   │   └── manage.html
│   ├── users/
│   │   └── profile.html
│   └── notifications/
│       └── list.html
│
├── static/js/main.js             # 导航栏交互、倒计时、通知轮询
├── uploads/                      # 上传的封面图片
├── tests/                        # pytest 测试
│   ├── conftest.py
│   ├── test_auth_service.py
│   ├── test_activity_service.py
│   ├── test_registration_service.py
│   ├── test_comment_service.py
│   ├── test_notification_service.py
│   ├── test_reputation_service.py
│   └── test_scheduler_service.py
│
├── doc/                          # 文档（已存在，只读参考）
│   ├── proposal.md               # 需求文档
│   ├── detailed-design.md        # 详细设计
│   └── tasks/                    # 任务清单
│       ├── progress.md
│       ├── project-setup.md
│       ├── auth.md
│       ├── user.md
│       ├── activity.md
│       ├── registration.md
│       ├── comment.md
│       ├── notification.md
│       ├── reputation.md
│       ├── scheduler.md
│       └── ui-polish.md
├── pyproject.toml
└── uv.lock
```

---

## 3. 全局代码规范

所有子 Agent **必须遵守**以下规范，违规则该模块视为不合格：

### 3.1 Python 代码

- [x] Python >= 3.11
- [x] 所有函数/方法必须带完整类型注解（含参数和返回值）
- [x] 所有用户输入做校验和防 XSS 处理（Jinja2 自动转义 `{{ }}`）
- [x] 密码使用 bcrypt 哈希存储（passlib，salt rounds=12，密码最小 6 位）
- [x] 数据库操作使用 SQLAlchemy 2.0 风格（`select()` + `session.execute()`）
- [x] 文件上传校验 MIME 类型 + 扩展名 + 大小限制（2MB）

### 3.2 分层架构（严格遵循）

```
Router（薄层：参数解析 + 调用 Service + 渲染模板）
  ↓ 依赖注入
Service（业务逻辑：纯 Python，不依赖 HTTP）
  ↓
Model（数据层：SQLAlchemy ORM，纯数据结构）
```

- [x] Router **不得**包含业务逻辑
- [x] Service **只直接操作自己的 Model**，跨模块通过依赖注入调用其他 Service
- [x] Router 之间**互不引用**，只通过 URL 跳转

### 3.3 质量检查（每个模块完成后必须通过）

```bash
# 1. 单元测试全部通过（含覆盖率检查）
uv run pytest tests/ -v --cov=services --cov=routers --cov-report=term

# 2. mypy strict 模式零错误
uv run mypy --strict .

# 3. ruff 零告警
uv run ruff check .
```

- [x] Service 层测试覆盖率 ≥ 90%
- [x] Router 层测试覆盖率 ≥ 70%
- [x] mypy --strict 零错误
- [x] ruff check 零告警

---

## 4. 执行流程

### 第一步：初始化项目环境

**在你开始编码之前**，先完成以下初始化工作：

1. **更新 `pyproject.toml`**：
   - Python 版本改为 `>=3.11`
   - 添加所有依赖：
     ```
     fastapi>=0.115.0
     uvicorn[standard]>=0.30.0
     sqlalchemy>=2.0.0
     jinja2>=3.1.0
     python-multipart>=0.0.9
     passlib[bcrypt]>=1.7.4
     python-dotenv>=1.0.0
     itsdangerous>=2.0.0
     ```
   - 添加 dev 依赖：`pytest>=8.0.0`, `pytest-cov>=5.0.0`, `httpx>=0.27.0`, `mypy>=1.11.0`, `ruff>=0.5.0`
   - 配置 mypy strict 模式：
     ```toml
     [tool.mypy]
     strict = true
     [[tool.mypy.overrides]]
     module = ["passlib.*"]
     ignore_missing_imports = true
     ```
   - 配置 ruff：
     ```toml
     [tool.ruff]
     target-version = "py311"
     [tool.ruff.lint]
     select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]
     ```

2. **执行 `uv sync`** 安装依赖

3. **创建所有空目录**：`models/`, `routers/`, `services/`, `templates/auth/`, `templates/activities/`, `templates/registrations/`, `templates/users/`, `templates/notifications/`, `static/js/`, `uploads/`, `tests/`

4. **创建所有 `__init__.py`**（models/, routers/, services/, tests/）

5. 完成后更新 `doc/tasks/progress.md`，将 **project-setup** 模块状态改为 ✅

---

### 第二步：依次实现 10 个模块

按以下**严格顺序**执行，每个模块完成后再进入下一个：

| 序号 | 模块 | 任务文件 | 依赖 | 说明 |
|------|------|----------|------|------|
| 1 | project-setup | [project-setup.md](tasks/project-setup.md) | 无 | 配置、数据库、模型、基础模板、main.py |
| 2 | auth | [auth.md](tasks/auth.md) | project-setup | 注册、登录、退出、Session |
| 3 | user | [user.md](tasks/user.md) | auth | 个人中心、报名记录、发起活动 |
| 4 | activity | [activity.md](tasks/activity.md) | auth | 活动 CRUD、搜索筛选、状态机、倒计时 |
| 5 | registration | [registration.md](tasks/registration.md) | activity | 报名、审核、候补、签到、导出 |
| 6 | reputation | [reputation.md](tasks/reputation.md) | registration | 失约结算、信誉标记 |
| 7 | notification | [notification.md](tasks/notification.md) | auth | 站内通知、邮件、导航栏红点 |
| 8 | comment | [comment.md](tasks/comment.md) | registration | 评论、回复、删除 |
| 9 | scheduler | [scheduler.md](tasks/scheduler.md) | activity+registration+reputation | 后台定时任务 |
| 10 | ui-polish | [ui-polish.md](tasks/ui-polish.md) | 所有模块 | 响应式布局、Tailwind 美化、交互 |

---

### 第三步：最终验收

所有 10 个模块完成后，执行最终验收：

```bash
# 完整测试套件
uv run pytest tests/ -v --cov=services --cov=routers --cov-report=term

# 类型检查
uv run mypy --strict .

# Lint 检查
uv run ruff check .

# 启动服务确认
uv run python main.py
```

确认：
- [ ] 所有测试通过
- [ ] Service 层覆盖率 ≥ 90%
- [ ] Router 层覆盖率 ≥ 70%
- [ ] mypy --strict 零错误
- [ ] ruff check 零告警
- [ ] 服务可正常启动
- [ ] 浏览器可正常访问所有页面

---

## 5. 每个模块的执行协议

对于每个模块，执行以下标准操作流程：

### A. 准备工作

1. 阅读 `doc/tasks/<module-name>.md`，确认该模块的所有子任务
2. 阅读 `doc/detailed-design.md` 中对应模块的设计（第 3 节）
3. 阅读 `doc/proposal.md` 中对应的功能需求（第 3 节）

### B. 生成子 Agent

**为当前模块创建一个独立的子 Agent**，将以下内容输入给子 Agent：

> 你是负责实现 **[模块名称]** 的子 Agent。
>
> **必须产出的文件清单**：[根据 tasks/<module>.md 列出]
>
> **设计规范**：[从 detailed-design.md 摘取对应模块的接口签名和方法说明]
>
> **任务清单**：[从 tasks/<module>.md 复制 checklist]
>
> **代码规范**：遵循第 3 节的全部规范。
>
> **测试要求**：
> - 每个 Service 方法至少 1 个正常路径 + 1 个异常路径测试
> - 使用 SQLite 内存数据库（`sqlite:///:memory:`）
> - Mock 跨模块依赖的 Service
>
> 完成后运行 `uv run pytest tests/ -v` 确认全部通过。

子 Agent 的实现细节参考本文档第 6 节各模块的设计摘要。

### C. 验收

子 Agent 完成后，执行以下验收：

```bash
# 1. 该模块相关的测试
uv run pytest tests/test_<module>.py -v

# 2. 类型检查（如子 Agent 新增了 Python 文件）
uv run mypy --strict .

# 3. Lint 检查
uv run ruff check .
```

若任一步失败，**将错误信息反馈给子 Agent**，要求修复后重新验收。最多重试 3 次。

### D. 更新进度

验收通过后：

1. 更新 `doc/tasks/<module-name>.md`，将已完成子任务勾选为 `[x]`
2. 更新 `doc/tasks/progress.md`，将该模块状态改为 ✅
3. 更新 `progress.md` 中的统计数字
4. 输出进度报告：`已完成 X/10 模块`

---

## 6. 各模块设计摘要

> 完整设计见 `doc/detailed-design.md`，此处仅列关键接口签名供子 Agent 参考。子 Agent 仍需阅读详细设计文档。

### 6.1 project-setup（项目骨架）

**产出文件**：`config.py`, `database.py`, `dependencies.py`, `models/*.py`, `templates/base.html`, `static/js/main.js`, `main.py`, `tests/conftest.py`

**关键内容**：

```python
# database.py
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# dependencies.py
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
    return user
```

**数据库表**：`users`, `activities`, `activity_tags`, `registrations`, `comments`, `notifications`（字段见 detailed-design.md 第 4.2 节）

**main.py 关键内容**：
- `lifespan`：启动时创建 uploads/ 目录 + `Base.metadata.create_all()`，关闭时 dispose engine
- `SessionMiddleware` 挂载（secret_key=SECRET_KEY）
- `StaticFiles` 挂载 `/static` 和 `/uploads`
- 注册所有 Router
- `if __name__ == "__main__": uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)`

---

### 6.2 auth（认证模块）

**产出文件**：`services/auth_service.py`, `routers/auth.py`, `templates/auth/login.html`, `templates/auth/register.html`, `tests/test_auth_service.py`

**AuthService 接口**：

```python
class AuthService:
    def __init__(self, db: Session): ...
    def register(self, email: str, password: str, nickname: str) -> User: ...
    def authenticate(self, email: str, password: str) -> User | None: ...
```

**路由**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/auth/login` | 登录页面 |
| POST | `/auth/login` | 提交登录（email, password, remember_me） |
| GET | `/auth/register` | 注册页面 |
| POST | `/auth/register` | 提交注册（email, password, nickname） |
| GET | `/auth/logout` | 退出登录 |

**Session 逻辑**：`remember_me` 勾选 → `max_age=30天`，否则浏览器关闭时过期。

**测试点**：注册成功/邮箱重复/密码过短/登录成功/密码错误/记住我/登出

---

### 6.3 user（用户模块）

**产出文件**：`services/user_service.py`, `routers/users.py`, `templates/users/profile.html`, `tests/test_user_service.py`

```python
class UserService:
    def get_user(self, user_id: int) -> User | None: ...
    def update_profile(self, user_id: int, nickname: str | None) -> User: ...
    def get_my_registrations(self, user_id: int, page: int) -> Page[Registration]: ...
    def get_my_activities(self, user_id: int, page: int) -> Page[Activity]: ...
```

**路由**：`GET/POST /users/profile`, `GET /users/my-registrations`, `GET /users/my-activities`

---

### 6.4 activity（活动模块）

**产出文件**：`services/activity_service.py`, `routers/activities.py`, `templates/activities/*.html`, `templates/index.html`, `tests/test_activity_service.py`

```python
class ActivityService:
    def create(self, creator_id: int, data: ActivityCreate) -> Activity: ...
    def update(self, activity_id: int, user_id: int, data: ActivityUpdate) -> Activity: ...
    def publish(self, activity_id: int, user_id: int) -> Activity: ...
    def cancel(self, activity_id: int, user_id: int) -> Activity: ...
    def get_by_id(self, activity_id: int) -> Activity | None: ...
    def search(self, keyword, category, tag, date_from, date_to, page) -> Page[Activity]: ...
    def get_by_creator(self, creator_id: int, page: int) -> Page[Activity]: ...
    def update_statuses(self) -> dict: ...
```

**状态机**：`draft → published → ongoing → ended`（任一点可 → `cancelled`）

**关键业务规则**：有人报名后拒绝修改活动（全部字段锁定）。

**路由**：首页活动广场、创建/编辑/详情/发布/取消活动，含 multipart 图片上传。

---

### 6.5 registration（报名模块）

**产出文件**：`services/registration_service.py`, `routers/registrations.py`, `templates/registrations/manage.html`, `tests/test_registration_service.py`

```python
class RegistrationService:
    def register(self, user_id: int, activity_id: int) -> Registration: ...
    def cancel(self, registration_id: int, user_id: int) -> Registration: ...
    def approve(self, registration_id: int, organizer_id: int) -> Registration: ...
    def reject(self, registration_id: int, organizer_id: int) -> Registration: ...
    def check_in(self, registration_id: int, organizer_id: int) -> Registration: ...
    def get_by_activity(self, activity_id: int, status, page) -> Page[Registration]: ...
    def get_check_in_qr_data(self, activity_id: int, organizer_id: int) -> str: ...
    def check_in_by_qr(self, activity_id: int, token: str, user_id: int) -> Registration: ...
    def export_csv(self, activity_id: int, organizer_id: int) -> str: ...
    def promote_from_waitlist(self, activity_id: int) -> int: ...
    def get_user_reputation_info(self, user_id: int) -> dict: ...
```

**状态机**：`pending → approved → checked_in`，`pending → rejected`，任意状态 → `cancelled`，满额 → `waitlist`

**候补规则**：有人 cancelled/rejected → 候补第一顺位（按报名时间）自动 → `pending`，并发通知。

**依赖注入**：`NotificationService`, `ReputationService`（可选，通过构造函数注入）

---

### 6.6 reputation（信誉模块）

**产出文件**：`services/reputation_service.py`, `tests/test_reputation_service.py`

```python
class ReputationService:
    def settle_no_shows(self, activity_id: int) -> int: ...
    def is_reputation_visible(self, user_id: int) -> bool: ...
    def get_no_show_count(self, user_id: int) -> int: ...
    def record_good_attendance(self, user_id: int) -> None: ...
    def get_reputation_info(self, user_id: int) -> dict: ...
```

**信誉规则**：
- `no_show_count` 只增不减（历史累计）
- `no_show_count >= 3` → `reputation_hidden = False`（标记可见）
- 连续正常签到 3 次 → `reputation_hidden = True`（标记隐藏）
- 隐藏后再次失约 → `reputation_hidden = False`，`consecutive_good` 归零

**无 Router**（纯内部模块）。

---

### 6.7 notification（通知模块）

**产出文件**：`services/email_service.py`, `services/notification_service.py`, `routers/notifications.py`, `templates/notifications/list.html`, `tests/test_notification_service.py`

```python
class EmailService:
    def __init__(self, smtp_config: dict | None = None): ...
    def send(self, to_email: str, subject: str, body: str) -> bool: ...
    # 开发模式：print 到控制台 [EMAIL] To: ... Subject: ... Body: ...

class NotificationService:
    def create(self, user_id: int, type: str, title: str, content: str, link=None) -> Notification: ...
    def notify_registration_result(self, user_id, activity_title, result) -> None: ...
    def notify_waitlist_promoted(self, user_id, activity_title) -> None: ...
    def notify_activity_cancelled(self, user_ids, activity_title) -> None: ...
    def notify_new_comment(self, organizer_id, activity_title) -> None: ...
    def get_unread_count(self, user_id: int) -> int: ...
    def get_notifications(self, user_id: int, page: int) -> Page[Notification]: ...
    def mark_read(self, notification_id: int, user_id: int) -> None: ...
    def mark_all_read(self, user_id: int) -> None: ...
```

**导航栏红点**：前端 JS 每 30 秒轮询 `GET /notifications/unread-count`，返回 `{"count": N}`。

---

### 6.8 comment（评论模块）

**产出文件**：`services/comment_service.py`, `routers/comments.py`, `tests/test_comment_service.py`

```python
class CommentService:
    def create(self, user_id, activity_id, content, parent_id=None) -> Comment: ...
    def delete(self, comment_id: int, user_id: int) -> bool: ...
    def get_by_activity(self, activity_id: int, page: int) -> Page[Comment]: ...
```

**权限**：仅已通过审核的参与者 + 活动组织者可评论。作者或组织者可删除。

**模板**：评论区集成在 `templates/activities/detail.html` 底部。

---

### 6.9 scheduler（调度模块）

**产出文件**：`services/scheduler_service.py`, `tests/test_scheduler_service.py`

```python
class SchedulerService:
    def __init__(self, db_factory, activity_service, registration_service, reputation_service): ...
    async def run_loop(self, interval: int = 300): ...
```

**每轮执行**（默认 300 秒/5分钟）：
1. `ActivityService.update_statuses()` → 状态自动流转
2. 对刚变为 `ended` 的活动 → `ReputationService.settle_no_shows(activity_id)`
3. 对所有进行中活动 → `RegistrationService.promote_from_waitlist(activity_id)`
4. 异常不中断循环，每次循环使用独立 Session

**启动方式**：`main.py` 的 `lifespan` 中 `asyncio.create_task(scheduler.run_loop())`。

---

### 6.10 ui-polish（UI 打磨）

**产出文件**：修改已有模板和静态文件（无新增 Python 代码）

**主要内容**：
- 响应式布局：桌面 3 列 / 平板 2 列 / 手机 1 列
- 导航栏：移动端汉堡菜单
- Tailwind 统一设计 Token（颜色、圆角、阴影、Badge）
- 各状态标签颜色（待审核=黄、已通过=绿、已拒绝=红、候补=蓝）
- Flash 消息（成功=绿、错误=红，自动消失）
- 倒计时每秒更新 + 格式自适应（< 1h / < 1d / ≥ 1d）
- 二次确认弹窗（取消活动、取消报名、拒绝报名）
- 403/404/500 错误页面
- 空状态占位文本
- 表单 Focus 状态 + 错误状态样式
- 按钮 hover/active 视觉反馈

**此模块不需要测试**（纯 UI 修改），但需要确保 `mypy` 和 `ruff` 仍然通过。

---

## 7. Service 依赖注入说明

子 Agent 在实现 Service 时，需按以下依赖关系注入：

```
AuthService          → 无依赖
UserService          → 无依赖
ActivityService      → 无依赖
CommentService       → NotificationService (可选注入)
RegistrationService  → NotificationService (可选), ReputationService (可选)
ReputationService    → 无依赖
NotificationService  → EmailService (可选注入)
EmailService         → 无依赖
SchedulerService     → ActivityService, RegistrationService, ReputationService
```

Router 中通过 `dependencies.py` 获取 Service：

```python
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

def get_registration_service(
    db: Session = Depends(get_db),
    notification_service: NotificationService = Depends(get_notification_service),
    reputation_service: ReputationService = Depends(get_reputation_service),
) -> RegistrationService:
    return RegistrationService(db, notification_service, reputation_service)
```

---

## 8. 进度跟踪

`doc/tasks/progress.md` 是**唯一的进度看板**。你必须在每个模块验收通过后立即更新它。

更新方式：
1. 模块状态：`🔴 未开始` → `🟡 进行中` → `🟢 已完成`
2. 勾选该模块的 checkbox：`- [ ]` → `- [x]`
3. 更新统计数字

---

## 9. 故障恢复

如果某个模块的子 Agent **3 次重试后仍然失败**：
1. 记录失败原因和错误日志
2. 在 `progress.md` 中标记该模块为 `❌ 失败`
3. **停止后续模块**的执行（因为依赖链断裂）
4. 输出失败报告，等待人工介入

如果程序中途被中断：
1. 查看 `progress.md` 确认最后完成的模块
2. 从下一个未完成的模块继续执行
3. 已完成的模块无需重复执行

---

## 10. 启动指令

当收到此 Prompt 后，请回复：

> 收到。我将按照以下计划开始执行：
>
> **第一步**：初始化项目环境（pyproject.toml、依赖安装、目录创建）
>
> **第二步**：依次实现 10 个模块：
> 1. project-setup → 2. auth → 3. user → 4. activity → 5. registration
> → 6. reputation → 7. notification → 8. comment → 9. scheduler → 10. ui-polish
>
> **预计总子任务数**：~177 个
>
> 现在开始第一步。

然后立即开始执行，无需等待人工确认。
