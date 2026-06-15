# AI 早报故障排查与恢复记录 · 2026-05-26

## 问题现象

今天早晨自动合并 Claude 早报流程出现问题，auto-merge workflow 全部 4 个 batch 均标记为 failure。

## 故障排查过程

### 1. 检查提交历史

- 最近 daily-briefing 合并提交：`b3af096` — `daily-briefing: 2026-05-25 [strong-signal]`（5/25 06:32 UTC）
- 今天的 4 个 batch 均已提交到 main：
  - `2d7baf8` — `authority-batch: 2026-05-26`（04:09 UTC）
  - `a33876c` — `industry-batch: 2026-05-26`（04:42 UTC）
  - `78d392f` — `china-batch: 2026-05-26`（05:07 UTC）
  - `3666b36` — `research-batch: 2026-05-26`（05:42 UTC）
- **没有** `daily-briefing: 2026-05-26` 合并提交 → `reports/2026-05-26.md` 缺失

### 2. 查看 workflow runs

通过 GitHub API 查询到 4 个 auto-merge workflow 全部 failure：

| Run ID | Batch | Status | Time |
|--------|-------|--------|------|
| 26417902347 | authority-batch | failure | 2026-05-25T20:09:27Z |
| 26419005984 | industry-batch | failure | 2026-05-25T20:42:26Z |
| 26419829492 | china-batch | failure | 2026-05-25T21:07:40Z |
| 26420928974 | research-batch | failure | 2026-05-25T21:42:53Z |

### 3. 根因定位

下载并分析 `authority-batch` 失败日志：

- 6 道安全护栏全部通过 ✅
- `gh pr merge` 执行成功，PR 已合并到 main ✅
- **失败发生在 Step 3-C**（显式触发 Pages 部署）：

```
could not create workflow dispatch event: HTTP 403: Resource not accessible by integration
```

**根因**：`auto-merge-claude-pr.yml` 缺少 `actions: write` 权限。

### 4. 时间线还原

| 时间 | 事件 | 结果 |
|------|------|------|
| 5/25 06:32 | May 25 daily-briefing auto-merge | ✅ success（当时还没有 Step 3-C） |
| 5/25 07:33 | 提交 `5933105` 新增 Step 3-C | ⚠️ 忘了加 `actions: write` 权限 |
| 5/26 04:09-05:42 | 4 个 batch auto-merge | PR **合并成功**，Step 3-C 全部 403 failure |

**关键**：PR 实际上已经成功合并（数据都在 main 上），只是 Step 3-C 的 403 导致整个 workflow 被标记为 failure。

### 5. 实际影响

- **PR 合并没问题** — 4 个 batch 文件已经在 main 上 ✅
- **Pages 部署没被显式触发** — 因为 Step 3-C 被 403 拦截
- **缺少 `reports/2026-05-26.md`** — 今天的 daily-briefing（合并汇总）未成功产出
- `reports/index.md` 未更新

## 修复措施

### 修复 1：添加 `actions: write` 权限

```diff
# .github/workflows/auto-merge-claude-pr.yml
 permissions:
   contents: write
   pull-requests: write
+  actions: write
```

commit: `aef525a` → `b95d1e2`（已推送）

### 修复 2：手动合并恢复 2026-05-26 日报

将 4 个 batch（authority 12 篇 + industry 23 篇 + china 19 篇 + research 18 篇）合并为：

- `reports/2026-05-26.md` — 72 篇精选，strong-signal
- 更新 `reports/index.md`

commit: `b490e38`（已推送）

## 结论

- **根因**：`5933105` 提交新增 Step 3-C 时遗漏了 `actions: write` 权限
- **非时间问题**：不是 cron 调度时间不对，不是 routine 没跑，是权限配置缺失
- **已修复**：权限已添加，明天 09:00 的 daily-briefing routine 应恢复正常
- **数据已恢复**：`reports/2026-05-26.md` 已合并推送，飞书通知应由 notify.yml 自动触发
