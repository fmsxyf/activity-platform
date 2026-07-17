# 活动模块 — 最小可执行任务

> 对应里程碑：M2 + M3（活动浏览部分）
> 依赖：[auth.md](auth.md)（需登录态创建活动）
> 完成后验收：可创建/编辑/发布/取消活动，首页可搜索筛选浏览活动

---

## 1. Service 层

- [ ] **1.1** 创建 `services/activity_service.py`，实现 `ActivityService`：
  - [ ] `create(creator_id, data)` → 创建活动（draft 或 published），同时创建 ActivityTag 记录
  - [ ] `update(activity_id, user_id, data)` → 编辑活动，**有人报名则拒绝修改**
  - [ ] `publish(activity_id, user_id)` → 草稿发布（仅组织者）
  - [ ] `cancel(activity_id, user_id)` → 取消活动（仅组织者），状态 → cancelled
  - [ ] `get_by_id(activity_id)` → 获取详情（含标签、报名人数统计）
  - [ ] `search(keyword, category, tag, date_from, date_to, page, page_size=12)` → 搜索筛选，仅返回 published/ongoing 状态，按开始时间倒序
  - [ ] `get_by_creator(creator_id, page, page_size=10)` → 某用户发起的活动列表
  - [ ] `update_statuses()` → 批量更新：published（已到开始时间）→ ongoing，ongoing（已到结束时间）→ ended。返回计数 dict

## 2. 活动状态机

- [ ] **2.1** 确认所有状态转换逻辑：
  - `draft` → `published`（发布）
  - `published` → `ongoing`（到达开始时间，Scheduler 自动）
  - `ongoing` → `ended`（到达结束时间，Scheduler 自动）
  - 任意非 ended 状态 → `cancelled`（组织者取消）

## 3. Router 层

- [ ] **3.1** 创建 `routers/activities.py`：
  - [ ] `GET /` → 首页活动广场：搜索框、分类下拉、标签筛选、时间范围、分页卡片列表
  - [ ] `GET /activities/create` → 创建活动表单页
  - [ ] `POST /activities/create` → 处理表单 + 封面图片 multipart 上传（限制 2MB，校验 MIME 类型），支持"保存草稿"和"直接发布"
  - [ ] `GET /activities/{id}` → 活动详情页（含报名状态、报名人数、剩余名额、倒计时数据）
  - [ ] `GET /activities/{id}/edit` → 编辑活动表单页（仅组织者，有人报名则显示不可编辑提示）
  - [ ] `POST /activities/{id}/edit` → 处理编辑提交（含图片更新）
  - [ ] `POST /activities/{id}/publish` → 发布草稿
  - [ ] `POST /activities/{id}/cancel` → 取消活动（需二次确认）

## 4. 文件上传

- [ ] **4.1** 封面图片上传逻辑：
  - 校验文件大小 ≤ 2MB
  - 校验 MIME 类型（仅允许 image/jpeg, image/png, image/gif, image/webp）
  - 生成唯一文件名（UUID + 原扩展名）
  - 保存到 `uploads/` 目录
  - 路径存入 `Activity.cover_image`

## 5. 模板

- [ ] **5.1** 创建 `templates/activities/create.html`：
  - 表单：标题、描述(textarea)、分类(下拉)、标签(逗号分隔输入)、封面图(文件选择)、开始时间、结束时间、地点、人数上限、费用、报名截止时间
  - "保存草稿" + "发布"两个提交按钮

- [ ] **5.2** 创建 `templates/activities/edit.html`：
  - 同 create 表单，预填现有数据
  - 有人报名时显示锁定提示

- [ ] **5.3** 创建 `templates/activities/detail.html`：
  - 封面图、标题、组织者昵称
  - 时间、地点、费用、报名人数/上限（"X / ∞"）
  - 倒计时（`data-start-time` 属性供 JS 使用）
  - 活动描述正文
  - 报名按钮区（根据状态显示不同按钮）
  - 评论区占位 + 组织者管理入口

- [ ] **5.4** 创建 `templates/activities/my.html`：
  - 我发起的活动列表，每个条目：标题、状态标签、报名人数、操作按钮（编辑/取消/管理报名）

- [ ] **5.5** 更新 `templates/index.html`：
  - 搜索栏（关键词 input + 分类 select + 标签 input + 日期范围）
  - 活动卡片网格（3列/2列/1列 响应式）
  - 每张卡片：封面图、标题、分类标签、时间、地点、费用、报名人数/上限、倒计时
  - 底部分页导航

## 6. 倒计时 JS

- [ ] **6.1** 在活动卡片和详情页实现倒计时：
  - 从 `data-start-time` 读取时间戳
  - 每秒更新显示：`X 天 X 时 X 分 X 秒`
  - 已开始 → "进行中"
  - 已结束 → "已结束"

## 7. 集成

- [ ] **7.1** 在 `main.py` 中注册 `activities_router`
- [ ] **7.2** 导航栏 Logo 链接到首页

## 8. 测试

- [ ] **8.1** 创建 `tests/test_activity_service.py`：
  - [ ] 创建草稿 / 发布活动
  - [ ] 编辑无报名者的活动 → 成功
  - [ ] 编辑有报名者的活动 → 拒绝
  - [ ] 非组织者编辑 → 拒绝
  - [ ] 取消活动 → 状态变为 cancelled
  - [ ] 按关键词搜索
  - [ ] 按分类筛选
  - [ ] 按标签筛选
  - [ ] 按时间范围筛选
  - [ ] 分页查询
  - [ ] `update_statuses()` 状态流转正确

- [ ] **8.2** 集成测试：
  - [ ] GET `/` 返回首页 + 活动卡片
  - [ ] POST `/activities/create` 创建活动 → 重定向到详情页
  - [ ] GET `/activities/{id}` 展示详情
  - [ ] 组织者编辑活动成功
  - [ ] 非组织者访问编辑页 → 403
  - [ ] 封面图上传 → 文件出现在 uploads/

## 9. 验证

- [ ] **9.1** 创建活动 → 在首页看到卡片
- [ ] **9.2** 按分类/标签/关键词搜索筛选
- [ ] **9.3** 上传封面图 → 详情页显示图片
- [ ] **9.4** 编辑活动（无人报名时）→ 修改生效
- [ ] **9.5** 取消活动 → 活动列表显示"已取消"
- [ ] **9.6** `uv run pytest tests/test_activity_service.py -v` 全部通过
