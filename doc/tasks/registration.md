# 报名模块 — 最小可执行任务

> 对应里程碑：M3（报名部分）+ M4（审核 & 候补）+ M5（签到 & 导出）
> 依赖：[activity.md](activity.md)（需有活动才能报名）
> 完成后验收：可报名/取消，组织者可审核/签到/导出，满额自动候补

---

## 1. Service 层

- [ ] **1.1** 创建 `services/registration_service.py`，实现 `RegistrationService`：
  - [ ] `register(user_id, activity_id)` → 报名逻辑：
    - 校验活动状态（非 cancelled/ended）
    - 校验报名截止时间
    - 校验不重复报名
    - 校验组织者不能报名自己活动
    - 名额未满 → `pending`；名额已满 → `waitlist`
  - [ ] `cancel(registration_id, user_id)` → 取消报名（仅本人），状态 → cancelled，触发 `promote_from_waitlist()`
  - [ ] `approve(registration_id, organizer_id)` → 审核通过（仅活动组织者），通知报名者
  - [ ] `reject(registration_id, organizer_id)` → 审核拒绝，触发候补递补，通知报名者
  - [ ] `check_in(registration_id, organizer_id)` → 手动签到（仅组织者，仅已通过状态可签到）
  - [ ] `get_by_activity(activity_id, status, page)` → 按活动 + 状态筛选报名列表（Tab 切换用）
  - [ ] `get_check_in_qr_data(activity_id, organizer_id)` → 生成签名 token（含 activity_id + 过期时间），返回签到 URL
  - [ ] `check_in_by_qr(activity_id, token, user_id)` → 验证 token 签名 + 有效期，执行签到
  - [ ] `export_csv(activity_id, organizer_id)` → 导出已通过名单为 CSV 字符串（列：昵称、邮箱、报名时间、签到状态）
  - [ ] `promote_from_waitlist(activity_id)` → 检查名额空缺，候补第一顺位（按报名时间）自动转 `pending`，并发通知
  - [ ] `get_user_reputation_info(user_id)` → 获取用户信誉信息（供模板展示用）

## 2. 报名状态机

- [ ] **2.1** 确认所有状态转换逻辑：
  - `pending` → `approved`（组织者通过）
  - `pending` → `rejected`（组织者拒绝）
  - `approved` → `checked_in`（签到）
  - `approved` → `cancelled`（用户取消）
  - `pending` → `cancelled`（用户取消）
  - `waitlist` → `cancelled`（用户取消）
  - `waitlist` → `pending`（候补自动递补）

## 3. Router 层

- [ ] **3.1** 创建 `routers/registrations.py`：
  - [ ] `POST /activities/{id}/register` → 报名（登录用户），返回详情页 + flash 消息
  - [ ] `POST /registrations/{id}/cancel` → 取消报名（仅本人）
  - [ ] `GET /activities/{id}/registrations` → 报名管理页（仅组织者），Tab：全部/待审核/已通过/已拒绝/候补
  - [ ] `POST /registrations/{id}/approve` → 审核通过
  - [ ] `POST /registrations/{id}/reject` → 审核拒绝
  - [ ] `POST /registrations/{id}/check-in` → 手动签到
  - [ ] `GET /activities/{id}/qr` → 签到二维码展示页（仅组织者）
  - [ ] `GET /check-in/{token}` → 扫码签到入口（登录用户扫码后自动签到）
  - [ ] `GET /activities/{id}/export` → 下载 CSV 文件

## 4. 签到二维码

- [ ] **4.1** 使用 `itsdangerous` 签名生成 token（含 activity_id + 过期时间 24h）
- [ ] **4.2** 二维码生成（可用 qrcode 库或前端 JS 库生成）
- [ ] **4.3** 组织者页面展示二维码图片 + 刷新按钮

## 5. CSV 导出

- [ ] **5.1** CSV 格式：昵称、邮箱、报名时间、签到状态（已签到/未签到）
- [ ] **5.2** 文件名：`{活动标题}_报名名单_{日期}.csv`
- [ ] **5.3** 响应头设置 `Content-Disposition: attachment`

## 6. 模板

- [ ] **6.1** 创建 `templates/registrations/manage.html`：
  - 活动信息摘要（标题、时间、报名人数/上限）
  - Tab 切换：待审核 / 已通过 / 已拒绝 / 候补（含各状态计数）
  - 每个报名者：昵称、邮箱、报名时间、失约标记（如有）、操作按钮
  - 待审核：通过 + 拒绝按钮
  - 已通过：签到按钮 + 签到状态标签
  - 导出 CSV 按钮 + 签到二维码按钮
  - 分页

## 7. 详情页集成

- [ ] **7.1** 在 `templates/activities/detail.html` 中集成报名按钮区：
  - 未登录 → "请登录后报名"链接
  - 未报名 + 有名额 → "立即报名"按钮
  - 未报名 + 满额 → "加入候补"按钮
  - 已报名（pending） → "等待审核中"标签 + 取消报名按钮
  - 已报名（approved） → "已通过"标签 + 取消报名按钮
  - 已报名（waitlist） → "候补中（第 X 位）"标签 + 取消报名按钮
  - 已报名（cancelled） → "已取消"标签
  - 已报名（rejected） → "已拒绝"标签
  - 组织者 → "管理报名"按钮（链接到报名管理页）
  - 报名者失约标记展示

## 8. 测试

- [ ] **8.1** 创建 `tests/test_registration_service.py`：
  - [ ] 报名成功 → status = pending
  - [ ] 名额满后报名 → status = waitlist
  - [ ] 重复报名 → 抛异常
  - [ ] 组织者报名自己活动 → 抛异常
  - [ ] 已结束活动报名 → 抛异常
  - [ ] 取消报名 → 触发候补递补
  - [ ] 审核通过 → 通知已发送
  - [ ] 审核拒绝 → 候补递补触发
  - [ ] 非组织者审核 → 拒绝
  - [ ] 签到 / 重复签到拒绝
  - [ ] 候补递补：第一顺位自动转 pending
  - [ ] CSV 导出内容正确
  - [ ] 二维码 token 验证

- [ ] **8.2** 集成测试：
  - [ ] 报名 → 取消 → 重新报名完整流程
  - [ ] 组织者审核通过 → 签到
  - [ ] 满额 → 候补 → 有人取消 → 自动递补
  - [ ] 导出 CSV 文件内容校验
  - [ ] 扫码签到流程

## 9. 验证

- [ ] **9.1** 用户报名 → 组织者在管理页看到待审核列表
- [ ] **9.2** 组织者通过审核 → 用户收到通知
- [ ] **9.3** 名额满后报名 → 自动进入候补
- [ ] **9.4** 有人取消 → 候补第一顺位自动递补
- [ ] **9.5** 组织者签到 → 报名状态变为已签到
- [ ] **9.6** 导出 CSV → 用 Excel 打开验证内容
- [ ] **9.7** 扫码签到 → 参与者扫码后自动签到
- [ ] **9.8** `uv run pytest tests/test_registration_service.py -v` 全部通过
