# 认证模块 — 最小可执行任务

> 对应里程碑：M1（后半部分）
> 依赖：[project-setup.md](project-setup.md)
> 完成后验收：可注册、登录、退出，"记住我"有效

---

## 1. Service 层

- [x] **1.1** 创建 `services/auth_service.py`，实现 `AuthService`：
  - `register(email, password, nickname)` → bcrypt 哈希密码，校验邮箱唯一性，创建 User，返回 User
  - `authenticate(email, password)` → 验证密码，成功返回 User，失败返回 None
  - 密码最小长度 6 位校验

## 2. Router 层

- [x] **2.1** 创建 `routers/auth.py`：
  - `GET /auth/login` → 渲染 `auth/login.html`（已登录用户重定向到首页）
  - `POST /auth/login` → 调用 `AuthService.authenticate()`，写入 Session（含 `remember_me` 控制 max_age），重定向到首页
  - `GET /auth/register` → 渲染 `auth/register.html`（已登录用户重定向到首页）
  - `POST /auth/register` → 调用 `AuthService.register()`，自动登录，重定向到首页
  - `GET /auth/logout` → 清除 Session，重定向到首页

## 3. 模板

- [x] **3.1** 创建 `templates/auth/login.html`
- [x] **3.2** 创建 `templates/auth/register.html`

## 4. Session 集成

- [x] **4.1** 在 `main.py` 中注册 `auth_router`
- [x] **4.2** 确认 `SessionMiddleware` 已配置
- [x] **4.3** 确认 `get_current_user` 依赖注入正常工作
- [x] **4.4** 确认未登录访问需认证页面时重定向到 `/auth/login`

## 5. 测试

- [x] **5.1** 创建 `tests/test_auth_service.py`：14 tests all passing
  - [x] 注册成功 → User 创建，密码为 bcrypt 哈希
  - [x] 重复邮箱注册 → 抛异常
  - [x] 密码过短注册 → 抛异常
  - [x] 登录成功 → 返回 User
  - [x] 密码错误 → 返回 None
  - [x] 邮箱不存在 → 返回 None
  - [x] "记住我" → Session max_age = 30 天
  - [x] 不勾选"记住我" → Session max_age = 浏览器关闭

- [x] **5.2** 集成测试（通过 TestClient）：
  - [x] GET `/auth/login` 返回 200 + HTML
  - [x] POST `/auth/register` 成功后重定向 + 可访问需登录页面
  - [x] POST `/auth/login` 成功后重定向
  - [x] GET `/auth/logout` 后无法访问需登录页面

## 6. 验证

- [x] **6.1** 注册新用户 → 自动登录 → 退出 → 重新登录
- [x] **6.2** 勾选"记住我" → 延长 Session 有效期
- [x] **6.3** `uv run pytest tests/test_auth_service.py -v` 全部通过
