# 信誉模块 — 最小可执行任务

> 对应里程碑：M4（信誉部分）
> 依赖：[registration.md](registration.md)（需签到数据）
> 完成后验收：失约自动结算，失约 ≥3 次显示标记，连续正常签到 3 次恢复

---

## 1. Service 层

- [ ] **1.1** 创建 `services/reputation_service.py`，实现 `ReputationService`：
  - [ ] `settle_no_shows(activity_id)` → 结算指定活动的失约：
    - 查询该活动下 `status=approved` 且 `checked_in=False` 且 `no_show_recorded=False` 的报名记录
    - 对每条记录：`user.no_show_count += 1`，`registration.no_show_recorded = True`
    - 如果 `user.no_show_count >= 3`：`user.reputation_hidden = False`
    - 返回本次记为失约的人数
  - [ ] `is_reputation_visible(user_id)` → 返回 `not user.reputation_hidden`
  - [ ] `get_no_show_count(user_id)` → 返回 `user.no_show_count`
  - [ ] `record_good_attendance(user_id)` → 签到成功后调用：
    - `user.consecutive_good += 1`
    - 如果 `user.consecutive_good >= 3` 且 `user.no_show_count >= 3`：`user.reputation_hidden = True`
  - [ ] `get_reputation_info(user_id)` → 返回 dict：`{no_show_count, is_visible, consecutive_good}`

## 2. 信誉规则

- [ ] **2.1** 失约判定：活动结束后，已通过审核但未签到的报名者记为失约
- [ ] **2.2** 标记可见：累计失约 ≥ 3 次后，`reputation_hidden = False`
- [ ] **2.3** 标记恢复：连续正常签到 ≥ 3 次后，`reputation_hidden = True`
- [ ] **2.4** 再次失约：标记隐藏状态下再次失约 → `reputation_hidden` 重新变为 `False`，`consecutive_good` 归零
- [ ] **2.5** `no_show_count` 只增不减（历史累计）

## 3. 集成：在其他模块嵌入信誉逻辑

- [ ] **3.1** `RegistrationService.check_in()` 成功后 → 调用 `ReputationService.record_good_attendance(user_id)`
- [ ] **3.2** `SchedulerService` 中 → 活动结束后调用 `ReputationService.settle_no_shows(activity_id)`
- [ ] **3.3** 报名审核时 → 组织者可见报名者的 `no_show_count` + 失约标记
- [ ] **3.4** 活动详情页报名区域 → 展示报名者信誉标记（⚠ + "该用户累计失约 X 次"）
- [ ] **3.5** 个人中心 → 展示自己的信誉状态

## 4. 模板集成

- [ ] **4.1** `templates/registrations/manage.html` → 报名者列表显示失约次数 + ⚠ 标记
- [ ] **4.2** `templates/users/profile.html` → 显示自己的失约统计
- [ ] **4.3** `templates/activities/detail.html` → 报名按钮区附近（如已报名者）显示信誉标记

## 5. 测试

- [ ] **5.1** 创建 `tests/test_reputation_service.py`：
  - [ ] `settle_no_shows`：已通过未签到 → `no_show_count += 1`，`no_show_recorded = True`
  - [ ] `settle_no_shows`：已签到用户 → 不计为失约
  - [ ] `settle_no_shows`：重复结算 → 不重复计数（`no_show_recorded` 防护）
  - [ ] 失约满 3 次 → `reputation_hidden = False`，`is_reputation_visible = True`
  - [ ] `record_good_attendance`：`consecutive_good` 递增
  - [ ] 连续正常签到 3 次 → `reputation_hidden = True`
  - [ ] 标记隐藏后再次失约 → `reputation_hidden = False`，`consecutive_good` 归零
  - [ ] `get_reputation_info` 返回数据完整性

- [ ] **5.2** 集成测试：
  - [ ] 报名 → 审核通过 → 不签到 → 活动结束 → 失约 + 1
  - [ ] 累计 3 次失约 → 再次报名时组织者看到 ⚠ 标记
  - [ ] 连续 3 次正常签到 → 标记隐藏

## 6. 验证

- [ ] **6.1** 创建 3 个活动，报名通过但不签到，活动结束后确认失约标记出现
- [ ] **6.2** 之后连续正常签到 3 次，确认失约标记隐藏
- [ ] **6.3** 隐藏后再次失约，确认标记重新出现
- [ ] **6.4** 组织者审核时能看到报名者的失约次数
- [ ] **6.5** `uv run pytest tests/test_reputation_service.py -v` 全部通过
