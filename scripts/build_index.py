#!/usr/bin/env python3
"""
同光早报 · 索引构建脚本

输入: reports/YYYY-MM-DD.md (Claude Routine 写的早报 markdown)
输出: docs/data/index.json (前端用的标准化索引)

JSON 结构:
{
  "meta": {
    "generated_at": "2026-05-14T12:00:00Z",
    "total_reports": 30,
    "total_articles": 1200,
    "date_range": ["2026-04-15", "2026-05-14"]
  },
  "reports": [
    {
      "date": "2026-05-14",
      "weekday": "周四",
      "signal_strength": "medium",  // strong/medium/weak
      "main_count": 37,
      "tier0_count": 4,
      "summary": "Anthropic 客户超 OpenAI / ...",  // 取 Top 5 第一条标题
      "url": "reports/2026-05-14.md"
    }
  ],
  "articles": [
    {
      "id": "20260514-001",
      "date": "2026-05-14",
      "is_top5": true,
      "is_tier0": false,
      "dimension": "🚀 产品",  // 或 "🏢 案例"/"💰 商业"/...
      "title": "Anthropic 企业客户数首次超越 OpenAI...",
      "summary": "Ramp 最新 AI 指数...",
      "meaning": "正在续签企业 AI 合同的采购方...",  // "📌 这意味着" 的内容
      "source": "Ramp",
      "quality_score": 8,  // 5-8
      "url": "原文链接",
      "companies": ["Anthropic", "OpenAI", "Ramp"],
      "keywords": ["企业 AI", "Ramp 指数"]
    }
  ],
  "tag_index": {
    "dimensions": { "🚀 产品": 12, "🏢 案例": 18, ... },
    "companies": { "Anthropic": 15, "OpenAI": 12, "SAP": 5, ... },
    "signal_days": { "strong": 5, "medium": 18, "weak": 7 }
  }
}
"""

import json
import re
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter


# ═══════════════════════════════════════════════════════════════════════
# 常量配置
# ═══════════════════════════════════════════════════════════════════════

REPORTS_DIR = Path("reports")
OUTPUT_FILE = Path("docs/data/index.json")

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 早报里的维度标签(根据 SKILL v5.1 的 8 个维度)
DIMENSION_PATTERNS = {
    "🚀 产品":        [r"🚀\s*企业级?\s*AI\s*产品", r"##\s*🚀"],
    "🏢 案例":        [r"🏢\s*企业\s*部署?\s*案例", r"##\s*🏢"],
    "💰 商业":        [r"💰\s*商业\s*进展", r"##\s*💰"],
    "👥 组织":        [r"👥\s*组织\s*变革", r"##\s*👥"],
    "⚙️ 基础设施":     [r"⚙️\s*基础设施", r"##\s*⚙️"],
    "📊 咨询":        [r"📊\s*咨询\s*研究", r"##\s*📊"],
    "⚖️ 监管":        [r"⚖️\s*监管", r"##\s*⚖️"],
    "🇨🇳 国内":       [r"🇨🇳\s*国内", r"##\s*🇨🇳"],
    "🛠 工具与开源":  [r"🛠\s*工具与开源", r"##\s*🛠"],
    "🧠 Tier 0":     [r"🧠\s*Tier\s*0", r"##\s*🧠"],
}

# 信号强度识别
SIGNAL_PATTERNS = {
    "strong": [r"\[strong-signal\]", r"强信号日", r"信号强度[::]\s*强"],
    "medium": [r"\[medium-signal\]", r"中等信号", r"信号强度[::]\s*中"],
    "weak":   [r"\[weak-signal\]", r"弱信号日", r"信号强度[::]\s*弱"],
}

# 高频公司名(用来"自动提取关键公司"——白名单方式比 NER 简单可靠)
KNOWN_COMPANIES = [
    # 美国大厂 AI
    "Anthropic", "OpenAI", "Google", "DeepMind", "Microsoft", "Meta",
    "Amazon", "AWS", "Apple", "NVIDIA", "Cohere", "Mistral",
    "Hugging Face", "Databricks", "Snowflake", "Salesforce", "Oracle",
    "IBM", "Cisco", "SAP", "Adobe", "Workday", "ServiceNow",
    # AI 创业
    "xAI", "Perplexity", "Vapi", "C3 AI", "Stripe", "Shopify",
    "Datadog", "Sentry", "Lovable", "Tomoro", "Cerebras",
    "MoonPay", "Dawn Labs", "Isomorphic Labs", "Thinking Machines",
    "Cowboy Space", "White Circle",
    # 咨询机构
    "McKinsey", "BCG", "Bain", "Deloitte", "PwC", "Accenture",
    "Harvard", "MIT", "Stanford",
    # 国内
    "字节", "阿里", "腾讯", "百度", "华为", "讯飞", "智谱", "Moonshot", "DeepSeek",
    "Kimi", "通义", "豆包", "文心", "混元", "Pangu", "盘古",
    # 投资
    "WSJ", "Bloomberg", "Reuters", "FT", "TechCrunch", "Stratechery",
    "Simon Willison", "Karpathy", "Ed Zitron", "Gary Marcus",
    "Dwarkesh", "Hashimoto", "Tobias Lütke", "Ilya Sutskever",
    "Sam Altman", "Dario Amodei", "Mira Murati",
    # 其他
    "Mythos", "Daybreak", "Joule", "Constitution", "Bedrock",
    "DeployCo", "Glasswing", "Project Glasswing",
    "Vapi", "Ring", "Sentinel", "Fabric", "Sapphire",
    "PitchBook", "Liveops", "Hyperight", "GitLab",
]


# ═══════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════

def detect_signal_strength(content: str) -> str:
    """从早报头部识别信号强度"""
    head = content[:1500]
    for sig, patterns in SIGNAL_PATTERNS.items():
        for p in patterns:
            if re.search(p, head, re.IGNORECASE):
                return sig
    return "medium"  # 默认中等


def extract_number(content: str, pattern: str, default: int = 0) -> int:
    """提取 N 篇主报告这种数字"""
    m = re.search(pattern, content)
    if m:
        try:
            return int(m.group(1))
        except (ValueError, IndexError):
            return default
    return default


def extract_companies(text: str) -> list:
    """从文本里识别出现的已知公司名"""
    found = []
    seen = set()
    for company in KNOWN_COMPANIES:
        if company.lower() in text.lower() and company not in seen:
            found.append(company)
            seen.add(company)
    return found


def split_into_dimensions(content: str) -> dict:
    """
    把早报 markdown 按维度章节切开。
    返回 {dimension_name: section_text}
    """
    # 找到所有 ## 标题位置
    lines = content.split('\n')
    sections = {}
    current_dim = None
    current_lines = []

    # 维度匹配——优先精确匹配 emoji + 名字
    dim_regex = re.compile(r'^##\s+(🚀|🏢|💰|👥|⚙️|📊|⚖️|🇨🇳|🛠|🧠|🌟).*', re.UNICODE)

    for line in lines:
        m = dim_regex.match(line)
        if m:
            # 保存上一节
            if current_dim:
                sections[current_dim] = '\n'.join(current_lines)
            # 解析这一节是哪个维度
            head_emoji = m.group(1)
            current_dim = None
            for name in DIMENSION_PATTERNS:
                if name.startswith(head_emoji):
                    current_dim = name
                    break
            if current_dim is None:
                current_dim = line.strip('# ').strip()
            current_lines = []
        else:
            if current_dim:
                current_lines.append(line)

    if current_dim:
        sections[current_dim] = '\n'.join(current_lines)

    return sections


def parse_articles(content: str, date_str: str) -> list:
    """
    解析早报里的所有文章条目。
    
    早报里文章的格式有两种:
    1. Top 5 区: **1. ⭐ 标题** \n 摘要 \n 📌 *这意味着:...*
    2. 维度章节里: ### [N] 标题 \n - 来源/时间/质量分 \n 内容 \n 📌 **这意味着**:...
    
    都要解析出来。
    """
    articles = []
    sections = split_into_dimensions(content)

    counter = 1

    # === 解析 Top 5(在 "🌟 今日 Top 5" 章节) ===
    top5_section = sections.get("🌟 今日 Top 5") or ""
    # 也可能写法是 "🌟 今日 Top 5(N 篇)" 这种带括号——再扫一遍找 🌟 开头的 key
    if not top5_section:
        for k, v in sections.items():
            if k.startswith("🌟"):
                top5_section = v
                break

    top5_pattern = re.compile(
        r'\*\*(\d+)\.\s+([^*]+)\*\*\s*\n(.*?)(?:\n📌\s*\*?这意味着[::]?\s*([^*\n]+)\*?|\n---|\Z)',
        re.DOTALL
    )
    for m in top5_pattern.finditer(top5_section):
        rank, title, summary, meaning = m.groups()
        summary_text = (summary or "").strip()

        # ⭐ 修复 #1:Top 5 也提取链接(多种格式)
        url = ""
        url_match = re.search(r'\*\*链接\*\*\s*[\|｜]\s*(https?://\S+)', summary_text)
        if url_match:
            url = url_match.group(1).rstrip('.,)]')
        else:
            md_link = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', summary_text)
            if md_link:
                url = md_link.group(2)
            else:
                bare_url = re.search(r'https?://[^\s)）】」\]"\'<>]+', summary_text)
                if bare_url:
                    url = bare_url.group(0).rstrip('.,)]》。、，；;')

        article = {
            "id": f"{date_str.replace('-', '')}-T{rank.zfill(2)}",
            "date": date_str,
            "is_top5": True,
            "is_tier0": False,
            "dimension": "🌟 Top 5",
            "title": title.strip(),
            # ⭐ 修复 #2:摘要从 300 字符增加到 600 字符(扩大 1 倍)
            "summary": summary_text[:600],
            "meaning": (meaning or "").strip()[:400] if meaning else "",  # meaning 也从 200 加到 400
            "source": "",
            "quality_score": 8,
            "url": url,
            "companies": extract_companies(title + " " + (summary or "")),
            "keywords": [],
        }
        articles.append(article)
        counter += 1

    # === 解析维度章节里的文章 ===
    dim_pattern = re.compile(
        r'###\s+(?:\[(\d+)\]|K-(\d+)\.|Karpathy-(\d+)\.)\s*(.+?)(?=\n)',
        re.UNICODE
    )

    # 文章详情提取
    article_pattern = re.compile(
        r'###\s+(?:\[(\d+)\]|K-?(\d+)\.|Karpathy-(\d+)\.)\s*(.+?)\n+'  # 标题
        r'(?:[-*]\s*\*\*来源\*\*\s*[\|｜]\s*([^\n]+?)(?:\n|$))?'         # 来源
        r'.*?'                                                            # 中间各种元数据
        r'(?:\*\*质量分\*\*\s*[\|｜]\s*(\d+)/8)?'                         # 质量分
        r'.*?'                                                            # 中间内容
        r'(?:📌\s*\*?\*?这意味着[::]?\*?\*?\s*[::]?\s*([^📌\n#]+?)(?=\n|📌|$|---))',
        re.DOTALL
    )

    for dim_name, dim_text in sections.items():
        if dim_name == "🌟 今日 Top 5":
            continue

        is_tier0 = dim_name.startswith("🧠")

        # 简化版:按 ### 切分,然后逐块解析
        sub_articles = re.split(r'\n(?=###\s+)', dim_text)
        for chunk in sub_articles:
            if not chunk.strip().startswith("###"):
                continue

            # 提取标题
            title_match = re.match(r'###\s+(?:\[\d+\]|K-?\d+\.|Karpathy-\d+\.)\s*(.+?)(?:\n|$)', chunk)
            if not title_match:
                continue
            title = title_match.group(1).strip()

            # 提取来源
            source_match = re.search(r'\*\*来源\*\*\s*[\|｜]\s*([^\n│｜|]+?)(?:[\|｜│]|\n)', chunk)
            source = source_match.group(1).strip() if source_match else ""

            # 提取质量分
            score_match = re.search(r'\*\*质量分\*\*\s*[\|｜]\s*(\d+)\s*/\s*8', chunk)
            quality = int(score_match.group(1)) if score_match else 6

            # 提取"这意味着"
            meaning_match = re.search(
                r'📌\s*\*?\*?这意味着[::]?\*?\*?\s*[::]?\s*([^📌\n#]+?)(?=\n|---|$)',
                chunk
            )
            # ⭐ meaning 也保留完整,不截断
            meaning = meaning_match.group(1).strip().rstrip('*。.') if meaning_match else ""

            # 提取主要内容(去除元数据行,留正文)
            body = chunk.split('\n')
            content_lines = []
            for line in body[1:]:  # 跳过标题行
                if re.match(r'^[-*]\s*\*\*[来源时间质量分维度链接]', line):
                    continue
                if line.startswith('📌'):
                    break
                if line.strip():
                    content_lines.append(line.strip())
            # ⭐ 修复 #2:摘要从 400 字符增加到 800 字符(扩大 1 倍)
            summary = ' '.join(content_lines)[:800]

            # ⭐ 修复 #1:提取链接——支持多种格式
            # 优先级 1: **链接** | URL 这种显式标注
            url = ""
            url_match = re.search(r'\*\*链接\*\*\s*[\|｜]\s*(https?://\S+)', chunk)
            if url_match:
                url = url_match.group(1).rstrip('.,)]')
            else:
                # 优先级 2: markdown 链接格式 [text](url)
                md_link = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', chunk)
                if md_link:
                    url = md_link.group(2)
                else:
                    # 优先级 3: 裸 URL 直接出现
                    bare_url = re.search(r'https?://[^\s)）】」\]"\'<>]+', chunk)
                    if bare_url:
                        url = bare_url.group(0).rstrip('.,)]》。、，；;')

            article = {
                "id": f"{date_str.replace('-', '')}-{str(counter).zfill(3)}",
                "date": date_str,
                "is_top5": False,
                "is_tier0": is_tier0,
                "dimension": dim_name,
                "title": title,
                "summary": summary,
                "meaning": meaning,
                "source": source,
                "quality_score": quality,
                "url": url,
                "companies": extract_companies(title + " " + summary),
                "keywords": [],
            }
            articles.append(article)
            counter += 1

    return articles


def get_top_title(articles: list) -> str:
    """取 Top 5 第一条作为早报摘要(无 Top 5 则取第一条文章)"""
    for a in articles:
        if a.get("is_top5") and a.get("id", "").endswith("T01"):
            return a["title"][:80]
    if articles:
        return articles[0]["title"][:80]
    return ""


def parse_report(md_path: Path) -> tuple:
    """
    解析单份早报 markdown
    返回 (report_meta, articles_list)
    """
    content = md_path.read_text(encoding='utf-8')
    date_str = md_path.stem  # YYYY-MM-DD

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"⚠️ 跳过非日期文件: {md_path}", file=sys.stderr)
        return None, []

    # 提取头部信息
    signal = detect_signal_strength(content)
    main_count = extract_number(content, r'(\d+)\s*篇\s*主报告', 0)
    tier0_count = extract_number(content, r'(\d+)\s*篇\s*Tier\s*0', 0)

    # 解析文章
    articles = parse_articles(content, date_str)

    # 如果 main_count 没解析到,从 articles 里数
    if main_count == 0:
        main_count = sum(1 for a in articles if not a["is_top5"] and not a["is_tier0"])
    if tier0_count == 0:
        tier0_count = sum(1 for a in articles if a["is_tier0"])

    report_meta = {
        "date": date_str,
        "weekday": WEEKDAY_CN[date_obj.weekday()],
        "signal_strength": signal,
        "main_count": main_count,
        "tier0_count": tier0_count,
        "summary": get_top_title(articles),
        "url": f"reports/{date_str}.md",
        "article_count": len(articles),
    }

    return report_meta, articles


# ═══════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════

def build_index():
    if not REPORTS_DIR.exists():
        print(f"❌ {REPORTS_DIR} 不存在", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(REPORTS_DIR.glob("*.md"))
    md_files = [f for f in md_files if re.match(r'\d{4}-\d{2}-\d{2}\.md$', f.name)]

    if not md_files:
        print("⚠️ reports/ 下没有 YYYY-MM-DD.md 文件", file=sys.stderr)
        sys.exit(0)

    print(f"📚 找到 {len(md_files)} 份早报")

    all_reports = []
    all_articles = []

    for md in md_files:
        print(f"  解析 {md.name}...", end='')
        report_meta, articles = parse_report(md)
        if report_meta is None:
            continue
        all_reports.append(report_meta)
        all_articles.extend(articles)
        print(f" ✓ {len(articles)} 篇文章")

    # 按日期降序排
    all_reports.sort(key=lambda r: r["date"], reverse=True)
    all_articles.sort(key=lambda a: a["date"], reverse=True)

    # ── 构建标签索引 ──
    dimensions_counter = Counter()
    companies_counter = Counter()
    signal_counter = Counter()

    for a in all_articles:
        if a["dimension"]:
            dimensions_counter[a["dimension"]] += 1
        for c in a["companies"]:
            companies_counter[c] += 1

    for r in all_reports:
        signal_counter[r["signal_strength"]] += 1

    # ── 时间序列(过去 30 天每天的文章数,for 趋势图) ──
    if all_reports:
        latest = datetime.strptime(all_reports[0]["date"], "%Y-%m-%d")
        earliest = latest - timedelta(days=29)
        date_articles = {}
        for r in all_reports:
            date_articles[r["date"]] = r["main_count"] + r["tier0_count"]
        timeline = []
        for i in range(30):
            d = (earliest + timedelta(days=i)).strftime("%Y-%m-%d")
            timeline.append({"date": d, "count": date_articles.get(d, 0)})
    else:
        timeline = []

    # ── 公司频次 timeline(过去 30 天 top 10 公司每天的出现次数) ──
    top10_companies = [c for c, _ in companies_counter.most_common(10)]
    company_timeline = {c: {} for c in top10_companies}
    for a in all_articles:
        for c in a["companies"]:
            if c in company_timeline:
                company_timeline[c][a["date"]] = company_timeline[c].get(a["date"], 0) + 1

    # ── 组装最终 JSON ──
    output = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_reports": len(all_reports),
            "total_articles": len(all_articles),
            "date_range": [
                all_reports[-1]["date"] if all_reports else "",
                all_reports[0]["date"] if all_reports else "",
            ],
        },
        "reports": all_reports,
        "articles": all_articles,
        "tag_index": {
            "dimensions": dict(dimensions_counter.most_common()),
            "companies": dict(companies_counter.most_common(50)),  # 最多 50 个
            "signal_days": dict(signal_counter),
        },
        "trends": {
            "timeline_30d": timeline,
            "top_companies_timeline": company_timeline,
            "top10_companies": top10_companies,
        },
    }

    # 写文件
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print()
    print(f"═══════════════════════════════════════")
    print(f"✅ 索引已生成: {OUTPUT_FILE}")
    print(f"📚 {len(all_reports)} 份早报 · {len(all_articles)} 篇文章")
    print(f"🏷  {len(dimensions_counter)} 个维度 · {len(companies_counter)} 家公司")
    print(f"📈 信号分布: {dict(signal_counter)}")
    print(f"═══════════════════════════════════════")


if __name__ == "__main__":
    build_index()
