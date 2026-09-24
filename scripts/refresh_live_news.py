#!/usr/bin/env python3
"""Collect dated AI RSS/Atom items; preserve editorial archive and last good news.
Only source-provided publication dates count as new content. No LLM claims/scores.
Exit 2 on unhealthy intake, after writing status so the UI can show the failure.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import ssl
import urllib.request
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
BEIJING = timezone(timedelta(hours=8))
AI_TERMS = re.compile(r'\b(?:AI|LLM|GPT|Gemini|Claude|OpenAI|Anthropic|ChatGPT|agents?|inference|robotics|CUDA|tokens?|agentic)\b|artificial intelligence|machine learning|人工智能|大模型|智能体|机器人|算力', re.I)
COMPANIES = {'OpenAI': r'\bOpenAI\b|\bChatGPT\b|\bGPT[-‑ ]?\d', 'Anthropic': r'\bAnthropic\b|\bClaude\b',
             'Google': r'\bGoogle\b|\bGemini\b|\bDeepMind\b', 'NVIDIA': r'\bNVIDIA\b|英伟达',
             'Microsoft': r'\bMicrosoft\b|微软', 'Meta': r'\bMeta\b|\bLlama\b',
             'Hugging Face': r'\bHugging ?Face\b', 'DeepSeek': r'\bDeepSeek\b'}
MAX_BYTES = 8 * 1024 * 1024

class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden - 1)
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)

def clean(text, limit):
    parser = PlainText(); parser.feed(unescape(text or ''))
    return re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()[:limit]

def date_value(value):
    if not value: return None
    try:
        dt = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except ValueError:
        try: dt = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError): return None
    # A date without a timezone is ambiguous; don't turn it into today's news.
    return dt.astimezone(UTC) if dt.tzinfo else None

def safe_url(value):
    try:
        p = urlsplit(value.strip())
        if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password: return ''
        if any(c in value for c in '\r\n\t'): return ''
        query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                           if not k.lower().startswith('utm_')])
        return urlunsplit((p.scheme, p.netloc, p.path, query, ''))
    except ValueError: return ''

def parse_feed(raw, source, now):
    if len(raw) > MAX_BYTES or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Feed size or XML declaration rejected')
    root = ET.fromstring(raw)
    kind = root.tag.rsplit('}', 1)[-1]
    if kind not in ('rss', 'feed', 'RDF'): raise ValueError('Not an RSS/Atom feed')
    articles = []
    for entry in root.iter():
        if entry.tag.rsplit('}', 1)[-1] not in ('item', 'entry'): continue
        fields = {}
        for child in entry:
            name = child.tag.rsplit('}', 1)[-1]
            value = ''.join(child.itertext())
            if name == 'link' and child.get('href'):
                if child.get('rel', 'alternate') == 'alternate': fields['link'] = child.get('href')
            elif name not in fields:
                fields[name] = value
        # Do not use Atom updated to re-date an old story with a published date.
        stamp = fields.get('published') or fields.get('pubDate') or fields.get('date') or fields.get('updated')
        dt = date_value(stamp)
        if not dt or dt > now + timedelta(minutes=5) or dt < now - timedelta(days=7): continue
        title = clean(fields.get('title'), 240)
        summary = clean(fields.get('description') or fields.get('summary') or fields.get('content'), 300)
        url = safe_url(fields.get('link', ''))
        if not title or not url: continue
        if not source.get('all_ai') and not AI_TERMS.search(title + ' ' + summary): continue
        articles.append({
            'id': 'live-' + hashlib.sha256(url.encode()).hexdigest()[:20],
            'date': dt.astimezone(BEIJING).date().isoformat(), 'published_at': dt.isoformat(),
            'title': title, 'summary': summary, 'meaning': '', 'url': url,
            'source': source['name'], 'source_id': source['id'], 'automated': True,
            'dimension': '📰 自动快讯', 'quality_score': None, 'is_top5': False,
            'is_tier0': False, 'companies': [company for company, pattern in COMPANIES.items() if re.search(pattern, title + ' ' + summary + ' ' + source['name'], re.I)],
        })
    return sorted(articles, key=lambda a: a['published_at'], reverse=True)[:25]

def fetch_source(source, now):
    try:
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError: ctx = ssl.create_default_context()
        req = urllib.request.Request(source['url'], headers={'User-Agent': 'LUMORA-AI-News/1.0 RSS Reader'})
        with urllib.request.urlopen(req, timeout=18, context=ctx) as res:
            raw = res.read(MAX_BYTES + 1)
        articles = parse_feed(raw, source, now)
        return articles, {'id': source['id'], 'name': source['name'], 'ok': True, 'items': len(articles)}
    except Exception as exc:
        return [], {'id': source['id'], 'name': source['name'], 'ok': False, 'items': 0,
                    'error': type(exc).__name__ + ': ' + str(exc)[:120]}

def build_payload(previous, results, now):
    # Merge by canonical link: retries and repeated items never duplicate a story.
    by_url = {a['url']: a for a in previous.get('articles', []) if safe_url(a.get('url', ''))}
    for items, _ in results:
        for article in items: by_url[article['url']] = article
    articles = sorted(by_url.values(), key=lambda a: a['published_at'], reverse=True)
    checks = [c for _, c in results]
    received = [a for items, _ in results for a in items]
    recent = [a for a in received if date_value(a['published_at']) >= now - timedelta(hours=72)]
    succeeded = sum(c['ok'] for c in checks)
    healthy = succeeded >= min(2, len(checks)) and bool(recent)
    old_meta = previous.get('meta', {})
    meta = {
        'attempted_at': now.isoformat(),
        'last_success_at': now.isoformat() if healthy else old_meta.get('last_success_at'),
        'status': ('ok' if succeeded == len(checks) else 'partial') if healthy else 'stale',
        'latest_article_at': articles[0]['published_at'] if articles else None,
        'sources_ok': succeeded, 'sources_total': len(checks), 'source_checks': checks,
        'total_articles': len(articles), 'received_items': len(received),
        'mode': 'rss-source-excerpts',
    }
    return {'meta': meta, 'articles': articles}, healthy

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT / 'docs/data/live-news.json')
    args = p.parse_args()
    sources = json.loads((ROOT / 'live_sources.json').read_text())
    previous = json.loads(args.output.read_text()) if args.output.exists() else {}
    now = datetime.now(UTC)
    with ThreadPoolExecutor(max_workers=7) as pool:
        results = list(pool.map(lambda s: fetch_source(s, now), sources))
    payload, healthy = build_payload(previous, results, now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix('.tmp'); temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    temp.replace(args.output)
    for check in payload['meta']['source_checks']:
        print(f"{check['name']}: {check['items']} items, {'OK' if check['ok'] else check['error']}")
    print(json.dumps({k:v for k,v in payload['meta'].items() if k != 'source_checks'}, ensure_ascii=False))
    if not healthy:
        print('::warning::AI news intake is stale or unavailable; previous articles retained.')
        raise SystemExit(2)

if __name__ == '__main__': main()
