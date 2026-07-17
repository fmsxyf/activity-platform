# 活动报名平台 — 详细设计文档

> 基于 [proposal.md](proposal.md) 需求文档编写

---

## 1. 项目结构

```
activity-platform/
├── main.py                       # FastAPI 应用入口、生命周期管理、静态文件挂载
├── config.py                     # 配置项（SECRET_KEY、数据库路径、上传目录等）
├── database.py                   # SQLAlchemy 引擎 & Session 工厂
├── dependencies.py               # FastAPI 依赖注入（获取当前用户、获取各 Service）
│
├── models/                       # SQLAlchemy ORM 模型（纯数据结构，不含业务逻辑）
│   ├── __init__.py
│   ├── user.py                   # User
│   ├── activity.py               # Activity, ActivityTag
│   ├── registration.py           # Registration
│   ├── comment.py                # Comment
│   └── notification.py           # Notification
│
├── routers/                      # FastAPI APIRouter（薄层，只做参数解析 & 模板渲染）
│   ├── __init__.py
│   ├── auth.py                   # /auth/*
│   ├── users.py                  # /users/*
│   ├── activities.py             # /activities/*
│   ├── registrations.py          # /activities/{id}/registrations/*
│   ├── comments.py               # /activities/{id}/comments/*
│   └── notifications.py          # /notifications/*
│
├── services/                     # 业务逻辑层（每个模块独立，通过接口交互）
│   ├── __init__.py
│   ├── auth_service.py           # 注册、登录、登出、密码哈希
│   ├── user_service.py           # 个人信息、报名记录、发起的活动
│   ├── activity_service.py       # 活动 CRUD、搜索、筛选、状态流转
│   ├── registration_service.py   # 报名、取消、审核、候补、签到、导出
│   ├── comment_service.py        # 评论、回复、删除
│   ├── notification_service.py   # 站内通知创建 & 查询、邮件发送调用
│   ├── reputation_service.py     # 失约计算、信誉标记判断
│   ├── email_service.py          # 邮件发送（开发阶段打印到控制台）
│   └── scheduler_service.py      # 后台定时任务（状态流转 & 失约结算）
│
├── templates/                    # Jinja2 模板
│   ├── base.html                 # 基础布局（导航栏、页脚、通知红点）
│   ├── index.html                # 首页 / 活动广场
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── activities/
│   │   ├── detail.html           # 活动详情（含评论区 & 报名入口）
│   │   ├── create.html           # 创建活动（含草稿）
│   │   ├── edit.html             # 编辑活动
│   │   └── my.html               # 我发起的活动列表
│   ├── registrations/
│   │   └── manage.html           # 报名管理（审核 / 签到 / 导出）
│   ├── users/
│   │   └── profile.html          # 个人中心
│   └── notifications/
│       └── list.html             # 通知列表
│
├── static/                       # 静态资源（Tailwind CDN 为主，少量自定义 JS）
│   └── js/
│       └── main.js               # 导航栏交互、通知轮询等
│
├── uploads/                      # 上传的封面图片（.gitignore 忽略）
├── tests/                        # 单元测试 & 集成测试
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures（测试数据库、测试客户端）
│   ├── test_auth_service.py
│   ├── test_activity_service.py
│   ├── test_registration_service.py
│   ├── test_comment_service.py
│   ├── test_notification_service.py
│   └── test_reputation_service.py
│
├── doc/                          # 文档
│   ├── proposal.md
│   └── detailed-design.md
├── pyproject.toml
└── uv.lock
```

---

## 2. 架构概览

### 2.1 分层架构

```
┌─────────────────────────────────────────┐
│  Routers（薄层）                          │
│  - 解析 HTTP 请求参数                     │
│  - 调用 Service                           │
│  - 渲染 Jinja2 模板返回 HTML              │
└──────────────┬──────────────────────────┘
               │ 依赖注入（dependencies.py）
┌──────────────▼──────────────────────────┐
│  Services（业务逻辑）                     │
│  - 纯 Python，不依赖 HTTP                 │
│  - 通过构造函数注入其他 Service             │
│  - 只访问自己的 Model                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Models（数据层）                         │
│  - SQLAlchemy ORM 模型                   │
│  - 纯数据结构，无业务逻辑                  │
└─────────────────────────────────────────┘
```

### 2.2 模块独立性原则

- 每个 Service **只直接操作自己的 Model**
- 跨模块操作通过**依赖注入**调用其他 Service 的公开方法
- Router 之间**互不引用**，只通过 URL 跳转
- 每个 Service **可独立进行单元测试**（mock 其依赖的 Service）

### 2.3 Service 依赖图

```
AuthService          → 无依赖
UserService          → 无依赖
ActivityService      → 无依赖
CommentService       → NotificationService (接口)
RegistrationService  → NotificationService (接口), ReputationService (接口)
ReputationService    → 无依赖（只读 Registration & User 模型）
NotificationService  → EmailService (接口)
EmailService         → 无依赖
SchedulerService     → ActivityService, RegistrationService, ReputationService
```

### 2.4 请求生命周期

```
HTTP 请求
  → Router 解析参数
    → dependencies.py 注入当前用户 & Service
      → Service 执行业务逻辑
        → Model 读写数据库
      ← 返回业务结果
    ← Router 渲染 Jinja2 模板
  ← 返回 HTML
```

---

## 3. 模块详细设计

### 3.1 AuthService（认证模块）

**职责**：用户注册、登录、登出、密码管理

**文件**：[services/auth_service.py](services/auth_service.py)

```python
class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, email: str, password: str, nickname: str) -> User:
        """注册新用户。密码 bcrypt 哈希后存储。邮箱唯一性校验。"""

    def authenticate(self, email: str, password: str) -> User | None:
        """验证邮箱密码，成功返回 User，失败返回 None"""

    def change_password(self, user_id: int, old_pw: str, new_pw: str) -> bool:
        """修改密码"""
```

**Router**：[routers/auth.py](routers/auth.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/auth/login` | 登录页面 |
| POST | `/auth/login` | 提交登录（表单：email, password, remember_me） |
| GET | `/auth/register` | 注册页面 |
| POST | `/auth/register` | 提交注册（表单：email, password, nickname） |
| GET | `/auth/logout` | 退出登录，清除 Session |

**测试点**：
- 注册成功 / 邮箱重复 / 密码过短
- 登录成功 / 密码错误 / 邮箱不存在
- "记住我"→ Session 过期时间不同
- 登出后 Session 清除

---

### 3.2 UserService（用户模块）

**职责**：个人信息管理、历史记录查询

**文件**：[services/user_service.py](services/user_service.py)

```python
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> User | None:
        """获取用户信息"""

    def update_profile(self, user_id: int, nickname: str | None) -> User:
        """更新个人信息（不含邮箱和密码）"""

    def get_my_registrations(self, user_id: int, page: int) -> Page[Registration]:
        """我报名的活动列表（分页）"""

    def get_my_activities(self, user_id: int, page: int) -> Page[Activity]:
        """我发起的活动列表（分页）"""
```

**Router**：[routers/users.py](routers/users.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/users/profile` | 个人中心页面 |
| POST | `/users/profile` | 更新个人信息 |
| GET | `/users/my-registrations` | 我的报名记录（分页） |
| GET | `/users/my-activities` | 我发起的活动（分页） |

**测试点**：
- 获取个人信息 / 更新昵称
- 报名记录分页 / 空列表
- 发起的活动列表

---

### 3.3 ActivityService（活动模块）

**职责**：活动的创建、编辑、删除、搜索、筛选

**文件**：[services/activity_service.py](services/activity_service.py)

**活动状态机**：

```
  ┌──────┐   发布    ┌───────────┐  开始时间到  ┌──────────┐  结束时间到  ┌──────┐
  │ draft │ ──────→ │ published │ ──────────→ │ ongoing  │ ──────────→ │ ended │
  └──────┘          └───────────┘              └──────────┘              └──────┘
       │                  │                        │                        │
       └──────────────────┴────────────────────────┴────────────────────────┘
                                    组织者取消 → cancelled
```

```python
class ActivityService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, creator_id: int, data: ActivityCreate) -> Activity:
        """创建活动（草稿或直接发布）"""

    def update(self, activity_id: int, user_id: int, data: ActivityUpdate) -> Activity:
        """编辑活动。如已有报名者，拒绝修改（全部锁定）"""

    def publish(self, activity_id: int, user_id: int) -> Activity:
        """发布草稿"""

    def cancel(self, activity_id: int, user_id: int) -> Activity:
        """取消活动（仅组织者可操作）"""

    def get_by_id(self, activity_id: int) -> Activity | None:
        """获取活动详情（含标签）"""

    def search(self, keyword: str | None, category: str | None,
               tag: str | None, date_from: datetime | None,
               date_to: datetime | None, page: int) -> Page[Activity]:
        """搜索 & 筛选活动，按开始时间倒序"""

    def get_by_creator(self, creator_id: int, page: int) -> Page[Activity]:
        """某用户发起的活动列表"""

    def update_statuses(self) -> dict:
        """批量更新活动状态（由 Scheduler 调用）。
           返回 {published→ongoing: N, ongoing→ended: N}"""
```

**Router**：[routers/activities.py](routers/activities.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页活动广场（搜索、筛选、分页） |
| GET | `/activities/create` | 创建活动页面 |
| POST | `/activities/create` | 提交创建（含 multipart 图片上传） |
| GET | `/activities/{id}` | 活动详情页（含评论 & 报名状态） |
| GET | `/activities/{id}/edit` | 编辑活动页面 |
| POST | `/activities/{id}/edit` | 提交编辑 |
| POST | `/activities/{id}/publish` | 发布草稿 |
| POST | `/activities/{id}/cancel` | 取消活动 |

**测试点**：
- 创建草稿 / 直接发布
- 编辑无报名者的活动 / 编辑有报名者的活动（应拒绝）
- 搜索按关键词 / 分类 / 标签 / 时间范围
- 状态自动流转

---

### 3.4 RegistrationService（报名模块）

**职责**：报名、取消、审核、候补、签到、导出

**文件**：[services/registration_service.py](services/registration_service.py)

**报名状态机**：

```
  用户报名
    │
    ▼
┌──────────┐   组织者通过   ┌──────────┐   组织者签到   ┌──────────┐
│ pending  │ ────────────→ │ approved │ ────────────→ │ checked_in│
│ 待审核    │               │ 已通过    │               │ 已签到    │
└──────────┘               └──────────┘               └──────────┘
    │                          │
    │   组织者拒绝               │ 用户取消 / 组织者取消活动
    ▼                          ▼
┌──────────┐              ┌──────────┐
│ rejected │              │ cancelled│
│ 已拒绝    │              │ 已取消    │
└──────────┘              └──────────┘

满额时报名 → waitlist（候补）
候补递补规则：有人 cancelled/rejected → 候补第 1 位自动 → pending（并发通知）
```

```python
class RegistrationService:
    def __init__(self, db: Session,
                 notification_service: NotificationService | None = None,
                 reputation_service: ReputationService | None = None):
        self.db = db

    def register(self, user_id: int, activity_id: int) -> Registration:
        """报名活动。
           - 活动不可报名时抛异常（已结束/已取消/已过截止时间）
           - 名额未满 → pending
           - 名额已满 → waitlist
           - 返回报名记录"""

    def cancel(self, registration_id: int, user_id: int) -> Registration:
        """取消报名（仅报名者本人）。
           取消后触发候补递补检查"""

    def approve(self, registration_id: int, organizer_id: int) -> Registration:
        """审核通过。通知报名者。"""

    def reject(self, registration_id: int, organizer_id: int) -> Registration:
        """审核拒绝。触发候补递补。通知报名者。"""

    def check_in(self, registration_id: int, organizer_id: int) -> Registration:
        """手动签到。"""

    def get_by_activity(self, activity_id: int, status: str | None,
                        page: int) -> Page[Registration]:
        """按活动查询报名列表，支持按状态筛选（Tab切换）"""

    def get_check_in_qr_data(self, activity_id: int, organizer_id: int) -> str:
        """生成签到二维码数据（含签名令牌的 URL）"""

    def check_in_by_qr(self, activity_id: int, token: str, user_id: int) -> Registration:
        """扫码签到（参与者扫组织者出示的二维码）"""

    def export_csv(self, activity_id: int, organizer_id: int) -> str:
        """导出已通过名单为 CSV 字符串"""

    def promote_from_waitlist(self, activity_id: int) -> int:
        """候补递补：检查名额空缺，将候补第一顺位转为待审核。
           返回递补人数。"""

    def get_user_reputation_info(self, user_id: int) -> dict:
        """获取某用户的信誉信息（供模板展示用）"""
```

**Router**：[routers/registrations.py](routers/registrations.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/activities/{id}/register` | 报名 |
| POST | `/registrations/{id}/cancel` | 取消报名 |
| GET | `/activities/{id}/registrations` | 报名管理页（仅组织者） |
| POST | `/registrations/{id}/approve` | 审核通过 |
| POST | `/registrations/{id}/reject` | 审核拒绝 |
| POST | `/registrations/{id}/check-in` | 手动签到 |
| GET | `/activities/{id}/qr` | 获取签到二维码页面（仅组织者） |
| GET | `/check-in/{token}` | 扫码签到入口（参与者点击后签到） |
| GET | `/activities/{id}/export` | 导出 CSV |

**测试点**：
- 报名成功 / 满额进入候补
- 取消报名 / 候补自动递补
- 审核通过 / 拒绝
- 非组织者审核（应拒绝）
- 签到 / 重复签到
- CSV 导出内容正确
- 二维码签到流程

---

### 3.5 CommentService（评论模块）

**职责**：评论发表、回复、删除

**文件**：[services/comment_service.py](services/comment_service.py)

```python
class CommentService:
    def __init__(self, db: Session,
                 notification_service: NotificationService | None = None):
        self.db = db

    def create(self, user_id: int, activity_id: int, content: str,
               parent_id: int | None = None) -> Comment:
        """发表评论或回复。
           - 仅已通过审核的参与者可评论
           - 组织者始终可评论（自己的活动）
           - 回复时通知被回复者"""

    def delete(self, comment_id: int, user_id: int) -> bool:
        """删除评论（仅作者或活动组织者可删）"""

    def get_by_activity(self, activity_id: int, page: int) -> Page[Comment]:
        """获取活动的评论列表（树形结构，按时间排序）"""
```

**Router**：[routers/comments.py](routers/comments.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/activities/{id}/comments` | 获取评论列表（分页，AJAX 加载） |
| POST | `/activities/{id}/comments` | 发表评论 |
| POST | `/comments/{id}/reply` | 回复评论 |
| DELETE | `/comments/{id}` | 删除评论 |

**测试点**：
- 通过审核的参与者可评论
- 未通过审核者评论（应拒绝）
- 回复评论 / 删除自己的评论
- 非作者删除（应拒绝）

---

### 3.6 NotificationService（通知模块）

**职责**：站内通知创建 & 查询、未读数、邮件发送

**文件**：[services/notification_service.py](services/notification_service.py)

```python
class NotificationService:
    def __init__(self, db: Session,
                 email_service: EmailService | None = None):
        self.db = db

    def create(self, user_id: int, type: str, title: str, content: str) -> Notification:
        """创建站内通知"""

    def notify_registration_result(self, user_id: int, activity_title: str,
                                    result: str) -> None:
        """报名审核结果通知（站内 + 邮件）"""

    def notify_waitlist_promoted(self, user_id: int, activity_title: str) -> None:
        """候补转正通知（站内 + 邮件）"""

    def notify_activity_cancelled(self, user_ids: list[int],
                                   activity_title: str) -> None:
        """活动取消通知（批量站内 + 邮件）"""

    def notify_new_comment(self, organizer_id: int, activity_title: str) -> None:
        """新评论通知（站内）"""

    def get_unread_count(self, user_id: int) -> int:
        """获取未读通知数（导航栏红点用）"""

    def get_notifications(self, user_id: int, page: int) -> Page[Notification]:
        """获取通知列表"""

    def mark_read(self, notification_id: int, user_id: int) -> None:
        """标记已读"""

    def mark_all_read(self, user_id: int) -> None:
        """全部标记已读"""
```

**Router**：[routers/notifications.py](routers/notifications.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/notifications` | 通知列表页 |
| GET | `/notifications/unread-count` | 未读数（JSON，导航栏 AJAX 轮询） |
| POST | `/notifications/{id}/read` | 标记已读 |
| POST | `/notifications/read-all` | 全部已读 |

**测试点**：
- 创建通知 / 获取未读数
- 标记已读
- 邮件发送调用（mock EmailService）
- 通知列表分页

---

### 3.7 EmailService（邮件模块）

**职责**：邮件发送（封装 SMTP 细节）

**文件**：[services/email_service.py](services/email_service.py)

```python
class EmailService:
    def __init__(self, smtp_config: dict | None = None):
        """开发阶段 smtp_config 为 None → 控制台打印"""
        self.config = smtp_config

    def send(self, to_email: str, subject: str, body: str) -> bool:
        """发送邮件。开发模式：print 到控制台。
           生产模式：通过 SMTP 发送。"""
```

**开发阶段输出示例**：
```
[EMAIL] To: user@example.com
        Subject: 报名审核结果 - 周末登山活动
        Body: 恭喜！您的报名已通过审核。
```

**测试点**：
- 开发模式输出到控制台
- SMTP 配置正确时真实发送

---

### 3.8 ReputationService（信誉模块）

**职责**：失约记录计算、信誉标记判断

**文件**：[services/reputation_service.py](services/reputation_service.py)

```python
class ReputationService:
    def __init__(self, db: Session):
        self.db = db

    def settle_no_shows(self, activity_id: int) -> int:
        """结算指定活动的失约：已通过但未签到的记为失约。
           返回本次记为失约的人数。"""

    def is_reputation_visible(self, user_id: int) -> bool:
        """判断是否应展示失约标记（累计失约 ≥ 3 且未被恢复）"""

    def get_no_show_count(self, user_id: int) -> int:
        """获取用户累计失约次数"""

    def record_good_attendance(self, user_id: int) -> None:
        """记录一次正常签到（用于信誉恢复计算）。
           连续 3 次正常签到自动隐藏标记。"""

    def get_reputation_info(self, user_id: int) -> dict:
        """获取信誉信息：{no_show_count, is_visible, consecutive_good}"""
```

**信誉恢复规则**：
- `users.no_show_count` 记录累计失约总数（只增不减，用于统计）
- `users.reputation_hidden` 控制是否展示失约标记
- 当 `no_show_count >= 3` 时，`reputation_hidden = False`（标记可见）
- 用户连续正常签到 3 次后，`reputation_hidden = True`（标记隐藏）
- 如果之后再次失约，`reputation_hidden` 重新变为 `False`
- 连续正常签到次数通过 `registrations` 表实时计算（最近 N 条已签到记录中连续非失约的次数）

**Router**：无（纯内部模块，无对外路由）

**测试点**：
- 失约结算：已通过未签到 → 失约+1
- 失约满 3 次 → 标记可见
- 连续正常签到 3 次 → 标记隐藏
- 标记隐藏后再次失约 → 标记重新可见

---

### 3.9 SchedulerService（调度模块）

**职责**：后台定时任务，处理状态流转 & 失约结算

**文件**：[services/scheduler_service.py](services/scheduler_service.py)

```python
class SchedulerService:
    def __init__(self, db_factory: Callable[[], Session],
                 activity_service: ActivityService,
                 reputation_service: ReputationService):
        pass

    async def run_loop(self, interval: int = 300):
        """后台循环，每 interval 秒执行一次：
           1. 更新活动状态（published→ongoing, ongoing→ended）
           2. 对刚结束的活动，结算失约
           3. 处理候补递补检查
        """
```

**触发时机**：FastAPI `lifespan` 中启动 `asyncio.create_task(run_loop())`

**执行逻辑**（每个周期）：
1. `ActivityService.update_statuses()` → 更新所有活动状态
2. 对刚变为 `ended` 的活动 → `ReputationService.settle_no_shows(activity_id)`
3. 对所有进行中活动 → `RegistrationService.promote_from_waitlist(activity_id)`

---

## 4. 数据库详细设计

### 4.1 ER 图（文字描述）

```
User ──1:N── Activity (creator)
User ──1:N── Registration
User ──1:N── Comment
User ──1:N── Notification
Activity ──1:N── ActivityTag
Activity ──1:N── Registration
Activity ──1:N── Comment
Comment ──0:N── Comment (parent_id, 自引用)
```

### 4.2 表结构

#### users

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱，用于登录 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希 |
| nickname | VARCHAR(50) | NOT NULL | 显示名称 |
| avatar | VARCHAR(255) | DEFAULT NULL | 头像路径（暂不实现上传） |
| no_show_count | INTEGER | DEFAULT 0 | 累计失约次数（只增不减） |
| reputation_hidden | BOOLEAN | DEFAULT TRUE | 失约标记是否隐藏 |
| consecutive_good | INTEGER | DEFAULT 0 | 连续正常签到次数（恢复计算用） |
| created_at | DATETIME | DEFAULT NOW | 注册时间 |

#### activities

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| creator_id | INTEGER | FK → users.id, NOT NULL | 组织者 |
| title | VARCHAR(100) | NOT NULL | 活动标题 |
| description | TEXT | NOT NULL | 活动描述 |
| cover_image | VARCHAR(255) | DEFAULT NULL | 封面图路径 |
| category | VARCHAR(20) | NOT NULL | 分类：运动/读书/聚会/旅行/学习/其他 |
| start_time | DATETIME | NOT NULL | 开始时间 |
| end_time | DATETIME | NOT NULL | 结束时间 |
| location | VARCHAR(255) | NOT NULL | 活动地点 |
| max_participants | INTEGER | NOT NULL, DEFAULT 0 | 人数上限，0=不限 |
| fee | INTEGER | NOT NULL, DEFAULT 0 | 费用（元），0=免费 |
| registration_deadline | DATETIME | DEFAULT NULL | 报名截止，NULL=活动开始时截止 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | draft / published / ongoing / ended / cancelled |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW | 更新时间 |

#### activity_tags

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| activity_id | INTEGER | FK → activities.id, NOT NULL | 所属活动 |
| tag_name | VARCHAR(30) | NOT NULL | 标签名 |
| UNIQUE | (activity_id, tag_name) | | 同一活动不重复标签 |

#### registrations

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| user_id | INTEGER | FK → users.id, NOT NULL | 报名者 |
| activity_id | INTEGER | FK → activities.id, NOT NULL | 活动 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending / approved / rejected / waitlist / cancelled |
| checked_in | BOOLEAN | DEFAULT FALSE | 是否已签到 |
| no_show_recorded | BOOLEAN | DEFAULT FALSE | 是否已记为失约（防止重复结算） |
| created_at | DATETIME | DEFAULT NOW | 报名时间 |
| UNIQUE | (user_id, activity_id) | | 同一用户对同一活动只能报一次 |

#### comments

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| user_id | INTEGER | FK → users.id, NOT NULL | 评论者 |
| activity_id | INTEGER | FK → activities.id, NOT NULL | 活动 |
| parent_id | INTEGER | FK → comments.id, DEFAULT NULL | 父评论（NULL=顶级评论） |
| content | TEXT | NOT NULL | 评论内容 |
| created_at | DATETIME | DEFAULT NOW | 评论时间 |

#### notifications

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 主键 |
| user_id | INTEGER | FK → users.id, NOT NULL | 接收者 |
| type | VARCHAR(30) | NOT NULL | 类型：registration_result / waitlist_promoted / activity_cancelled / new_comment |
| title | VARCHAR(100) | NOT NULL | 通知标题 |
| content | TEXT | NOT NULL | 通知内容 |
| link | VARCHAR(255) | DEFAULT NULL | 点击跳转链接 |
| is_read | BOOLEAN | DEFAULT FALSE | 是否已读 |
| created_at | DATETIME | DEFAULT NOW | 通知时间 |

---

## 5. API 路由汇总

### 5.1 认证相关

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/auth/login` | ❌ | 登录页 |
| POST | `/auth/login` | ❌ | 提交登录 |
| GET | `/auth/register` | ❌ | 注册页 |
| POST | `/auth/register` | ❌ | 提交注册 |
| GET | `/auth/logout` | ✅ | 退出登录 |

### 5.2 用户相关

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/users/profile` | ✅ | 个人中心 |
| POST | `/users/profile` | ✅ | 更新个人信息 |
| GET | `/users/my-registrations` | ✅ | 我的报名 |
| GET | `/users/my-activities` | ✅ | 我发起的活动 |

### 5.3 活动相关

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/` | ❌ | 首页活动广场 |
| GET | `/activities/create` | ✅ | 创建活动页 |
| POST | `/activities/create` | ✅ | 提交创建 |
| GET | `/activities/{id}` | ❌ | 活动详情 |
| GET | `/activities/{id}/edit` | ✅ | 编辑活动页 |
| POST | `/activities/{id}/edit` | ✅ | 提交编辑 |
| POST | `/activities/{id}/publish` | ✅ | 发布草稿 |
| POST | `/activities/{id}/cancel` | ✅ | 取消活动 |

### 5.4 报名相关

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/activities/{id}/register` | ✅ | 报名 |
| POST | `/registrations/{id}/cancel` | ✅ | 取消报名 |
| GET | `/activities/{id}/registrations` | ✅ | 报名管理页 |
| POST | `/registrations/{id}/approve` | ✅ | 审核通过 |
| POST | `/registrations/{id}/reject` | ✅ | 审核拒绝 |
| POST | `/registrations/{id}/check-in` | ✅ | 手动签到 |
| GET | `/activities/{id}/qr` | ✅ | 签到二维码页 |
| GET | `/check-in/{token}` | ✅ | 扫码签到 |
| GET | `/activities/{id}/export` | ✅ | 导出 CSV |

### 5.5 评论相关

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/activities/{id}/comments` | ✅ | 发表评论 |
| POST | `/comments/{id}/reply` | ✅ | 回复评论 |
| DELETE | `/comments/{id}` | ✅ | 删除评论 |

### 5.6 通知相关

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/notifications` | ✅ | 通知列表 |
| GET | `/notifications/unread-count` | ✅ | 未读数（JSON） |
| POST | `/notifications/{id}/read` | ✅ | 标记已读 |
| POST | `/notifications/read-all` | ✅ | 全部已读 |

---

## 6. 认证 & 安全设计

### 6.1 Session 管理

- 使用 Starlette `SessionMiddleware`，基于**签名 Cookie**
- Session 数据仅存 `user_id`（最小化 Cookie 内容）
- 默认过期：浏览器关闭时清除
- "记住我"：Cookie `max_age` 设为 30 天

### 6.2 密码安全

- 使用 `bcrypt` 哈希（passlib 库），salt rounds = 12
- 密码最小长度：6 位
- 前端 + 后端双重校验

### 6.3 权限控制

- 通过 FastAPI `Depends(get_current_user)` 依赖注入
- 需要登录的路由注入 `user_id`，否则重定向到登录页
- 组织者专属操作（审核、签到、导出）在 Service 层校验 `creator_id`

### 6.4 XSS 防护

- Jinja2 默认自动转义 HTML（`{{ }}` 语法）
- 用户输入的富文本内容使用白名单标签过滤
- 文件上传校验 MIME 类型 + 扩展名

---

## 7. 依赖包

```toml
# pyproject.toml 新增依赖
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "jinja2>=3.1.0",          # FastAPI 内置，模板引擎
    "python-multipart>=0.0.9", # 文件上传
    "passlib[bcrypt]>=1.7.4",  # 密码哈希
    "python-dotenv>=1.0.0",    # 环境变量
    "openpyxl>=3.1.0",         # Excel 导出
    "itsdangerous>=2.0.0",     # Session 签名（Starlette 依赖）
]
```

---

## 8. 页面模板设计要点

### 8.1 base.html（基础布局）

所有页面继承此模板，包含：
- `<head>`：Tailwind CDN、页面标题 block、倒计时 JS 逻辑
- 顶部导航栏：Logo、搜索框、通知红点（AJAX 轮询）、用户下拉菜单
- 主内容区 `{% block content %}`
- 页脚

### 8.2 活动倒计时

- 活动卡片和活动详情页展示**实时倒计时**（距活动开始时间）
- 格式：`X 天 X 时 X 分 X 秒`
- 实现方式：
  - 服务端渲染初始值（`start_time` 时间戳写入 `data-start-time` 属性）
  - 前端 JS 每秒更新一次倒计时文本
  - 活动已开始 → 显示"进行中"
  - 活动已结束 → 显示"已结束"

### 8.3 导航栏状态

| 状态 | Logo | 搜索 | 通知 | 用户菜单 |
|------|------|------|------|----------|
| 未登录 | ✅ | ✅ | ❌ | 登录/注册按钮 |
| 已登录 | ✅ | ✅ | ✅ (含红点) | 头像 + 下拉 |

### 8.4 响应式布局

- 桌面端：活动卡片 3 列网格
- 平板端：2 列
- 手机端：1 列，导航栏折叠为汉堡菜单

---

## 9. 错误处理策略

| 场景 | HTTP 状态码 | 处理方式 |
|------|------------|----------|
| 表单校验失败 | 422 | 返回表单页 + 错误提示 |
| 未登录访问需登录页 | 302 | 重定向到登录页，登录后跳回 |
| 无权限操作 | 403 | 显示错误页面 + 提示信息 |
| 资源不存在 | 404 | 显示 404 页面 |
| 业务规则冲突（如重复报名） | 200 | 当前页 flash 消息提示 |
| 服务器错误 | 500 | 通用错误页面 |

---

## 10. 测试策略

### 10.1 单元测试（每个 Service 独立测试）

- 每个 Service 测试使用**独立的 SQLite 内存数据库**
- 依赖的 Service 使用 **Mock 对象**
- 覆盖：正常路径、边界条件、异常情况

### 10.2 集成测试

- 使用 FastAPI `TestClient` + 真实 SQLite 内存数据库
- 测试完整 HTTP 请求 → 响应流程
- 覆盖：登录 → 创建活动 → 报名 → 审核 → 签到 → 失约结算

### 10.3 测试目标覆盖率

- Service 层：≥ 90%
- Router 层：≥ 70%（核心流程）

---

## 11. 开发顺序建议

按里程碑 M1 → M6 顺序，每个阶段完成后可独立验证：

- **M1**：`database.py` → models → `AuthService` → `auth_router` → templates/auth/ → 可注册登录
- **M2**：`ActivityService` → `activity_router` → templates/activities/ → 可创建编辑活动
- **M3**：`RegistrationService`(报名部分) → 报名/取消 → 活动广场 → 可浏览报名
- **M4**：审核 + 候补 + `ReputationService` → 审核流程 + 信誉标记
- **M5**：`NotificationService` + `EmailService` + 签到 + 导出 + `CommentService` + `SchedulerService`
- **M6**：CSS 美化 + 响应式优化 + 交互打磨
