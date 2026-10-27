import unittest
from datetime import date
from html.parser import HTMLParser

import portal


class Links(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.hrefs = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs).get('href'))


class PortalTests(unittest.TestCase):
    def test_routines_are_rendered_by_consumption_cycle(self):
        sources = {'s': {'tag': '攻略', 'title': '出典'}}
        data = {'checked_at': '2026-10-27', 'events': [],
                'daily': [{'source_id': 's', 'title': '使命の任務', 'description': '5回'}],
                'accumulating': [{'source_id': 's', 'title': '悪夢', 'description': '上限に注意'}],
                'weekly': [{'source_id': 's', 'title': 'デイリーダンジョン', 'description': '週14回'}],
                'optional': [{'source_id': 's', 'title': 'フィールドボス', 'description': '出現時'}]}
        result = portal.render_portal(data, sources, ['s'])
        for label in ('毎日確認', '上限前に消化', '週の期限までに', '開催時・余裕があれば'):
            self.assertIn(label, result)
        for key, title in [('daily', '使命の任務'), ('accumulating', '悪夢'), ('weekly', 'デイリーダンジョン'), ('optional', 'フィールドボス')]:
            self.assertIn(title, result.split(f'id="{key}"')[1].split('</section>')[0])

    def test_exchange_source_must_be_declared(self):
        data = {'checked_at': '2026-10-20', 'exchanges': [
            {'source_id': 'missing', 'title': '交換', 'description': '説明'}]}
        with self.assertRaisesRegex(ValueError, 'source'):
            portal.render_portal(data, {}, [])

    def test_event_end_day_is_not_claimed_to_be_fully_active(self):
        event = {'starts_on': '2026-10-14', 'ends_on': '2026-11-04'}
        for day, state in [('2026-10-13', 'upcoming'), ('2026-10-19', 'active'),
                           ('2026-11-04', 'ending'), ('2026-11-05', 'ended')]:
            with self.subTest(day=day):
                self.assertEqual(portal.event_state(event, date.fromisoformat(day)), state)

    def test_unknown_card_source_prevents_publication(self):
        data = {'checked_at': '2026-10-19', 'events': [], 'tools': [], 'daily': [
            {'source_id': 'missing', 'title': '任務', 'description': '説明'}]}
        with self.assertRaisesRegex(ValueError, 'source'):
            portal.render_portal(data, {}, [])

    def test_cards_escape_text_and_use_the_declared_source_link(self):
        data = {'checked_at': '2026-10-19', 'events': [], 'tools': [
            {'source_id': 'tool', 'title': '<script>alert(1)</script>', 'description': '説明 & 詳細'}]}
        sources = {'tool': {'url': 'https://example.com/tool?a=1&b=2', 'tag': '海外ツール', 'title': 'ツールの出典'}}
        result = portal.render_links(data, sources, ['tool'])
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('https://example.com/tool?a=1&b=2', Links(result).hrefs)
        self.assertIn('#source-tool', Links(result).hrefs)


if __name__ == '__main__':
    unittest.main()


