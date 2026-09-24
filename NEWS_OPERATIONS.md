# 全球 AI 早报的更新链路

## 2026-09-24 故障与修复

最后一份 Claude 深度早报为 `reports/2026-07-27.md`。此后 GitHub Actions 持续更新剪藏索引，并触发阅读库构建，但没有任务生成新的正文。`index.json` 的 `generated_at` 因而每天变动，正文仍停留在七月；主站正常镜像了旧内容。现有证据不能说明外部 Claude Routine 停止的具体原因。

恢复不依赖个人 Claude 会话的 RSS/Atom 自动采集。`live_sources.json` 是已验证的七个信源；`scripts/refresh_live_news.py` 保存原文标题、短摘要、链接、来源发布日期，写入 `docs/data/live-news.json`。未经过人工审编，界面标记“自动快讯 / 来源摘要 · 未评分”，不虚构质量评分或深度分析。原来 55 份早报及其 ID、收藏继续保留。

## 定时和发布

- `build-and-deploy-pages.yml` 北京时间计划 01:17、07:17、13:17、19:17 运行，也可手动运行；GitHub 调度可能延迟。
- 采集与索引产物先提交到 main，再发布本仓库 Pages。主站 `meigu-ai-stock-board` 每次部署拉取这里的 `docs/`，英语版块不受本仓库内容变化影响。
- 源文章时间、采集尝试时间、最近成功时间分开存储并展示。超过 30 小时没成功采集或 72 小时无新内容时，浏览器直接显示过期提醒，即使整个定时器停止也不会显示正常。
- 至少两个信源可用且采到 72 小时内的真实文章，才记作成功。单个信源失败可降级；全失败或无近期文章保留历史，先发布故障状态，再让 health job 失败。重跑不会制造重复条目。
- 剪藏任务和 Pages 任务使用同一并发组，提交前 rebase，减少数据互相覆盖。

## 维护

新增信源只修改 `live_sources.json`。`all_ai: false` 用于综合博客，按 AI 词过滤；不允许把未标日期的条目改成当天新闻。初次抓近七天，每源最多 25 条；已采文章留存在文件中。不要把自动快讯写进 `reports/` 冒充原来的深度审编早报。

本地验证：`python3 -m unittest discover -s tests`；采集：`python3 scripts/refresh_live_news.py`。浏览器检查 `/data/live-news.json` 和顶部的“信源状态与更新说明”。原深度早报需要恢复外部 Claude Routine 才能继续原审编方式；该部分未由 RSS 采集替代。
