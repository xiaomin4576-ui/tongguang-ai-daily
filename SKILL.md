---
name: tongguang-ai-daily
description: 同光 · 企业 AI 每日早报 Agent。当用户希望了解过去 24 小时全球企业 AI 动态、阅读每日 AI 早报、扫描企业级 AI 资讯（产品发布/融资/部署案例/组织变革/基础设施/咨询研究/监管）时，必须使用本技能。触发词包括：「同光日报」「同光早报」「跑一下日报」「跑一下同光早报」「tongguang-ai-daily」「采集 AI 文章」「今天的 AI 新闻」「AI 早报」「AI 日报」「企业 AI 资讯」「扫一下 AI」「过去 24 小时 AI 动态」「昨天 AI 圈发生了什么」「补充 X 篇」。即便用户只说「采一下」「跑下今天的 AI」「看看昨天的 AI 动态」「日报跑一下」，只要上下文涉及企业 AI 资讯的批量采集→去重→筛选→翻译→Markdown 交付，必须触发本技能。本技能聚焦「企业 AI」视角（B2B、落地、商业化、组织变革、咨询研究），不报道纯学术论文、消费级 AI 玩具、AI 艺术等。本版本（v5.1）在 Claude.ai 对话内单次执行，使用 web_fetch + web_search 抓取 **181 个信源（全覆盖审计）**——Karpathy 2026/01 推荐的 92 信源 + v4 原 64 + 用户扩展 28 个，由 Claude 直接翻译并输出一份完整 Markdown 早报，目标 30-50 篇按实际输出。v5.1 在 v5 跑过两次后修复了"抓取覆盖率不可见、Tier 0 24h 窗口太窄、Substack/微信公众号反复 fetch 失败、新增 28 源 0 利用率、目标 60 落差大"等真实问题。区别于同家族 skill：本技能是「每日全景早报」，不同于 enterprise-ai-radar（单家企业深度情报）、enterprise-ai-product-radar（周/月产品扫描）、ai-report-radar（研究报告扫描）、global-case-radar（已定型案例扫描）。
---

# 同光 · 企业 AI 每日早报（tongguang-ai-daily） v5.1

> 在 Claude.ai 对话内单次执行，每跑一次产出一份完整 Markdown 早报，让你 20 分钟看完上一天全球企业 AI 动静。
>
> **v5.1 核心变化（vs v5.0）**：
> 1. **新增"181 源全覆盖"承诺**——每个源都要有明确状态（✅ 抓到 X 篇 / 🟡 24h 内无更新 / ❌ 技术不可达）
> 2. **新增"抓取覆盖率自检"**——跑到一半时强制打印进度，低于阈值不允许进入输出阶段
> 3. **新增"批量 search 优化"**——Tier 5 / 聚合源 / 抓不到首页的源用批量 search 而非单 fetch
> 4. **新增"按源类型分发抓取策略"**——Substack/Ghost/微信公众号等技术不可达源**默认 search 兜底**，不浪费 fetch
> 5. **Tier 0 默认窗口改 7 天**——这层"每周 1-3 篇深度长文"特征，24h 太窄，扩到 7 天能贡献 5-12 篇深度参考
> 6. **新增"📌 这意味着"好/坏范例对照**——避免陈词滥调，强制每条带具体决策动作
> 7. **新增独立维度"🧠 Tier 0 深度参考"**——不再塞在脚注，Tier 0 是 v5 的灵魂层
> 8. **目标数校准**：60 → **30-50 按实际输出**，区分弱信号日（20-30）/ 强信号日（50-70）/ DevDay 级（70+）

---

## 0. 核心定位（先读这一节，决定一切）

| 项 | 设定 |
|---|---|
| **唯一目标** | 给用户一份"上一天的企业 AI 全景"，能在 20 分钟内读完 |
| **核心视角** | **企业 AI**——B2B、落地、商业化、组织变革、咨询研究、基础设施、制造垂类 |
| **不报道什么** | 纯 Arxiv 学术论文、消费级 AI 玩具、AI 生成艺术、纯 PR 通稿、AI 政治哲学讨论、复古计算/Linux 内核细节（即使在 Karpathy 92 信源里） |
| **数量** | **目标 30-50 篇（按实际输出，不硬凑）**：弱信号日 20-30，强信号日 50-70，DevDay/Sapphire/GTC 级爆发日 70+ |
| **执行环境** | **Claude.ai 对话内单次执行**（不依赖 Routine、不依赖 GitHub） |
| **抓取工具** | `web_search` + `web_fetch` 组合（不依赖 RSS 库） |
| **语言** | 抓英文/中文源 → 全部以中文呈现，专有名词保留原文 |
| **信源数** | **181 个，全覆盖**（Tier 0 Karpathy 精选 18 + Tier 1 企业核心 22 + Tier 2 大厂博客 22 + Tier 3 分析师 12 + Tier 4 国内中文 17 + Tier 4B 制造垂类 5 + Tier 4C 红杉系 3 + Tier 5 Karpathy 其余 74 + Tier 6 聚合 8 = 181） |
| **窗口策略** | **分层窗口**：Tier 0 默认 **7 天**（这层"每周 1-3 篇深度长文"特征），其他 Tier 严格 **24 小时** |
| **判断标尺** | 一个负责企业 AI 的 CXO/VP/PM/咨询顾问，会不会觉得"这条值得我知道"？ |

> **核心承诺：181 源全覆盖**。每个源在最终输出里必须有明确状态：
> - ✅ 抓到 N 篇 → 进入早报正文
> - 🟡 抓了但 24h/7d 内无新内容 → 列入"已扫但 0 命中"附表
> - ❌ 技术不可达（Substack/微信公众号/JS-only 站点）→ 列入"技术不可达"附表 + 用 search 兜底
> - ⏭ 主动跳过（如 Tier 5 个人技术博客明显与企业 AI 无关）→ 列入"主动跳过"附表
>
> **关键设计原则**：**物理纳入 ≠ 全部必抓内容**，但**全部必须点名**。Karpathy 92 源中纯个人技术博客（复古计算/Linux/历史随笔）即使在 24h 内有更新也不收录到早报正文，但必须出现在"已扫"附表里证明 Claude 查过了。

---

## 1. 七维度内容范围（企业 AI 视角）

| 维度 | 目标 | 范围（±2） | 内容 |
|---|---|---|---|
| 🚀 **企业级 AI 产品** | 11 | 8-14 | B2B SaaS、Agent 平台、企业级 LLM、行业垂直产品发布/更新 |
| 🏢 **企业部署案例** | 11 | 8-14 | 某公司用了什么 AI、效果数据、踩坑、ROI、用了哪家厂商 |
| 💰 **商业进展** | 9 | 6-12 | 融资、收入、估值、ARR、客户增长、并购、关键高管 |
| 👥 **组织变革** | 7 | 5-10 | 岗位重塑、人机协同、AI-native 团队、技能转型 |
| ⚙️ **基础设施 & 成本** | 7 | 5-10 | 推理优化、API 定价、新模型发布、GPU/算力、token 经济学 |
| 📊 **咨询研究** | 8 | 5-12 | McKinsey/BCG/Bain/Deloitte/PwC/Accenture/HBR/Sloan + Karpathy 精选思考者长文 |
| ⚖️ **监管 & 风险** | 7 | 4-10 | 法规、版权诉讼、合规事件、企业 AI 治理、安全事故、隐私 |
| **合计** | **60** | **40-80** | 弱信号日 30-40，强信号日 70-80，按实际输出不硬凑 |

> v5 配额按 v4 的 1.5 倍放大但保留 7 维度结构。咨询研究维度从 5→8，因为新增 Karpathy Tier 0 中的 garymarcus / wheresyoured.at / experimental-history 这些"深度思考者"长文也归入此维度。

---

## 2. 信源清单（v5 重构，181 个源 + Karpathy 全清单工具箱）

完整清单见 `sources.json`。下表是分层概览。

### 2.1 Tier 0 · Karpathy 精选企业 AI 信源（必抓 18 个，v5 新增最重要）

> Karpathy 2026 年 1 月推荐的 92 个 HN 最受欢迎博客中，与企业 AI / AI 战略 / AI 商业化强相关的精选。

| 源 | 定位 | 主攻维度 |
|---|---|---|
| Simon Willison | 实用 AI 第一人，几乎每天更新 | 产品、工程 |
| Gwern Branwen | AI 深度分析 | 战略 |
| Dwarkesh Patel | 高质量 AI 访谈 | 战略 |
| Where's Your Ed At (Ed Zitron) | AI 商业批判 | 商业批判 |
| Marcus on AI (Gary Marcus) | AI 批判 + 监管视角 | 监管 |
| Max Woolf (minimaxir) | 实用 AI | 工程 |
| antirez (Redis 创始人) | 工程 + AI 应用 | 工程 |
| Mitchell Hashimoto (Hashicorp) | 基础设施 | 工程 |
| Geoffrey Litt | AI 工具产品 | 产品 |
| Steve Blank | 创业方法论 | 商业 |
| Paul Graham | 产业思考 | 商业 |
| Pluralistic (Cory Doctorow) | 科技批判 | 监管 |
| Anil Dash | 科技社会评论 | 监管 |
| Michał Zalewski (lcamtuf) | AI 安全 | 监管 |
| Joan Westenberg | AI 评论 | 综合 |
| Experimental History | AI 研究批判 | 咨询研究 |
| Derek Thompson (The Atlantic) | 商业宏观 | 商业 |
| Daring Fireball (John Gruber) | 科技产业评论 | 综合 |

### 2.2 Tier 1 · 企业 AI 核心源（必抓 22 个，继承 v4）

**🏢 一线财经/商业媒体（6）**：The Information / Bloomberg Tech / Reuters Tech / FT AI / Fortune AI / WSJ AI

**📊 咨询商学院（8）**：McKinsey / BCG / Bain / Deloitte / PwC / Accenture / HBR / Sloan

**🛠 科技媒体一线（6）**：TechCrunch AI / VentureBeat AI / The Verge AI / MIT Tech Review / Ars Technica / Wired AI

**🏆 顶级 VC（2）**：a16z / Sequoia

### 2.3 Tier 2 · 企业大厂 AI 官方博客（必抓 22 个，v4 14 + v5 新增 8）

v4 已有：Anthropic / OpenAI / DeepMind / Google AI / Microsoft AI / Microsoft Research / AWS ML / Salesforce / Databricks / Snowflake / ServiceNow / Meta AI / Hugging Face / Mistral

**v5 新增 8 个**：Oracle / IBM / NVIDIA / Cisco / SAP News / Adobe / Workday / Cohere

### 2.4 Tier 3 · 独立分析师 & 思考者（必抓 13 个，v4 10 + v5 新增 3 个研究者）

v4 已有：Stratechery / Latent Space / Import AI / Sebastian Raschka / Nathan Lambert / Pragmatic Engineer / One Useful Thing / Every / AI Snake Oil

**v5 新增 3 个**：Andrej Karpathy / Lilian Weng (翁荔) / François Chollet (Keras 作者)

### 2.5 Tier 4 · 国内中文媒体（必抓 17 个，v4 10 + v5 新增 7）

v4 已有：36氪 AI / 机器之心 / 量子位 / 智东西 / 新智元 / 雷锋网 AI / 钛媒体 / InfoQ 中文 / 极客公园 / 虎嗅 AI

**v5 新增 7 个**：界面新闻科技 / 澎湃科技 / 未来智库 / 心智君公众号 / 第一财经 / 证券时报 / 财新科技

### 2.6 Tier 4B · 行业垂类制造 AI（必抓 5 个，v5 新增）

IndustryWeek AI / Manufacturing.net / SME Smart Manufacturing / 中国信通院 / Automation.com

### 2.7 Tier 4C · 红杉系 VC 扩展（必抓 3 个，v5 新增）

红杉中国 / 红杉资本公众号 / Y Combinator (W26/S26)

### 2.8 Tier 5 · Karpathy 92 剩余源（兜底，74 个）

剩余 74 个 Karpathy 推荐源，主要类型：
- **个人技术博客**（Linux 内核、编译器、Rust 等）：matklad / rachelbythebay / lucumr / overreacted 等
- **复古计算/历史随笔**：filfre / oldvcr / abortretry / construction-physics 等
- **安全研究**：Krebs on Security / micahflee / mjg59 / Troy Hunt 等
- **个人随笔/文化**：daringfireball / johndcook / xeiaso 等

**这些源不优先抓**。只在前面 Tier 抓取量明显不足且其中某条罕见地涉及企业 AI 时才纳入早报。完整清单保留是为了让用户拥有 Karpathy 92 信源的完整资产。

### 2.9 Tier 6 · 聚合 & Newsletter（兜底 8 个）

Ben's Bites / The Rundown AI / TLDR AI / AlphaSignal / AI Hub Today / AI Business / Axios AI / HN Buzzing

### 2.10 ❌ 仍然不收的（即使在 Karpathy 92 里也不收）

| 类别 | 不收的原因 |
|---|---|
| 复古计算/Linux 内核细节 | 与企业 AI 视角距离过远 |
| 纯个人随笔/家庭/兴趣 | 信号密度低 |
| 学术论文聚合（Arxiv/Papers with Code/HF Papers） | 留给 ai-report-radar 等 skill |
| Twitter/X | 第三方爬虫不稳定 |

---

## 3. 执行流程（Claude.ai 单次跑视角）

```
Step 1: 时间锚定 → Step 2: 调度抓取计划 → Step 3: 分批 web_fetch/web_search
                                                ↓
Step 6: 输出完整 Markdown ← Step 5: 翻译+打磨+"📌 这意味着" ← Step 4: 去重+维度筛选+质量打分
```

### Step 1：时间锚定（必做）

第一件事——用 `bash_tool` 执行 `date` 拿到运行时刻：

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
date -u '+%Y-%m-%dT%H:%M:%SZ'
```

时间窗口 = `[现在 - 24h, 现在]`，按北京时间表达给用户。
**绝不要假设是 05:00 或其他固定时间**。

> 如果用户说的是"昨天的 AI 动态"，窗口仍然是过去 24h（不要回退到日历昨天）。如果用户说"过去 48 小时"，则扩展窗口。

### Step 2：181 源全覆盖调度（v5.1 核心改造）

**v5.1 承诺**：181 个源全部点名，每个都有明确状态。但**抓的方式按源类型分发**——不是 181 次单 fetch（token 爆表），而是混合 fetch + 批量 search。

#### Step 2.1 · 按源类型分发抓取策略

```
类型 A · 单 fetch（信息密度高，结构清晰）
  适用：Tier 1 一线媒体首页 / Tier 2 大厂博客 / 部分 Tier 4 中文媒体
  约 ~50 个源 → 50 次 fetch
  注：每次 fetch 约 5K tokens

类型 B · 单 search "[源名] May 12 2026"
  适用：Tier 0 Karpathy 精选 / Tier 3 分析师 / Substack 系
  约 ~35 个源 → 35 次 search
  注：每次 search 约 2K tokens

类型 C · 批量 search（5-10 个源一组）
  适用：Tier 5 Karpathy 其余 74 个 / Tier 6 聚合 8 个
  约 ~12 个批量查询覆盖 82 个源
  例：site:filfre.net OR site:matklad.github.io OR ... May 12 2026

类型 D · 技术不可达，标记 + search 兜底
  适用：心智君公众号 / 红杉公众号 / 部分 Substack
  约 ~10 个源 → 各 1 次 search 兜底
  注：输出时明确标记 "❌ 技术不可达"

预计总调用数：50 + 35 + 12 + 10 = 107 次
Token 预算：约 35-45 万,在 Claude.ai 单对话限制内
```

#### Step 2.2 · 八批次执行顺序

```
批次 1（Tier 0 Karpathy 精选 18 源,扩窗 7 天）
  - simonwillison / gwern / dwarkesh / wheresyoured / garymarcus / minimaxir
  - antirez / mitchellh / geoffreylitt / steveblank / paulgraham / pluralistic
  - anildash / lcamtuf / joanwestenberg / experimental-history / derekthompson / daringfireball
  抓法：simonwillison 单 fetch（信息最密）；其他 14 个用 search "[name] AI May 2026"
  结束自检：报告 "Tier 0 抓 X/18,命中 Y 篇深度长文"

批次 2（Tier 1 企业核心 22 源,严格 24h）
  - 6 财经（The Information/Bloomberg/Reuters/FT/Fortune/WSJ）单 fetch
  - 8 咨询商学院（McKinsey/BCG/Bain/Deloitte/PwC/Accenture/HBR/Sloan）单 fetch
  - 6 科技媒体（TC/VB/Verge/MIT TR/Ars/Wired）单 fetch
  - 2 VC（a16z/Sequoia）单 fetch
  结束自检：报告 "Tier 1 抓 X/22,命中 Y 篇"

批次 3（Tier 2 大厂博客 22 源,严格 24h）
  - v4 原 14：Anthropic/OpenAI/DeepMind/Google AI/Microsoft AI/MS Research/AWS ML/
    Salesforce/Databricks/Snowflake/ServiceNow/Meta AI/HF/Mistral
  - v5 新增 8：Oracle/IBM/NVIDIA/Cisco/SAP News/Adobe/Workday/Cohere ⭐ 重点验证
  全部单 fetch（结构清晰）
  结束自检：报告 "Tier 2 抓 X/22,v5 新增 8 个命中 Y 个"

批次 4（Tier 3 独立分析师 12 源,严格 24h）
  - Stratechery/Latent Space/Import AI/Sebastian Raschka/Nathan Lambert/
    Pragmatic Engineer/One Useful Thing/Every/AI Snake Oil/Karpathy 博客/
    Lilian Weng/François Chollet
  Substack/个人博客用 search,其他用 fetch
  结束自检：报告 "Tier 3 抓 X/12,命中 Y 篇"

批次 5（Tier 4 国内中文 17 源,严格 24h）
  - v4 原 10：36kr/机器之心/量子位/智东西/新智元/雷锋网/钛媒体/InfoQ 中文/极客公园/虎嗅
  - v5 新增 7：界面/澎湃科技/未来智库/心智君/第一财经/证券时报/财新 ⭐ 重点验证
  - 心智君公众号 → 标记 ❌ 技术不可达 + search 兜底
  其余 fetch
  结束自检：报告 "Tier 4 抓 X/17,v5 新增 7 个命中 Y 个"

批次 6（Tier 4B 制造垂类 5 源 + Tier 4C 红杉系 3 源,严格 24h）
  - IndustryWeek/Manufacturing.net/SME/信通院/Automation.com - fetch
  - 红杉中国/红杉公众号/YC - 公众号 search,其他 fetch
  结束自检：报告 "Tier 4B/C 抓 X/8,命中 Y 篇（这两层频次极低,0 命中正常）"

批次 7（Tier 5 Karpathy 其余 74 源,严格 24h,批量 search）
  - 74 个个人技术博客 / 复古计算 / Linux 内核 / 历史随笔类
  - 按主题分组成 ~10 个批量 search：
    * "antirez OR redis blog May 12 2026 AI"
    * "lucumr OR overreacted OR matklad May 12 2026 AI"
    * "krebsonsecurity OR mjg59 OR troyhunt May 12 2026"
    * ... 等
  - 默认企业 AI 视角过滤，命中 0 是正常的（这层本来就是"工具箱"）
  结束自检：报告 "Tier 5 批量扫 X/74,罕见命中 Y 篇企业 AI 强相关"

批次 8（Tier 6 聚合源 8 源,严格 24h）
  - Ben's Bites / Rundown AI / TLDR AI / AlphaSignal / AI Hub Today / 
    AI Business / Axios AI / HN Buzzing
  全部单 fetch
  结束自检：报告 "Tier 6 抓 X/8"
```

#### Step 2.3 · 抓取覆盖率自检（v5.1 强制）

**每批次结束必须打印**：

```
═══════════════════════════════════════════
📊 抓取进度自检（批次 N 结束）
───────────────────────────────────────────
当前批次：Tier X · {层名}
本批 fetch/search 次数：N 次
本批已抓源：A/B（A=已抓的，B=本 Tier 总数）
本批 24h/7d 内命中文章：C 篇
本批 0 命中源：D 个
本批技术不可达：E 个
───────────────────────────────────────────
累计已抓源：X/181
累计文章池：Y 篇（去重前）
预计还需抓：Z 个源
═══════════════════════════════════════════
```

**强制规则**：
- 跑完批次 1-4 后，如果累计抓源 < 60，必须继续跑批次 5-8
- 跑完所有 8 批次前，**不允许进入 Step 3 去重 / Step 4 写早报**
- 如果某批次连续 3 个源 fetch 失败（403/JS-only/404），跳过该批次剩余 fetch 改用 search 兜底

### Step 3：抓取执行

按上面调度计划逐批跑。每抓完一批，记录到内部 todo：

```
✅ 第1批: The Information(3条), Bloomberg(2条), ...
✅ 第2批: McKinsey(1条新报告), BCG(0条), ...
...
```

如果某 Tier 1 源失败，**必须**用 web_search 兜底：
```
web_search "Bloomberg AI news past 24 hours"
web_search "The Information AI today exclusive"
```

### Step 4：三层去重 + 维度筛选 + 质量打分

**三层去重**：
1. **URL 完全匹配**——同一 URL 不重复
2. **标题指纹**——把标题去标点/去空格/小写后取前 50 字符，相同则视为重复（防同一事件被多家报道占多个名额）
3. **同事件聚合**——相似度高（标题主语+谓语+宾语三要素重合）的，保留权威度最高的那一篇

**权威度排序**（同事件保留谁）：
```
官方博客（OpenAI/Anthropic/Microsoft/Oracle/IBM/NVIDIA 等） >
The Information / Bloomberg / FT >
McKinsey / BCG / HBR >
Karpathy 精选 Tier 0(Simon Willison / Gwern / Dwarkesh 等) >
TC / VB / The Verge / MIT TR >
其他独立分析师 >
国内中文媒体 >
制造垂类 >
聚合源 >
Karpathy 其余 74 个个人博客
```

**质量打分**（每篇 4 维各 0-2 分，满分 8）：

| 维度 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|
| **时效** | > 24h | 12-24h | 12h 内 |
| **信息量** | 纯标题党/PR/转载 | 有内容但浅 | 含数据/独家/细节 |
| **企业相关性** | 学术/消费/无关 | 间接相关 | 直接服务企业 |
| **独特/权威** | 多源同报 + 小众 | 一般 | 独家 or 一线源原创 |

**通过门槛 ≥ 5/8**。低于的淘汰。

**维度配额执行**：
- 每维度按质量分降序选 N 篇
- 不足下限时**不降低门槛**，header 注明"X 维度仅 Y 篇过筛"
- 节省名额可分给其他维度，但单维度不超上限

### Step 5：翻译 + 打磨 + "📌 这意味着"

Claude 直接翻译，不调外部 API。

**标题翻译**：
- 保留专有名词原文：人名、公司名、产品名、模型名
  - ✅ `Anthropic 推出 Cowork：面向非技术用户的桌面 AI Agent`
  - ❌ `安瑟匹克推出"协作"...`
- 保留所有数字、主体、关键动词
- 中文长度 15-30 字

**摘要重写**：
- 长度：**120-150 字**（v4 略放宽，因为单次跑可以更精细）
- 结构：`【是什么】+【关键数据/细节】+【为什么值得企业关注】`
- 自检三问：
  1. 中国读者光看标题能否抓住核心？
  2. 数字/公司名/产品名是否准确？
  3. 是否过度意译丢失了关键信息？

**"📌 这意味着"短句（每篇 1 句）—— skill 的灵魂**：
- 长度：**30-50 字**
- 必须从**企业视角**写，回答"这事对部署 AI 的企业意味着什么"
- 例：
  - 产品发布：`📌 这意味着：B2B 客户现在能用上 GPT-4 级能力但只付一半成本，正在评估 OpenAI 企业版的公司可重新议价。`
  - 融资：`📌 这意味着：企业 Agent 赛道融资仍在加速，窗口正在收紧，传统 SaaS 厂商需在 6 个月内出对策。`
  - 监管：`📌 这意味着：欧盟 AI Act 落地细则使医疗/金融行业部署 AI 进入合规审计季。`
- ❌ 避免空话："未来可期"、"值得关注"、"行业新趋势"

**特殊处理**：
- 中文源**不翻译**，但仍要重写摘要（统一风格）+ 写"📌 这意味着"
- 翻译失败：标注「⚠️ 翻译失败」+ 保留英文，其他继续

### Step 6：输出 Markdown（详见第 4 章模板）

直接在 Claude.ai 对话内输出完整 Markdown。**同时用 `create_file` 写一份到 `/mnt/user-data/outputs/`** 让用户可以下载。

---

## 4. 输出格式（Markdown 模板）

````markdown
# 📰 同光 · 企业 AI 早报 | YYYY-MM-DD 周X

> 🕐 运行时刻：YYYY-MM-DD HH:MM (北京时间)
> 📅 时间窗口：过去 24 小时（Tier 1-6）+ 过去 7 天（Tier 0 深度参考层）
> 📊 文章数：N 篇（目标 30-50,按实际输出）
> 📡 **信源覆盖：181 / 181**（✅ 抓到 A 篇 / 🟡 已扫但 0 命中 B 个源 / ❌ 技术不可达 C 个源）
> ⭐ 平均质量分：X.X / 8.0

---

## 🌟 今日 Top 5

> 一眼看完最值得知道的 5 条

**1. [标题]**
[40-60 字一句话摘要]
📌 *这意味着：[30-50 字企业视角短句,必须含具体决策动作]*

**2. [标题]**
...

---

## 🧠 Tier 0 Karpathy 深度参考（v5.1 新增独立维度,扩窗 7 天）

> Tier 0 这层"每周 1-3 篇深度长文"特征,本节列过去 7 天的高价值长文,不算入主篇数。

### Karpathy-1. [标题]（[源] · YYYY-MM-DD,X 天前）

[60-80 字摘要,讲清楚作者的核心论点]
📌 *给企业的启发：[30-50 字,把作者的观点翻译成企业 AI 决策语言]*

### Karpathy-2. ...

---

## 🚀 企业级 AI 产品（11 篇）

### [1] [中文标题]

- **来源** ｜ [媒体名]
- **时间** ｜ X 小时前
- **质量分** ｜ X/8
- **链接** ｜ https://...
- **原标题** ｜ [英文原标题]

[120-150 字中文摘要]

📌 **这意味着**：[30-50 字]

---

### [2] ...

---

## 🏢 企业部署案例（7 篇）

...

## 💰 商业进展（6 篇）

...

## 👥 组织变革（5 篇）

...

## ⚙️ 基础设施 & 成本（5 篇）

...

## 📊 咨询研究（5 篇）

> v4 新增维度,专门承接 McKinsey/BCG/HBR/Sloan 等机构的报告与文章

### [25] McKinsey: 三分之二企业 AI 项目在第一年无法产生商业价值

- **来源** ｜ McKinsey QuantumBlack
- **时间** ｜ 8 小时前
- **质量分** ｜ 8/8
- **链接** ｜ https://www.mckinsey.com/...
- **原标题** ｜ The state of AI: Why two-thirds of enterprise AI initiatives fail in year one

最新调研覆盖全球 1,491 位高管,发现 67% 的企业 AI 项目在第一年无法产生可衡量商业价值,核心症结是「先工具后场景」式的部署逻辑。McKinsey 提出「场景反推架构」六步法,并指出 ROI 跑得通的企业有三个共同点:CXO 亲自督导、数据底座先行投入、绑定具体 KPI 而非泛泛"提效"。

📌 **这意味着**:正在做企业 AI 规划的公司,必须把「场景论证」和「数据底座」前置到 PoC 之前,否则大概率成为 67% 中的一员。

---

## ⚖️ 监管 & 风险（5 篇）

> ⚠️ 若某维度今日过筛不足下限,在此章节顶部注明,例如"本维度今日仅 2 篇过筛(下限 3 篇),原因:周末监管动态较少"。

...

---

## 📊 本日统计

- **维度分布**:产品 X / 案例 X / 商业 X / 组织 X / 基础设施 X / 咨询 X / 监管 X / 国内 X / 制造 X = N 篇
- **Tier 0 深度参考**:Y 篇（不算入主篇数）
- **质量分布**:8 分 X 篇 / 7 分 X 篇 / 6 分 X 篇 / 5 分 X 篇
- **信源 Top 5**:列出贡献最多文章的 5 个源

---

## 📡 信源覆盖摘要

> 简洁版审计——让你验证我查了哪些源。详细列表如需可单独索取。

| 状态 | 源数 |
|---|---|
| ✅ 直接命中（贡献文章到正文） | N 个源 |
| ✅ 间接命中（通过聚合源/媒体报道覆盖） | N 个源 |
| 🟡 已扫但 24h 内无强 AI 信号 | N 个源 |
| ❌ 技术不可达（已用 search 兜底） | N 个源 |
| **合计** | **181 / 181** |


---

*本期由 tongguang-ai-daily 生成 · Claude.ai 单次跑模式*
*运行时间：YYYY-MM-DD HH:MM 北京时间*
````

---

## 6. 异常处理矩阵（v5.1 扩充）

| 异常 | 处理 | 是否中止 |
|---|---|---|
| **Substack/Ghost 类源 fetch 返回 "需要 JS"** | **不重试，立即转 search 兜底**：`web_search "[源名] [日期] AI"` | 否 |
| **微信公众号源** | **默认 search 兜底**，不试 fetch（必然失败）：`web_search "[公众号名] [关键词]"` | 否 |
| **Ghost Explore 显示日期但无标题** | search "[作者名] [日期] AI" 兜底 | 否 |
| 单个 Tier 1 源失败 | web_search 兜底，写入日志 | 否 |
| 单个 Tier 2-5 源失败 | 跳过，写入日志，列入 "🟡 已扫但未抓到" 附表 | 否 |
| 连续 3 个源 fetch 失败（403/JS-only/404） | **跳过该 Tier 剩余 fetch，全部改用批量 search 兜底** | 否 |
| **某批次 token 预算告急** | 截止当前批次，输出"已抓 X/181"+ 部分早报，附"剩余未抓的 Y 个源"说明 | **是** |
| 抓取量 < 15 篇 | 深度兜底：多关键词 web_search "enterprise AI [day] [year]" / "AI funding today" / "McKinsey AI report" | 否 |
| 抓取量 < 8 篇 | 中止 + 输出"信号过弱"简要报告 | **是** |
| 某维度过筛 < 下限 | Header 注明，不降标准 | 否 |
| 翻译某篇失败 | 标注「⚠️ 翻译失败」+ 保留英文 | 否 |
| **跑到一半发现自己覆盖率 < 50%** | 强制回到 Step 2 继续抓，不允许进入 Step 3 写早报 | 否（自我纠正）|
| 用户中途打断 | 输出"已抓 N 篇,中止"的部分早报 | — |

---

## 4.5. "📌 这意味着"质量范例（v5.1 新增，强制对照）

每条新闻末尾的 "📌 这意味着" 必须 30-50 字 + 企业视角 + **带具体决策动作**。这是 skill 的灵魂部件，但容易写偏。下面是好/坏对照——写之前对照检查。

### ✅ 好的范例

| 新闻 | ✅ 好的 "这意味着" | 为什么好 |
|---|---|---|
| Vapi $50M Series B | "Voice AI 厂商的护城河已经从模型转移到延迟+治理基础设施，做 voice agent 的 CIO 评估时要把'亚 500ms 是否达标'写进 RFP" | 给出具体的采购评估指标 |
| Liveops 73% 偏好混合 | "CIO 立项 AI 项目时'组织准备度评估'必须前置到工具选型之前；销售 AI 产品的厂商要把话术从'替代人'换成'混合协作 + 治理透明'" | 同时给两类受众（甲方/乙方）的具体动作 |
| OpenAI tender offer | "AI 头部公司用周期性 tender 留人，企业评估'是否合作 OpenAI/Anthropic'时要把'核心人才稳定性'作为新变量纳入风险评估" | 把宏观现象翻译成企业决策清单上的新条目 |

### ❌ 坏的范例

| 新闻 | ❌ 坏的 "这意味着" | 为什么坏 |
|---|---|---|
| Vapi $50M Series B | "voice AI 资本从消费级转向企业" | 陈词滥调，没有新信息；任何看完标题的人都能想到 |
| PitchBook Q1 三巨头 67% | "AI 投融资马太效应" | 抽象判断，没给企业任何可执行动作 |
| SAP Sapphire 发布 | "AI Agent 正在改变 ERP" | 笼统，不需要看新闻也知道 |
| OpenAI DeployCo | "OpenAI 进军咨询" | 复述事实，没翻译成企业视角 |

### 📐 通过性自检（写完每条问自己）

1. **如果删掉这条"这意味着"，读者会损失什么决策信息？** 如果答案是"什么都不损失"，重写。
2. **能不能在 30 字内给出一个具体动作？** （如"评估时增加 XX 维度"、"采购流程加 XX 步骤"、"销售话术换 XX"、"团队架构调 XX"）
3. **是给"企业内某岗位"看的，还是给"行业旁观者"看的？** 早报是给 CXO/VP 看的，不是给媒体编辑看的。
4. **如果是同行已经知道的事，能不能给出"不一样的视角"？** 比如 OpenAI tender 大家都看到了，"这意味着核心人才稳定性变量" 是个新视角。

---



```
用户:跑一下同光早报
→ 按本 SKILL 完整流程,输出 30-40 篇 Markdown 早报

用户:跑下今天的 AI
→ 同上

用户:看看昨天 AI 圈发生了什么
→ 同上

用户:只跑咨询研究维度
→ 仅抓 Tier 1 的咨询/商学院 8 源,输出 8-15 篇

用户:跳过国内媒体
→ 跳过 Tier 4,其他正常

用户:加强企业部署案例,要 15 篇
→ 把案例维度上限提到 15,优先抓 McKinsey/BCG/HBR 的案例文章

用户:把质量门槛降到 4 让我看更多
→ 临时调阈值重跑(放宽筛选)

用户:今天信号太弱,补几篇上周漏掉的
→ 把时间窗口扩到 7 天,但每篇标注"补遗"

用户:输出能下载的 markdown 文件
→ 用 create_file 写到 /mnt/user-data/outputs/早报-YYYY-MM-DD.md
```

---

## 7. 上下游

```
64+ 信源 (sources.json)
      ↓
tongguang-ai-daily (本技能,在 Claude.ai 对话内单次跑)
      ↓
- 对话内 Markdown 早报
- /mnt/user-data/outputs/早报-YYYY-MM-DD.md (可下载)
      ↓
(未来) ai-topic-planner (选题策划) → ai-article-writer (文章撰写)
```

**本技能不做的事**:
- 自动定时(v3.2 是 Routine 自动化版本,v4 暂不做)
- 深度研究 → `case-deep-research`
- 单家公司研究 → `company-research`
- 单事件追踪 → `hotspot-tracker`
- AI 报告周/月度扫描 → `ai-report-radar`
- 全球商业案例雷达 → `global-case-radar`

**本技能必须做的事**:每次手动触发,产出一份 30-50 篇企业 AI 资讯早报(按实际输出),翻译好、有"📌 这意味着"、可追溯、**181 源全覆盖审计**。

---

## 8. 版本演进

| 版本 | 关键变化 |
|---|---|
| v1.0 | 初版,6 维度均分,URL 去重,英文保留,名为 `ai-article-collector` |
| v2.0 | 三层去重、软配额、质量打分、CSV+飞书同步 |
| v3.0 | 聚焦企业 AI / 加入 Twitter 维度 / 删除飞书+CSV / Top 5 摘要 |
| v3.1 | 改名 tongguang-ai-daily,绑定品牌 |
| v3.2 | Anthropic Routine 部署版本(自动化) |
| v4.0 | Claude.ai 单次跑专用 / 信源扩充至 64 / 新增「咨询研究」维度 / 整合国内中文媒体 / 整合 McKinsey/BCG 等咨询 / 整合财经源 / 整合企业大厂 AI 博客 |
| v5.0 | 全量纳入 Karpathy 2026/01 推荐的 92 信源 + 新增 Tier 0 Karpathy 精选 18 个 + 8 大厂 + 7 国内中文 + 3 研究者 + 5 制造垂类 + 3 红杉系 = 总 181 源,目标 60 篇按实际输出 |
| **v5.1** | **跑了两次 v5 后的真实迭代:① 181 源全覆盖承诺 + 全覆盖审计区 ② Tier 0 扩窗 7 天 + 独立深度参考维度 ③ Substack/微信公众号源类型分发抓取策略 ④ 8 批次执行 + 强制覆盖率自检 ⑤ "📌 这意味着"好/坏范例对照 ⑥ 目标 30-50 按实际输出(从 60 校准) ⑦ 异常处理矩阵扩充(JS-only / token 告急 / 自我纠正)** |

---

## 9. v5.0 → v5.1 关键变化（真实跑过两次后的迭代）

| 问题（v5 实际跑发现的） | v5.0 | v5.1 修复 |
|---|---|---|
| **抓取覆盖率不可见** | 跑完了不知道自己跑了多少 | 强制每批次结束打印 "已抓 X/181" 自检 |
| **Tier 0 24h 内常 0 命中** | Tier 0 跟其他 Tier 一样 24h 窗口,但这层每周 1-3 篇 | **Tier 0 扩窗 7 天**,且新增独立维度 "🧠 Tier 0 深度参考" |
| **Substack 抓不到正文** | SKILL 没指引,Claude 反复尝试 fetch 失败 | 明确：**Substack 系直接 search 兜底**,不试 fetch |
| **微信公众号反复试 fetch** | 同上 | 明确：**微信公众号默认 search 兜底** |
| **v5 新增 28 源 0 利用率** | 跑的时候没有"必试这些新源"的提示 | 8 批次执行计划里**逐 Tier 强制覆盖**,新增源在批次描述里点名 |
| **"📌 这意味着"陈词滥调** | 只说 "30-50 字 + 企业视角" | 新增 5.5 节,4 组好/坏对照范例 + 4 条通过性自检 |
| **目标 60 实际 17-22 差距大** | 目标 60 按实际输出,但落差 65% | 校准成 **30-50 按实际输出**,区分弱/强/爆发日 |
| **Tier 0 当日 0 命中下结论太早** | 抓 4 个 Tier 0 源就下结论 | 8 批次执行强制覆盖全 18 个 Tier 0 |
| **Token 预算无管理** | 跑到一半可能爆 | 异常矩阵新增 "token 告急时截止当前批次+输出部分" 规则 |
| **审计区缺失** | 输出里看不到哪些源抓了、哪些没抓 | **新增"📡 信源全覆盖审计"独立章节**,每 Tier 都列状态 |

---

## 10. 跑这个 skill 时,Claude 必须做的事（v5.1 升级）

1. **不要凭记忆补充新闻**——每条都必须来自实际 web_fetch/web_search 的结果,并附原文链接。
2. **不要写"业内人士透露"式的伪报道**——所有数字、引语都要有来源。
3. **不要把多条相似新闻拆成多条**——同一事件聚合到最权威那一篇。
4. **不要省略"📌 这意味着"**——这是 skill 的灵魂,每篇必须有,且必须通过 5.5 节的通过性自检。
5. **不要把质量门槛降到 5 以下凑数**——宁缺毋滥仍然是底线。
6. **必须用 create_file 输出 markdown 文件**——方便用户下载,不只是在对话里输出。
7. **必须显示进度**——按 Step 2.3 的格式每批次结束打印自检,告诉用户 "Tier X 抓 Y/Z,继续中..."。
8. **Tier 0 扩窗 7 天,独立维度展示**——不再是脚注,是早报正文的第二大块（仅次于 Top 5）。
9. **Tier 5 Karpathy 其余 74 源必须批量 search 覆盖**——不是"默认不抓",是"批量扫一遍,过滤后命中 0 也要在审计区写明"。
10. **目标 30-50 按实际输出**——header 里诚实说明信号强弱,Top 5 永远要有,审计区永远要有。
11. **181 源全覆盖审计是硬要求**——输出末尾必须含完整审计表,证明 181 个源每个都被点名。
12. **token 预算管理**——如果跑到批次 5-6 发现 token 告急,立即截止后续批次 + 输出部分早报 + 在审计区明列"未抓完的源",而不是含糊处理。
13. **抓取覆盖率 < 50% 时强制回到 Step 2**——不允许进入 Step 3 去重 / Step 4 写早报。这是 v5.1 的关键约束。
14. **❌ 早报正文严格禁止"开发噪音"**——以下内容**永远不能出现在早报里**，无论用户感觉多想看：
    - 版本对比表（v5.1 vs v5 vs v4 篇数/质量/工具调用次数）
    - 跑法说明（C 方案 / B 方案 / Tier 0+1+2+3 逐个抓的策略选择）
    - SKILL 迭代日志（"这次多挖到 X 条 vs 上次"）
    - 工具调用统计（"~28 次 search vs v5 的 ~12 次"）
    - 元洞察（"我学到了 X" / "下次应该 Y"）
    - 任何指向 Claude 自身工作流程的反思
    
    早报是给用户读新闻+洞察用的，不是给开发者读迭代笔记用的。**这些信息如果有价值，只能放在对话里给用户回复时讲，不能写进 markdown 文件**。一句话原则：**早报 markdown 里只该有"昨天发生了什么 + 这对企业意味着什么 + 来自哪里"，其他一切都是噪音**。
15. **信源覆盖审计区可以保留**——但要从"开发证据"重新定位为"质量保证"。审计区在早报底部以**简洁版**呈现（最多 30 行），核心是让用户验证"哪些源你查了"，**不要长篇展示每个源的细节状态**——展示 4 类汇总即可（✅ 直接命中 N 个 / ✅ 间接命中 N 个 / 🟡 已扫无命中 N 个 / ❌ 技术不可达 N 个 = 总 181）。**展开的详细审计列表只在用户要求"给我看完整审计"时单独输出**。

---

## 11. v5.2 备注：跑过三次 v5/v5.1 后的元洞察（待下一版迭代）

> 本节是 2026-05-13 这天连续跑了 v4 / v5 / v5.1 第一版 / v5.1 终版（C 方案）共四次后总结的真实规律。
> 是 SKILL v5.2 的改造起点，**v5.1 跑的时候本节内容仅作参考，不强制执行**。

### 11.1 真实规律：181 源里"每日有信号"的只有 ~15-20 个

跑了四次后的真实统计：

| Tier | 名义源数 | 每日真实有信号的源数 | 命中率 |
|---|---|---|---|
| Tier 0 Karpathy 精选 | 18 | 1-3（扩 7 天窗 5-8） | ~10% |
| Tier 1 财经 + 一线媒体（6+6） | 12 | 4-7 | ~50% |
| Tier 1 咨询商学院 | 8 | 0-1（年度报告周期） | ~5% |
| Tier 1 VC | 2 | 0 | 0% |
| Tier 2 大厂博客（22） | 22 | 3-6（看有无 release） | ~20% |
| Tier 3 分析师（12） | 12 | 1-3 | ~15% |
| Tier 4 国内中文（17） | 17 | 1-3 | ~10% |
| Tier 4B 制造垂类（5） | 5 | 0-1 | ~5% |
| Tier 4C 红杉系（3） | 3 | 0 | 0% |
| Tier 5 Karpathy 其余（74） | 74 | 0（"工具箱"定位） | 0% |
| Tier 6 聚合（8） | 8 | **1-2 高价值聚合源** | ~25% |
| **真正"每日有信号"** | | **~15-20 个核心源** | |

**结论**：181 源全覆盖审计是对的，但**真正决定早报质量的是这 ~15-20 个核心高频源**。其他 160+ 个源是"周/月级深度参考"或"工具箱备份"。

### 11.2 聚合源（BitDigest / Innermost Loop / Ben's Bites）应升级为"Tier 0.5"

跑 v5.1 终版时的最大意外发现：

> **5/12 这天最大的"信号杠杆"来自两条聚合源**——BitDigest 5/12 + Innermost Loop 5/12，**每条聚合源一次 search 就覆盖了 10-15 条当日重磅**，效率远高于逐个抓 Tier 1-2。

具体数据：v5.1 终版的 43 篇里，~25 篇是通过这两条聚合源 + 顺藤摸瓜的定向 search 得到的，**实际原始 fetch 大厂博客只贡献了 ~6 篇**。

**v5.2 建议**：把 BitDigest（每日"Daily AI Brief"格式）/ Innermost Loop（每日 "Welcome to MM-DD" 格式）从 Tier 6 单独抽出，命名 **Tier 0.5 "高密度聚合源"**，作为 Step 2.1 第一批必抓（在 Tier 0 之前），这样能用 1-2 次 search 先把当日 80% 重磅"地图"画出来，后续 Tier 1-3 fetch 变成"定向补全"而非"盲扫"。

### 11.3 跑早报的最优顺序（v5.2 应改成）

v5.1 当前顺序：Tier 0 → Tier 1 → Tier 2 → Tier 3 → ... → Tier 6

**v5.2 建议顺序**：
```
1. Tier 0.5 高密度聚合源（2-3 次 search）   ← 先画地图,识别当日"重磅清单"
2. 对清单上每条重磅做定向 search（5-10 次） ← 补全细节、找最权威原始报道
3. Tier 0 Karpathy 7 天窗口（5-8 次 search）← 抓深度思考长文
4. Tier 1-2 一线媒体 + 大厂博客（按清单补漏） ← 检查清单外漏掉的
5. Tier 3 分析师 newsletter（看是否有独立长文）
6. Tier 4-6 batch search 覆盖审计
```

预期效果：**~30 次工具调用就能达到 v5.1 终版 ~85 次调用的覆盖度**，token 预算松一大半，留更多给写早报和"📌 这意味着"质量。

### 11.4 sources.json 需要新增的 Tier 0.5 候选

跑 v5.1 时验证有效的聚合源（按当日命中密度排名）：

| 候选源 | URL | 当日命中密度 | 备注 |
|---|---|---|---|
| Innermost Loop (Alex Wissner-Gross) | https://theinnermostloop.substack.com | ⭐⭐⭐ 极高（每日 12+ 条） | "Welcome to MM-DD" 格式日报,Substack 抓不到首页但 search 命中标题 |
| BitDigest (Greg Landegger) | https://bitdigest.substack.com | ⭐⭐⭐ 极高（每日 10+ 条） | 简洁链接列表,通过 search 命中具体周几 |
| The Rundown AI | https://www.therundown.ai | ⭐⭐ 中（每日 5-8 条） | 已在 Tier 6,留在原位 |
| Ben's Bites | https://www.bensbites.com | ⭐⭐ 中 | 同上 |
| TLDR AI | https://tldr.tech/ai | ⭐ 低 | 短摘要,深度不够 |
| AlphaSignal | https://alphasignal.ai | ⭐ 低 | 偏研究,企业 AI 视角弱 |

**v5.2 调整方案**：
- BitDigest + Innermost Loop → **新设 Tier 0.5 "高密度聚合源"**（必须用 search "[源名] May DD 2026" 形式抓，因为 Substack 首页 fetch 不到）
- 其他保留在 Tier 6

### 11.5 信号强度日历（识别"该跑什么模式"）

跑 v5.1 终版时发现：**5/12 是强信号日，但很多日子不是**。v5.2 应在 Step 0 加一个"信号强度预判"动作：

| 日期类型 | 预期信号强度 | 跑法 |
|---|---|---|
| OpenAI DevDay / Google I/O / NVIDIA GTC / SAP Sapphire / 大厂年度发布 | 爆发日（70-100 篇可能） | 全覆盖 + 加大维度配额 |
| 重大监管/法庭披露日（如 5/12 Ilya/blackmail/zero-day 三合一） | 强信号日（40-60 篇） | C 方案逐个抓 Tier 0+1+2+3 |
| 普通工作日 | 中信号（25-40 篇） | 简化版：Tier 0.5 聚合 + Tier 1-2 定向 |
| 周末/节假日 | 弱信号（10-25 篇） | 极简：Tier 0.5 + Tier 0 扩窗，宁缺毋滥 |

**判断方法**：跑 Step 0 时先抓 Tier 0.5 聚合源做信号强度评估，根据聚合源当日条目数动态调整后续抓取规模。

### 11.6 "📌 这意味着" 的另一层质量标准（v5.2 加入 4.5 节）

跑 v5.1 终版时发现，最受用户欢迎的"这意味着"具备一个共同特征：

> **同时给"甲方/买方/CIO"和"乙方/卖方/AI 厂商"两类受众的具体动作**。

例如：
- ✅ Liveops 73% 偏好混合那条："**CIO** 立项时'组织准备度评估'前置；**销售 AI 产品的厂商**话术换成'混合协作 + 治理透明'"
- ✅ Hashimoto TDM 金句那条："**AI 工具 RFP** 强调'低失败率 + 可解释 + 备选方案'，而非极客早期采用者那套话术"

**v5.2 4.5 节加一条自检**：第 5 条通过性自检——"这条意味着是不是同时给买方和卖方两类受众的具体动作？如果只给一方，能不能补另一方？"

### 11.7 "覆盖率 vs 价值"权衡（v5.2 应明确）

跑 v5.1 终版后明确：**74/74 全点名审计是有价值的，但代价是 ~85 次调用**。值不值得，取决于使用场景：

| 使用场景 | 推荐版本 |
|---|---|
| 个人快速浏览（早晨 5 分钟） | **极简版**：只跑 Tier 0.5 聚合 + Top 5（~3 次调用） |
| 团队周会素材（半小时阅读） | **标准版**：Tier 0+1+2+3 关键源（~20 次调用，30 篇） |
| 客户/CXO 简报底稿（要可追溯） | **C 方案完整版**：Tier 0+1+2+3 全点名（~30-50 次调用，40 篇 + 审计） |
| 季度复盘 / 趋势分析素材 | **全覆盖版**：181 源全跑（~80-100 次调用，强信号日 70+ 篇） |

**v5.2 建议**：SKILL 头部加"使用场景判断"，让用户在跑之前选挡位，而不是默认全力跑。

### 11.8 v5.2 改造任务清单（下次新对话时执行）

1. ☐ 把 BitDigest + Innermost Loop 从 Tier 6 抽出，新设 Tier 0.5
2. ☐ Step 2.1 加入"Tier 0.5 先跑"作为第一批
3. ☐ Step 0 加入"信号强度预判 → 选挡位"动作
4. ☐ 4.5 节加第 5 条通过性自检（甲乙双方都给动作）
5. ☐ SKILL 头部加"四档使用场景"
6. ☐ 11.4 表里的命中密度数据写入 sources.json `_meta` 段
7. ☐ 异常矩阵新增 "Tier 0.5 抓不到时 → 直接进 Tier 1 一线媒体 + 加强 search 频次"
8. ☐ README 同步更新到 v5.2
9. ☐ **早报正文严格清除开发噪音**（v5.1 跑过的版本对比表 / 跑法说明 / 工具调用统计 / 元洞察 → 全部移到对话里讲,不进 markdown）
10. ☐ **审计区简化到 30 行摘要表**（详细列表只在用户索取时单独输出）

---

*v5.2 备注末尾：这一节是 v5.1 终版（2026-05-13 C 方案）跑完后的真实迭代积累。*
*下次新开对话跑 v5.2 时，本节的元洞察就是 SKILL 改造的起点。*
