# 调度模块 — 最小可执行任务

> 对应里程碑：M5（后台任务部分）
> 依赖：[activity.md](activity.md) + [registration.md](registration.md) + [reputation.md](reputation.md)
> 完成后验收：后台定时任务自动更新活动状态、结算失约、处理候补递补

---

## 1. Service 层

- [ ] **1.1** 创建 `services/scheduler_service.py`，实现 `SchedulerService`：
  - [ ] `__init__(db_factory, activity_service, registration_service, reputation_service)`
  - [ ] `async run_loop(interval=300)` → 后台异步循环，每 `interval` 秒执行一次：
    - 步骤 1：`ActivityService.update_statuses()` → 更新活动状态
    - 步骤 2：对刚变为 `ended` 的活动 → `ReputationService.settle_no_shows(activity_id)`
    - 步骤 3：对所有 `published`/`ongoing` 状态的活动 → `RegistrationService.promote_from_waitlist(activity_id)`
    - 异常处理：单次循环出错不中断整个循环，记录错误日志
  - [ ] 每次循环开始/结束时打印日志：`[Scheduler] Cycle #N started/completed`

## 2. FastAPI 生命周期集成

- [ ] **2.1** 在 `main.py` 的 `lifespan` 中：
  - 创建 `SchedulerService` 实例（注入各 Service 工厂）
  - 使用 `asyncio.create_task(scheduler.run_loop())` 启动后台任务
  - 在 shutdown 阶段取消后台任务（`task.cancel()` + `try/except CancelledError`）

## 3. 调度逻辑细节

- [ ] **3.1** `update_statuses()` 调用时机：每 300 秒（5 分钟）扫描一次
- [ ] **3.2** 失约结算时机：仅对**本轮**状态变为 `ended` 的活动结算（可用 `updated_at` 或状态变更追踪）
- [ ] **3.3** 候补递补时机：每次循环检查所有进行中的活动
- [ ] **3.4** 每次循环使用独立的数据库 Session（从 `db_factory` 获取）

## 4. 测试

- [ ] **4.1** 创建 `tests/test_scheduler_service.py`：
  - [ ] `update_statuses()` 被调用 → 活动状态正确流转
  - [ ] `settle_no_shows()` 被调用 → 失约正确结算
  - [ ] `promote_from_waitlist()` 被调用 → 候补递补
  - [ ] 循环内单步异常不影响后续步骤
  - [ ] 多次循环间使用独立 Session

- [ ] **4.2** 使用 `unittest.mock.AsyncMock` + `patch`：
  - [ ] Mock `ActivityService.update_statuses()` 返回 `{published→ongoing: 1, ongoing→ended: 1}`
  - [ ] 验证 `settle_no_shows` 被调用（且仅对 ended 活动）
  - [ ] 验证 `promote_from_waitlist` 被调用

## 5. 验证

- [ ] **5.1** 启动服务 → 控制台看到 `[Scheduler]` 日志输出
- [ ] **5.2** 创建一个活动，设置开始时间为 1 分钟后 → 等待调度 → 状态变为 ongoing
- [ ] **5.3** 创建活动 → 报名通过 → 不签到 → 等待结束时间 → 确认失约记录
- [ ] **5.4** 活动满额 → 有人报名进入候补 → 有人取消 → 等待调度 → 候补转正
- [ ] **5.5** `uv run pytest tests/test_scheduler_service.py -v` 全部通过
