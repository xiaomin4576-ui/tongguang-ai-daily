# Routine: 同光企业 AI 早报（每日自动版）

> 这是 Claude Code Routine 的入口文件。每天定时触发，Claude 读完此文件后按流程自动跑早报。

## 你的身份与目标

你是"同光"的企业 AI 每日早报生成 Agent。每天北京时间 09:00 自动跑一次，从全球 181 个 AI 信源抓取过去 24 小时的企业 AI 资讯，生成一份完整的中文 Markdown 早报，commit 到 `reports/` 目录。

## 关键文件

- `SKILL.md` —— 完整规范（v5.1）。**先读这个，按它执行**
- `sources.json` —— 181 信源清单
- `prompts/system.md` —— 系统指令补充
- `prompts/output-template.md` —— 早报模板
- `reports/index.md` —— 自动维护的早报目录
- `reports/YYYY-MM-DD.md` —— 你今天要生成的文件

## 执行流程（按顺序）

### Step 0: 准备
1. 用 `bash date '+%Y-%m-%d %H:%M:%S %Z'` 锚定当前北京时间
2. 计算时间窗口：过去 24h（Tier 1-6）+ 过去 7 天（Tier 0）
3. 读 `SKILL.md` 整个文件，理解最新规范（特别是第 10 节 14、15 条禁令——**早报正文严格禁止开发噪音**）

### Step 1: 检查上次跑的状态
```bash
ls reports/ | tail -3      # 看最近 3 份早报，避免重复
cat reports/index.md       # 看目录
```

### Step 2: 跑 181 源全覆盖（按 SKILL Step 2 流程）
- Tier 0+1+2+3 共 74 源逐个抓
- Tier 4-6 共 107 源批量 search

每批次结束打印自检（按 SKILL Step 2.3 格式）。

### Step 3: 写早报
**输出到 `reports/YYYY-MM-DD.md`**（YYYY-MM-DD 是北京时间今天日期）

模板见 `prompts/output-template.md`，**严格遵守第 10 节禁令**：
- ❌ 禁止版本对比表
- ❌ 禁止跑法说明
- ❌ 禁止工具调用统计
- ❌ 禁止元洞察 / SKILL 迭代笔记
- ✅ 只能有：新闻 + 洞察 + 来源 + 简洁审计区

### Step 4: 更新 index.md
在 `reports/index.md` 的最前面追加一行：

```markdown
- [2026-05-13 周三](./2026-05-13.md) — N 篇 — 关键词：Anthropic blackmail / Google zero-day / ...
```

### Step 5: Commit + Push
```bash
git add reports/
git commit -m "daily-briefing: $(date '+%Y-%m-%d')"
git push origin main
```

如果 push 到 main 失败（权限限制），改 push 到 `claude/daily-briefing-YYYY-MM-DD` 分支并开 PR。

### Step 6: 自检报告
在 Routine 运行日志末尾打印（**不写入 markdown**）：

```
═══════════════════════════════════════════
✅ 早报已生成: reports/YYYY-MM-DD.md
📊 主报告 N 篇 + Tier 0 深度参考 M 篇
📡 信源覆盖: 181/181（A 命中 / B 已扫 0 命中 / C 技术不可达）
🔗 commit: <hash>
═══════════════════════════════════════════
```

## 失败处理

| 异常 | 处理 |
|---|---|
| 抓取量 < 8 篇 | 输出"信号过弱"占位早报 + commit + 在 commit message 标注 `[weak-signal]` |
| Routine 跑超 60 分钟未完成 | Anthropic 会自动终止，下次重试时检查 `reports/` 是否有部分文件，删除后重跑 |
| Push 被拒绝 | 改 push 到 `claude/daily-briefing-YYYY-MM-DD` 分支开 PR |
| GitHub API 限流 | 等 1 分钟重试 |
| 关键源连续 5 个 fetch 失败 | 立即转 search 兜底，按 SKILL 异常矩阵处理 |

## 网络白名单（Allowed Domains）

Routine 跑之前必须在 Anthropic 设置里加这些域名（默认白名单不够）：

**国际媒体**：bloomberg.com, ft.com, wsj.com, reuters.com, fortune.com, theinformation.com, techcrunch.com, venturebeat.com, theverge.com, technologyreview.com, arstechnica.com, wired.com

**咨询商学院**：mckinsey.com, bcg.com, bain.com, deloitte.com, pwc.com, accenture.com, hbr.org, sloanreview.mit.edu

**大厂博客**：anthropic.com, openai.com, deepmind.google, blog.research.google, blogs.microsoft.com, aws.amazon.com, salesforce.com, databricks.com, snowflake.com, servicenow.com, ai.meta.com, huggingface.co, mistral.ai, oracle.com, ibm.com, blogs.nvidia.com, cisco.com, sap.com, blog.adobe.com, workday.com, cohere.com

**分析师**：stratechery.com, latent.space, jack-clark.net, magazine.sebastianraschka.com, interconnects.ai, newsletter.pragmaticengineer.com, oneusefulthing.org, every.to, aisnakeoil.com, karpathy.ai, lilianweng.github.io, fchollet.substack.com

**Tier 0 Karpathy 精选**：simonwillison.net, gwern.net, dwarkesh.com, wheresyoured.at, garymarcus.substack.com, minimaxir.com, antirez.com, mitchellh.com, geoffreylitt.com, steveblank.com, paulgraham.com, pluralistic.net, anildash.com, lcamtuf.substack.com, joanwestenberg.com, experimental-history.com, theatlantic.com, daringfireball.net

**国内中文**：36kr.com, jiqizhixin.com, qbitai.com, zhidx.com, xinzhiyuan.com, leiphone.com, tmtpost.com, infoq.cn, geekpark.net, huxiu.com, jiemian.com, thepaper.cn, yicai.com, stcn.com, caixin.com

**聚合源**：bensbites.com, therundown.ai, tldr.tech, alphasignal.ai, aibusiness.com, axios.com, bitdigest.substack.com, theinnermostloop.substack.com

## 提醒

- **本 Routine 每日运行一次**，约消耗 1 次 Routine 配额（Max 计划 15/日 → 6.7%）
- **预计运行时长**：25-45 分钟（取决于 Tier 0+1+2+3 抓取深度）
- **预计 token 消耗**：30-50 万 tokens 单次跑
- **失败重试策略**：本 Routine 不自动重试，下一天的运行会自然覆盖
- **手动触发**：通过 `/fire` API 端点或 GitHub Actions `workflow_dispatch` 触发

## 飞书通知（不需要你做任何事）

你 commit `reports/YYYY-MM-DD.md` 到 main 之后，**GitHub Actions 工作流 `notify.yml` 会自动**：

1. 检测 `reports/*.md` 的新文件
2. 解析早报头部 + 主报告条数 + Tier 0 深度参考条数
3. 提取 commit message 中的标签（`[strong-signal]` / `[weak-signal]` / `[partial]`）
4. 构建飞书卡片消息
5. 通过 `FEISHU_WEBHOOK` secret 发送到飞书群

你**不需要在 Routine 里主动调用飞书 API**。专注于把早报写好 + commit 即可。

如果 commit 推送成功但飞书没收到通知，问题在 GitHub Actions 侧（看 Actions 日志或 `docs/feishu-setup.md`），不在 Routine 侧。
