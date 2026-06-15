#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_clips_index.py v2
精确适配 xiaomin4576-ui/my-clips 格式:

# YYYY-MM-DD

## HH:MM:SS · 文字
> 引用块内容
来源: @用户名: 描述...  所在页面: [链接名](url)

---

## HH:MM:SS · 图片
![alt](image-url)
来源: @用户名

---
"""

import os
import re
import json
import sys
from datetime import datetime, timezone, timedelta

CLIPS_DIR = os.environ.get('CLIPS_DIR', 'my-clips/clips')
OUTPUT_PATH = os.environ.get('OUTPUT_PATH', 'docs/data/clips-index.json')

# ═══════════════════════════════════════════════════════════════════
# 信源识别(根据 URL 或 @用户)
# ═══════════════════════════════════════════════════════════════════
URL_SOURCE_PATTERNS = [
    (r'mp\.weixin\.qq\.com',                  '微信公众号'),
    (r'(twitter\.com|x\.com)',                 'X(Twitter)'),
    (r'zhihu\.com',                            '知乎'),
    (r'(weibo|t\.cn)',                         '微博'),
    (r'(juejin|csdn|jianshu|sspai)\.cn',      '中文技术博客'),
    (r'(medium\.com|substack\.com)',           'Medium/Substack'),
    (r'(hbr\.org|harvardbusiness)',           'HBR'),
    (r'(mckinsey|bcg|bain|deloitte)\.com',    '咨询公司'),
    (r'(bloomberg|reuters|wsj|ft)\.com',       '国际财经'),
    (r'(theverge|techcrunch|wired)',          '科技媒体'),
    (r'(36kr|qbitai|geekpark|tmtpost)',       '中文科技媒体'),
    (r'github\.com',                            'GitHub'),
    (r'arxiv\.org',                            'arXiv'),
]

def detect_source_from_url(url):
    if not url:
        return ''
    for pattern, name in URL_SOURCE_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return name
    return ''

# ═══════════════════════════════════════════════════════════════════
# 解析单条裁剪
# ═══════════════════════════════════════════════════════════════════

def parse_one_clip(chunk_text, file_date, file_name):
    """
    解析单个 ## HH:MM:SS · 类型 段落
    
    输入示例:
    
    22:42:21 · 文字
    
    > Tycoon AI 是自动化理念在组织层面的激进实验:当 Agent 能力密度超过人类...
    
    来源:@skyrain888: 8/9 Tycoon AI 是自动化理念... 所在页面:[AI 组织 - Search / X](https://x.com/...)
    
    """
    result = {
        'time': '',
        'type': '',     # 文字 / 图片
        'quote': '',    # 引用块内容
        'images': [],   # 图片 URL 列表
        'author': '',   # @用户名
        'author_desc': '', # @用户名后的描述
        'source_url': '',  # 所在页面 URL
        'source_page': '', # 所在页面名
        'all_urls': [],
        'raw': chunk_text.strip(),
    }
    
    lines = chunk_text.strip().split('\n')
    if not lines:
        return None
    
    # 第一行: HH:MM:SS · 类型
    first = lines[0].strip().lstrip('#').strip()
    m = re.match(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*[·•]\s*(.+)', first)
    if m:
        h, mn, s, kind = m.group(1), m.group(2), m.group(3) or '00', m.group(4)
        result['time'] = f"{h.zfill(2)}:{mn}:{s}"
        result['type'] = kind.strip()
    else:
        # 不像标准格式, 把整个第一行当 type
        result['type'] = first
    
    body = '\n'.join(lines[1:]).strip()
    
    # 提取所有 URL
    urls = re.findall(r'https?://[^\s\)\]"\'<>]+', body)
    result['all_urls'] = list(dict.fromkeys(urls))  # 去重
    
    # 1. 提取引用块(> 开头)
    quote_lines = []
    for line in body.split('\n'):
        line_strip = line.strip()
        if line_strip.startswith('>'):
            quote_lines.append(re.sub(r'^>\s*', '', line_strip))
    if quote_lines:
        result['quote'] = '\n'.join(quote_lines).strip()
    
    # 2. 提取图片
    img_matches = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', body)
    result['images'] = [{'alt': alt, 'url': url} for alt, url in img_matches]
    
    # 3. 提取"来源: @xxx"行
    source_match = re.search(r'来源[::]\s*(.+?)(?=\n\n|\n来源|\n所在页面|$)', body, re.DOTALL)
    if source_match:
        source_line = source_match.group(1).strip().replace('\n', ' ')
        
        # 先把 "来源:" 后的 markdown 链接 [@user](url) 整体替换成 @user
        # 因为我们已经在 source_line 里提取 author + author_desc, url 已经在 all_urls 里
        cleaned = re.sub(r'\[(@[^\]]+)\]\([^)]+\)', r'\1', source_line)
        
        # 提取 @用户名
        author_match = re.search(r'@([A-Za-z0-9_]+)', cleaned)
        if author_match:
            result['author'] = '@' + author_match.group(1)
            # @user 后面的描述
            after = cleaned[author_match.end():].lstrip(':: ').strip()
            # 去掉 "所在页面" 之后的部分
            if '所在页面' in after:
                after = after.split('所在页面')[0].strip()
            # 去掉末尾的省略号 / 引号
            after = after.rstrip('. …"\' ')
            result['author_desc'] = after[:300]
    
    # 4. 提取"所在页面: [名称](URL)"
    page_match = re.search(r'所在页面[::]\s*\[([^\]]+)\]\(([^)]+)\)', body)
    if page_match:
        result['source_page'] = page_match.group(1).strip()
        result['source_url'] = page_match.group(2).strip()
    else:
        # 兜底: 找最后一个 URL
        if urls:
            result['source_url'] = urls[-1]
    
    return result

# ═══════════════════════════════════════════════════════════════════
# 解析整个 md 文件
# ═══════════════════════════════════════════════════════════════════

def parse_file(filepath):
    filename = os.path.basename(filepath)
    
    # 文件名提取日期 (2026-05-23.md)
    file_date = ''
    m = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if m:
        file_date = m.group(1)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            md = f.read()
    except Exception as e:
        print(f"  ⚠️ 读取失败 {filename}: {e}", file=sys.stderr)
        return []
    
    # 按 ## 分割(每个 ## 是一条裁剪)
    # 但要小心:第一段(在 # H1 之后, 第一个 ## 之前)是文件 header, 跳过
    
    # 找所有 ## 标题位置(不是 ### 等)
    chunks = []
    pattern = re.compile(r'^##\s+', re.MULTILINE)
    matches = list(pattern.finditer(md))
    
    if not matches:
        return []
    
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(md)
        chunk_text = md[start:end]
        # 去掉 ## 标记
        chunk_text = re.sub(r'^##\s+', '', chunk_text, count=1)
        # 去掉末尾的 --- 分隔线
        chunk_text = re.sub(r'\n---\s*$', '', chunk_text.rstrip())
        chunks.append(chunk_text)
    
    clips = []
    for idx, chunk in enumerate(chunks):
        parsed = parse_one_clip(chunk, file_date, filename)
        if not parsed:
            continue
        
        # 计算最终 source(优先 source_url, 兜底 author 平台)
        source_name = detect_source_from_url(parsed['source_url'])
        if not source_name and parsed['author']:
            # 有 @用户名 但无 URL → 推测是 Twitter/X
            if '/x.com' in str(parsed['all_urls']) or 'twitter.com' in str(parsed['all_urls']):
                source_name = 'X(Twitter)'
            else:
                source_name = '社交媒体'
        
        # 生成 title
        # 类型 = 图片: 优先 image alt > author_desc > "[图片裁剪]"
        # 类型 = 文字: 优先 quote 第一句 > author_desc > "[时间] · 文字"
        title = ''
        if parsed['type'] == '图片':
            if parsed['images'] and parsed['images'][0]['alt']:
                title = parsed['images'][0]['alt'][:80]
            elif parsed['author_desc']:
                title = parsed['author_desc'][:80]
            else:
                title = f"[图片] {parsed['author']}" if parsed['author'] else f"[图片裁剪] {parsed['time']}"
        else:
            # 文字类型
            if parsed['quote']:
                title = parsed['quote'].split('\n')[0][:80]
            elif parsed['author_desc']:
                title = parsed['author_desc'][:80]
            else:
                title = f"{parsed['time']} · {parsed['type']}"
        
        # 标签自动添加(time / type / author)
        tags = []
        if parsed['type']:
            tags.append(parsed['type'])
        if parsed['author']:
            tags.append(parsed['author'])
        
        # 生成 preview(展示用)
        preview = parsed['quote'] or parsed['author_desc'] or ''
        if parsed['images']:
            preview = ('[图片] ' if not preview else preview + ' [含图]')
        preview = preview[:240] + ('...' if len(preview) > 240 else '')
        
        clip = {
            'id': f"{filename.replace('.md', '')}_{idx+1:03d}",
            'file': filename,
            'date': file_date,
            'time': parsed['time'],
            'type': parsed['type'],
            'title': title,
            'quote': parsed['quote'],
            'images': parsed['images'],
            'has_image': len(parsed['images']) > 0,
            'author': parsed['author'],
            'author_desc': parsed['author_desc'],
            'source': source_name,
            'source_page': parsed['source_page'],
            'source_url': parsed['source_url'],
            'all_urls': parsed['all_urls'][:5],
            'tags': tags,
            'preview': preview,
            'raw': parsed['raw'],
            'datetime': f"{file_date}T{parsed['time']}+08:00" if file_date and parsed['time'] else file_date,
        }
        clips.append(clip)
    
    return clips

# ═══════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════

def main():
    if not os.path.exists(CLIPS_DIR):
        print(f"❌ 目录不存在: {CLIPS_DIR}", file=sys.stderr)
        for alt in ['../my-clips/clips', '../../my-clips/clips', 'clips']:
            if os.path.exists(alt):
                print(f"  ✓ 改用: {alt}")
                globals()['CLIPS_DIR'] = alt
                break
        else:
            output_empty()
            return
    
    md_files = sorted([
        os.path.join(CLIPS_DIR, f) 
        for f in os.listdir(CLIPS_DIR) 
        if f.endswith('.md') and not f.startswith('.')
    ], reverse=True)  # 最新日期在前
    
    print(f"📁 发现 {len(md_files)} 个 md 文件")
    
    all_clips = []
    for filepath in md_files:
        filename = os.path.basename(filepath)
        clips = parse_file(filepath)
        all_clips.extend(clips)
        print(f"  📄 {filename}: {len(clips)} 条裁剪")
    
    # 按 datetime 倒序(最新在前)
    all_clips.sort(key=lambda c: c.get('datetime', '0'), reverse=True)
    
    # 统计
    sources = {}
    types_count = {'文字': 0, '图片': 0, '其他': 0}
    authors_count = {}
    files_count = {}
    image_count = 0
    
    for c in all_clips:
        if c['source']:
            sources[c['source']] = sources.get(c['source'], 0) + 1
        t = c.get('type', '')
        if t == '文字': types_count['文字'] += 1
        elif t == '图片': types_count['图片'] += 1
        else: types_count['其他'] += 1
        
        if c['author']:
            authors_count[c['author']] = authors_count.get(c['author'], 0) + 1
        files_count[c['file']] = files_count.get(c['file'], 0) + 1
        
        if c.get('has_image'):
            image_count += 1
    
    output = {
        'generated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'source_repo': 'xiaomin4576-ui/my-clips',
        'source_path': CLIPS_DIR,
        'total_files': len(md_files),
        'total_clips': len(all_clips),
        'total_with_images': image_count,
        'types': types_count,
        'top_sources': sorted(sources.items(), key=lambda x: -x[1])[:10],
        'top_authors': sorted(authors_count.items(), key=lambda x: -x[1])[:15],
        'files': sorted(files_count.items(), key=lambda x: x[0], reverse=True),
        'clips': all_clips,
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH) or '.', exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print()
    print(f"═══════════════════════════════════════════")
    print(f"✅ 解析完成")
    print(f"   文件: {len(md_files)}")
    print(f"   裁剪: {len(all_clips)}")
    print(f"   含图: {image_count}")
    print(f"   类型: {types_count}")
    print(f"   信源 Top 5: {list(sources.items())[:5]}")
    print(f"   作者 Top 5: {list(authors_count.items())[:5]}")
    print(f"   输出: {OUTPUT_PATH} ({size_kb:.1f} KB)")
    print(f"═══════════════════════════════════════════")

def output_empty():
    output = {
        'generated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'source_repo': 'xiaomin4576-ui/my-clips',
        'total_files': 0,
        'total_clips': 0,
        'total_with_images': 0,
        'types': {'文字': 0, '图片': 0, '其他': 0},
        'top_sources': [],
        'top_authors': [],
        'files': [],
        'clips': [],
        'error': f'clips 目录不存在: {CLIPS_DIR}',
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH) or '.', exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
