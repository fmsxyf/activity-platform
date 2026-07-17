# 通知模块 — 最小可执行任务

> 对应里程碑：M5（通知 + 邮件部分）
> 依赖：[auth.md](auth.md)（需登录态）
> 完成后验收：站内通知可创建/查看/标记已读，导航栏红点实时更新，邮件在控制台输出

---

## 1. EmailService

- [ ] **1.1** 创建 `services/email_service.py`，实现 `EmailService`：
  - [ ] `__init__(smtp_config=None)` → 开发阶段 `smtp_config` 为 None
  - [ ] `send(to_email, subject, body)` → 开发模式：`print` 到控制台，格式：
    ```
    [EMAIL] To: xxx@example.com
            Subject: 报名审核结果 - {活动标题}
            Body: ...
    ```
  - [ ] 预留 SMTP 发送逻辑（生产模式切换）

## 2. NotificationService

- [ ] **2.1** 创建 `services/notification_service.py`，实现 `NotificationService`：
  - [ ] `create(user_id, type, title, content, link=None)` → 创建站内通知
  - [ ] `notify_registration_result(user_id, activity_title, result)` → 站内 + 邮件通知审核结果
  - [ ] `notify_waitlist_promoted(user_id, activity_title)` → 站内 + 邮件通知候补转正
  - [ ] `notify_activity_cancelled(user_ids, activity_title)` → 批量站内 + 邮件通知活动取消
  - [ ] `notify_new_comment(organizer_id, activity_title)` → 站内通知新评论
  - [ ] `get_unread_count(user_id)` → 返回未读通知数量（导航栏红点用）
  - [ ] `get_notifications(user_id, page, page_size=20)` → 分页查询通知列表，按时间倒序
  - [ ] `mark_read(notification_id, user_id)` → 标记单条已读
  - [ ] `mark_all_read(user_id)` → 全部标记已读

## 3. Router 层

- [ ] **3.1** 创建 `routers/notifications.py`：
  - [ ] `GET /notifications` → 通知列表页（分页）
  - [ ] `GET /notifications/unread-count` → 返回 JSON `{"count": N}`（供导航栏 AJAX 轮询）
  - [ ] `POST /notifications/{id}/read` → 标记已读，返回 JSON `{"ok": true}`
  - [ ] `POST /notifications/read-all` → 全部已读，重定向回通知列表

## 4. 模板

- [ ] **4.1** 创建 `templates/notifications/list.html`：
  - 通知列表：图标（按 type 区分）、标题、内容摘要、时间、"已读/未读"状态
  - 点击通知跳转到关联链接（如活动详情页）
  - "全部已读"按钮
  - 分页
  - 空状态："暂无通知"

## 5. 导航栏通知红点

- [ ] **5.1** 在 `templates/base.html` 导航栏添加通知铃铛图标 + 未读红点
- [ ] **5.2** 已登录时，红点显示未读数（`<span id="unread-badge">`）
- [ ] **5.3** 在 `static/js/main.js` 中实现 AJAX 轮询：
  - 每 30 秒请求 `GET /notifications/unread-count`
  - 更新红点数字
  - 未读数为 0 时隐藏红点

## 6. 集成：在其他模块触发通知

- [ ] **6.1** `RegistrationService.approve()` → 调用 `notify_registration_result()`
- [ ] **6.2** `RegistrationService.reject()` → 调用 `notify_registration_result()`
- [ ] **6.3** `RegistrationService.promote_from_waitlist()` → 调用 `notify_waitlist_promoted()`
- [ ] **6.4** `ActivityService.cancel()` → 调用 `notify_activity_cancelled()`
- [ ] **6.5** `CommentService.create()` → 顶级评论通知组织者，回复通知被回复者

## 7. 集成

- [ ] **7.1** 在 `main.py` 中注册 `notifications_router`
- [ ] **7.2** 配置 Service 依赖注入（`NotificationService` 注入 `EmailService`）

## 8. 测试

- [ ] **8.1** 创建 `tests/test_notification_service.py`：
  - [ ] 创建通知 → Notification 记录存在
  - [ ] 获取未读数 → 正确计数
  - [ ] 标记单条已读 → is_read = True
  - [ ] 全部已读 → 所有 is_read = True
  - [ ] 通知列表分页
  - [ ] 审核结果通知（站内 + 邮件调用）
  - [ ] 候补转正通知（站内 + 邮件调用）
  - [ ] 活动取消批量通知
  - [ ] 新评论通知
  - [ ] EmailService mock 验证邮件被调用

- [ ] **8.2** 集成测试：
  - [ ] GET `/notifications` 返回通知列表
  - [ ] GET `/notifications/unread-count` 返回 JSON
  - [ ] POST `/notifications/{id}/read` 标记已读
  - [ ] POST `/notifications/read-all` 全部已读

## 9. 验证

- [ ] **9.1** 审核报名 → 被审核者收到站内通知 + 控制台输出邮件
- [ ] **9.2** 导航栏红点显示正确未读数
- [ ] **9.3** 点击通知 → 标记已读
- [ ] **9.4** "全部已读" → 红点消失
- [ ] **9.5** 30 秒后红点自动更新
- [ ] **9.6** `uv run pytest tests/test_notification_service.py -v` 全部通过
