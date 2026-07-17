# 评论模块 — 最小可执行任务

> 对应里程碑：M5（评论部分）
> 依赖：[registration.md](registration.md)（需报名审核通过才能评论）
> 完成后验收：已通过参与者可评论/回复，作者和组织者可删除评论

---

## 1. Service 层

- [ ] **1.1** 创建 `services/comment_service.py`，实现 `CommentService`：
  - [ ] `create(user_id, activity_id, content, parent_id=None)` → 发表评论或回复：
    - 校验权限：仅已通过审核（approved）的参与者 + 活动组织者可评论
    - 组织者对自己的活动始终可评论
    - 回复时（parent_id 非空）通知被回复者
    - 顶级评论时通知活动组织者（通知由 Router 或 Service 调用 `notification_service.notify_new_comment`）
  - [ ] `delete(comment_id, user_id)` → 删除评论：
    - 仅评论作者 或 活动组织者可删除
    - 返回 True/False
  - [ ] `get_by_activity(activity_id, page, page_size=20)` → 获取评论列表：
    - 先查顶级评论（parent_id IS NULL），按时间正序
    - 每条顶级评论附带其子回复（按时间正序）
    - 返回树形结构

## 2. Router 层

- [ ] **2.1** 创建 `routers/comments.py`：
  - [ ] `POST /activities/{id}/comments` → 发表评论（需登录）
  - [ ] `POST /comments/{id}/reply` → 回复评论（需登录）
  - [ ] `DELETE /comments/{id}` → 删除评论（需登录，作者或组织者）
  - [ ] `GET /activities/{id}/comments?page=N` → 获取评论列表（JSON，AJAX 加载，可选分页）

## 3. 模板集成

- [ ] **3.1** 在 `templates/activities/detail.html` 底部集成评论区：
  - 评论列表区域（树形展示：顶级评论 + 缩进的子回复）
  - 每条评论：头像占位、昵称、时间、内容、回复按钮、删除按钮
  - 已登录 + 有权限 → 显示评论输入框 + 提交按钮
  - 无权限 → 显示"仅通过审核的参与者可评论"
  - 未登录 → 显示"请登录后评论"

## 4. AJAX 评论加载

- [ ] **4.1** 评论列表通过 AJAX 加载（`GET /activities/{id}/comments?page=N`）
- [ ] **4.2** 发表评论通过 AJAX POST，成功后局部刷新评论区（不刷新整页）
- [ ] **4.3** 回复评论通过点击"回复"按钮展开内联输入框

## 5. 测试

- [ ] **5.1** 创建 `tests/test_comment_service.py`：
  - [ ] 已通过参与者发表评论 → 成功
  - [ ] 未通过审核者发表评论 → 拒绝
  - [ ] 未报名者发表评论 → 拒绝
  - [ ] 活动组织者发表评论 → 成功（即使未报名）
  - [ ] 回复评论 → 成功，parent_id 正确
  - [ ] 作者删除自己评论 → 成功
  - [ ] 活动组织者删除他人评论 → 成功
  - [ ] 非作者/非组织者删除评论 → 拒绝
  - [ ] 评论列表树形结构正确

- [ ] **5.2** 集成测试：
  - [ ] POST `/activities/{id}/comments` 发表评论
  - [ ] POST `/comments/{id}/reply` 回复
  - [ ] DELETE `/comments/{id}` 删除
  - [ ] 非权限操作返回 403

## 6. 验证

- [ ] **6.1** 通过审核的用户在活动详情页发表评论
- [ ] **6.2** 其他用户回复评论 → 显示嵌套结构
- [ ] **6.3** 作者删除自己的评论 → 评论消失
- [ ] **6.4** 组织者删除他人的评论 → 评论消失
- [ ] **6.5** 未通过审核者无法看到评论输入框
- [ ] **6.6** `uv run pytest tests/test_comment_service.py -v` 全部通过
