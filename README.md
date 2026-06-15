# 同光 · 企业 AI 每日早报（Routine + GitHub + 飞书 版）

> Anthropic Claude Code Routine + GitHub 持久化 + 飞书自动通知
> 每日 09:00 北京时间自动生成 · 历史档案永久保存 · 一键开门见早报

---

## 这是什么

每天北京时间 09:00，Claude Code Routine **自动**：

1. 从 GitHub clone 这个 repo
2. 读 `SKILL.md` 规范 + `sources.json` 信源清单
3. 用 web_fetch + web_search 抓取过去 24h 全球 181 个企业 AI 信源
4. 生成中文 Markdown 早报 → `reports/YYYY-MM-DD.md`
5. 更新目录 `reports/index.md`
6. Git commit + push 到 `main`
7. GitHub Actions 自动给你的飞书群发卡片消息

**你的笔记本可以关着、可以休假、可以出国旅行**——Routine 跑在 Anthropic 云上。

---

## 🚀 部署 4 步（约 20 分钟搞定）

### 前置条件 ✅

- Claude **Max** 计划（你已确认）
- Claude Code on the web 已启用 → https://claude.ai/code/settings
- GitHub 账号
- 飞书账号（含一个用来接收早报的群）
- 安装 Claude GitHub App → https://github.com/apps/claude

---

### Step 1：建 GitHub repo（5 分钟）

```bash
# 在你本地解压本 zip
unzip tongguang-ai-daily-routine.zip
cd tongguang-ai-daily-routine

# 初始化 git
git init
git add .
git commit -m "init: tongguang-ai-daily routine 版骨架"

# 在 GitHub.com 上创建新 repo,名字建议: tongguang-ai-daily
# 然后:
git remote add origin git@github.com:你的用户名/tongguang-ai-daily.git
git branch -M main
git push -u origin main
```

---

### Step 2：在 Claude Code 创建 Routine（5 分钟）

1. 打开 https://claude.ai/code
2. 左侧菜单 → **Routines** → **New routine**
3. 按下表填写：

| 字段 | 值 |
|---|---|
| **Name** | `同光企业 AI 早报` |
| **Repository** | 你的用户名/tongguang-ai-daily |
| **Branch** | `main` |
| **Instructions** | 复制 `.claude/routines/daily-briefing.md` **全部内容**粘贴 |
| **Model** | Claude Sonnet 4.6（推荐，省 token）或 Opus 4.7（深度更好） |
| **Trigger Type** | Scheduled |
| **Schedule** | Daily 09:00 Asia/Shanghai |

4. 滚到下方 **Environment** → **Allowed Domains** → **粘贴**`.claude/routines/daily-briefing.md` 第 "网络白名单" 章节里的全部域名（~80 个）

5. **Permissions** → 启用 **Allow unrestricted branch pushes**（不然 Claude 只能 push 到 `claude/*` 分支，要走 PR 合并流程）

6. 保存 routine

---

### Step 3：配置飞书机器人（5 分钟）

**详细图文步骤**见 [`docs/feishu-setup.md`](./docs/feishu-setup.md)。简要：

1. 飞书群 → 设置 → 群机器人 → 添加自定义机器人 → 拿 webhook URL
2. GitHub repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `FEISHU_WEBHOOK`
   - Value: 上一步的 webhook URL

完成后无需任何额外操作，每次 Routine commit 早报，飞书会自动收到卡片。

---

### Step 4：第一次测试（5 分钟）

**在 Routine 详情页点 "Run now"**，开始第一次跑。观察：

| 检查项 | 预期 |
|---|---|
| 进度日志显示抓取活动 | ✅ |
| 跑完后 `reports/YYYY-MM-DD.md` 文件出现 | ✅ |
| `reports/index.md` 顶部多了一行新条目 | ✅ |
| Git commit 自动推送到 main | ✅ |
| GitHub Actions notify.yml 被触发 | ✅ |
| 飞书群收到卡片消息 | ✅ |

如果其中任一项失败，参考 `docs/feishu-setup.md` 的"常见问题"或 README 末尾的"故障排查"。

---

## 📂 完整文件结构

```
tongguang-ai-daily/
├── README.md                          ← 你在读的这个文件
├── SKILL.md                           ← v5.1 完整规范（参考资产）
├── sources.json                       ← 181 信源清单
├── .gitignore
├── .claude/
│   └── routines/
│       └── daily-briefing.md          ← ⭐ Routine 入口 prompt
├── prompts/
│   ├── system.md                      ← 系统级指令
│   └── output-template.md             ← 早报模板（含禁令）
├── reports/
│   ├── index.md                       ← 自动维护的早报目录
│   ├── 2026-05-13.md                  ← 早报存档（Routine 每天追加）
│   ├── 2026-05-14.md
│   └── ...
├── docs/
│   └── feishu-setup.md                ← 飞书机器人配置指南
└── .github/
    └── workflows/
        └── notify.yml                 ← 飞书通知自动化
```

---

## ⚙️ Max 计划下的运行预算

| 项 | 量 |
|---|---|
| **Routine 配额** | Max = 每日 15 次（每月 ~450 次） |
| **本 Routine 占用** | 每日 1 次 = **6.7% 配额** ✅ 极宽裕 |
| **预留空间** | 14 次/日 留给：调试 + 周报汇编 + 月报 + 其他 routine |
| **token 消耗** | 30-50 万 tokens/次 ≈ Max 配额的 ~30-50% 单日消耗 |
| **预计运行时长** | 25-45 分钟 |
| **GitHub 存储** | 30 天 ~1-2MB / 1 年 ~15-25MB（白菜级） |
| **GitHub Actions 时长** | 每次 notify ≤ 30 秒（免费版 2000 分钟/月，远远够） |

**Max 计划下你完全可以再加几个 routine**：周报 / 月报 / 季度趋势分析 / 行业垂类周报 等。

---

## 🔄 三种触发方式

本 Routine 默认配置 **Scheduled（每日 09:00）**，但你随时可以补加 API 或 GitHub 触发。

### 默认：Scheduled

每日 09:00 Asia/Shanghai 自动跑。

### 可选：API 触发（手动跑或外部系统集成）

**用法**：等今天的 Routine 已经跑过、但你想再跑一次（比如下午有重磅新闻）：

```bash
curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_你的ID/fire \
  -H "Authorization: Bearer sk-ant-oat01-你的token" \
  -H "anthropic-beta: experimental-cc-routine-2026-04-01" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"text": "重大新闻：xxx 发布了 yyy,请重新跑今日早报"}'
```

要启用：在 Routine 编辑页 → Triggers → Add API trigger → 复制 URL 和 token（**token 只显示一次**）

### 可选：GitHub Event 触发

例如：当 `sources.json` 被改动时触发一次"测试跑"，验证新信源配置。

---

## 🔧 调试期前 3-5 天监控清单

第一周建议每天 09:30 检查一次：

- [ ] `reports/今天日期.md` 是否生成
- [ ] 文件大小是否合理（30-80KB 算正常，<10KB 可能信号过弱）
- [ ] 飞书群是否收到通知
- [ ] commit message 标签：`[strong-signal]` / `[medium-signal]` / `[weak-signal]` / `[partial]`
- [ ] 如果有 `[partial]`，看 Routine session URL 检查具体哪里中断

第一周可能遇到的真实问题（来自 v3.2 经验）：

| 症状 | 原因 | 修复 |
|---|---|---|
| 国内中文源全 0 命中 | 域名未加白名单 | 补充 36kr/qbitai/jiqizhixin 等到 Allowed Domains |
| Substack 系全 0 命中 | Substack 首页是 JS-only | 正常，SKILL 应自动转 search 兜底，验证此行为 |
| commit 推不到 main | Permissions 没开 | Routine 设置 → Allow unrestricted branch pushes |
| 飞书不发通知 | Secret 没配 | 看 GitHub Actions 日志 + `docs/feishu-setup.md` |
| 跑超 60 分钟被终止 | token 超预算 | 切到 Sonnet 4.6（更快）或简化 SKILL 的 Tier 4-6 batch |

---

## 🛠 进阶：调整与扩展

### A. 想要更"轻量"的早报（每天 15-20 篇）

编辑 `.claude/routines/daily-briefing.md`，把 Step 2 改成：

```
Step 2 简化版: 只跑 Tier 0+1+2 共 62 源,Tier 3-6 跳过
```

这样 Routine 跑 15-20 分钟就能完成，token 消耗减半。

### B. 想要周报 / 月报

复制 `.claude/routines/daily-briefing.md` 为 `.claude/routines/weekly-digest.md`，改成：

- Trigger: Scheduled, Weekly 周日 18:00
- Instructions: 读取过去 7 份早报 → 提炼 Top 20 趋势 → 写 `reports/weekly/2026-W19.md`

在 Claude Code 新建第二个 Routine 用这个文件。

### C. 想要别的通知渠道

`notify.yml` 当前只发飞书。如要再加：

- **企业微信**：直接复制 notify.yml 改成 `notify-wecom.yml`，curl 换 WeCom 的 markdown 格式
- **邮件**：用 `dawidd6/action-send-mail@v3` action（已留示例占位在 v1 notify.yml，但被我清理了，可以从 git history 里翻出）
- **Slack**：把飞书 webhook 换成 Slack incoming webhook

### D. 想要让 Routine 帮你做更多事

Max 计划每日 15 次 routine，你可以并行加：

- 客户企业 AI 情报 Routine（每周）
- 案例研究 Routine（每月）
- 周报汇编 Routine（每周日）
- 您行业垂类雷达（每日）

每个 routine 独立 instructions、独立 schedule。

---

## 🔗 相关文档

- [Claude Code Routines 官方文档](https://code.claude.com/docs/en/routines)
- [Routines 限额说明](https://claude.ai/settings/usage)
- [SKILL v5.1 完整规范](./SKILL.md)
- [181 信源清单](./sources.json)
- [飞书机器人配置](./docs/feishu-setup.md)

---

*Routine 版部署完成后，你和 Claude 的角色就分工了——*
*Claude 每天 09:00 替你跑信息搜集，你只需要点开飞书卡片读早报。*
