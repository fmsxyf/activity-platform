# 用户模块 — 最小可执行任务

> 对应里程碑：M1（辅助）
> 依赖：[auth.md](auth.md)（需要登录态）
> 完成后验收：可查看/编辑个人信息，查看报名记录和发起的活动列表

---

## 1. Service 层

- [ ] **1.1** 创建 `services/user_service.py`，实现 `UserService`：
  - `get_user(user_id)` → 返回 User 或 None
  - `update_profile(user_id, nickname)` → 更新昵称，返回更新后的 User
  - `get_my_registrations(user_id, page, page_size=10)` → 分页查询报名记录（含关联 Activity 信息），按报名时间倒序
  - `get_my_activities(user_id, page, page_size=10)` → 分页查询发起的活动，按创建时间倒序

## 2. Router 层

- [ ] **2.1** 创建 `routers/users.py`：
  - `GET /users/profile` → 渲染 `users/profile.html`，展示个人信息 + 失约标记状态
  - `POST /users/profile` → 更新昵称，刷新页面 + flash 消息
  - `GET /users/my-registrations` → 分页展示报名记录（状态标签：待审核/已通过/已拒绝/候补/已取消）
  - `GET /users/my-activities` → 分页展示发起的活动（含报名人数统计）

## 3. 模板

- [ ] **3.1** 创建 `templates/users/profile.html`：
  - 邮箱（只读展示）
  - 昵称（可编辑，表单提交）
  - 失约标记状态（`no_show_count` + 是否可见）
  - "我的报名"链接 + "我的活动"链接
  - 保存按钮

- [ ] **3.2** 个人中心页内嵌"我的报名"列表：
  - 活动标题（链接到详情页）、报名状态标签、报名时间
  - 分页导航

- [ ] **3.3** 个人中心页内嵌"我发起的活动"列表：
  - 活动标题（链接到详情页）、状态、报名人数/上限、创建时间
  - 分页导航
  - "管理报名"入口

## 4. 集成

- [ ] **4.1** 在 `main.py` 中注册 `users_router`
- [ ] **4.2** 导航栏用户下拉菜单：个人中心、我的活动、退出

## 5. 测试

- [ ] **5.1** 创建 `tests/test_user_service.py`：
  - [ ] 获取存在的用户
  - [ ] 获取不存在的用户 → None
  - [ ] 更新昵称成功
  - [ ] 报名记录分页（含空列表）
  - [ ] 发起的活动分页（含空列表）

- [ ] **5.2** 集成测试：
  - [ ] GET `/users/profile` 已登录 → 200
  - [ ] GET `/users/profile` 未登录 → 302 重定向到登录
  - [ ] POST `/users/profile` 更新昵称 → 页面显示新昵称

## 6. 验证

- [ ] **6.1** 登录后访问个人中心，确认信息正确展示
- [ ] **6.2** 修改昵称 → 刷新确认生效
- [ ] **6.3** 未登录直接访问 `/users/profile` → 跳转到登录页
- [ ] **6.4** `uv run pytest tests/test_user_service.py -v` 全部通过
