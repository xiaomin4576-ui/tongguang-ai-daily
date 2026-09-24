import sys
from pathlib import Path
import unittest
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from refresh_live_news import parse_feed, build_payload, safe_url, clean

NOW = datetime(2026, 9, 24, 9, tzinfo=timezone.utc)
SOURCE = {'id':'sample', 'name':'Sample', 'all_ai':True}

def rss(date='Thu, 24 Sep 2026 08:00:00 GMT', url='https://example.com/post', title='AI update'):
    return f'<rss><channel><item><title>{title}</title><link>{url}</link><pubDate>{date}</pubDate><description><![CDATA[<p>Summary</p><script>bad()</script>]]></description></item></channel></rss>'.encode()

class IntakeTest(unittest.TestCase):
    def test_publication_date_and_plain_excerpt(self):
        a = parse_feed(rss(), SOURCE, NOW)[0]
        self.assertEqual(a['date'], '2026-09-24')
        self.assertEqual(a['summary'], 'Summary')
        self.assertIsNone(a['quality_score'])
        self.assertEqual(parse_feed(rss(url='https://example.com/post?utm_source=x'), SOURCE, NOW)[0]['id'], a['id'])

    def test_reject_missing_old_future_and_unsafe_links(self):
        for date in ('', 'Thu, 24 Sep 2020 08:00:00 GMT', 'Fri, 25 Sep 2026 08:00:00 GMT', 'not a date'):
            self.assertEqual(parse_feed(rss(date), SOURCE, NOW), [])
        self.assertEqual(parse_feed(rss(url='javascript:alert(1)'), SOURCE, NOW), [])
        with self.assertRaises(ValueError): parse_feed(b'<!DOCTYPE rss><rss/>', SOURCE, NOW)
        with self.assertRaises(ValueError): parse_feed(b'<html/>', SOURCE, NOW)

    def test_atom_uses_published_not_recent_updated(self):
        atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>AI</title><link rel="alternate" href="https://example.com/atom"/><published>2026-07-01T00:00:00Z</published><updated>2026-09-24T08:00:00Z</updated></entry></feed>'
        self.assertEqual(parse_feed(atom, SOURCE, NOW), [])
        fresh = atom.replace(b'2026-07-01', b'2026-09-24')
        self.assertEqual(parse_feed(fresh, SOURCE, NOW)[0]['url'], 'https://example.com/atom')

    def test_general_feed_requires_ai_topic(self):
        source = dict(SOURCE, all_ai=False)
        self.assertEqual(parse_feed(rss(title='A holiday story'), source, NOW), [])
        self.assertEqual(len(parse_feed(rss(title='Gemini improvements'), source, NOW)), 1)

    def test_failures_keep_content_and_success_timestamp(self):
        items = parse_feed(rss(), SOURCE, NOW)
        good = (items, {'id':'one','name':'One','ok':True,'items':1})
        payload, healthy = build_payload({}, [good, good], NOW)
        self.assertTrue(healthy)
        self.assertEqual(len(payload['articles']), 1)
        bad = ([], {'id':'one','name':'One','ok':False,'items':0})
        failed, healthy = build_payload(payload, [bad, bad], NOW + timedelta(days=1))
        self.assertFalse(healthy)
        self.assertEqual(failed['articles'], items)
        self.assertEqual(failed['meta']['last_success_at'], payload['meta']['last_success_at'])
        self.assertEqual(failed['meta']['status'], 'stale')

    def test_empty_success_is_not_new_content(self):
        empty = ([], {'id':'one','name':'One','ok':True,'items':0})
        payload, healthy = build_payload({}, [empty, empty], NOW)
        self.assertFalse(healthy)
        self.assertIsNone(payload['meta']['last_success_at'])

if __name__ == '__main__': unittest.main()
