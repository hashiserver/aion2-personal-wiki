import unittest
from datetime import datetime
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
    def test_task_detail_link_is_distinct_from_external_resource(self):
        sources = {'s': {'tag': '攻略', 'title': '出典', 'url': 'https://example.com/guide'}}
        data = {'checked_at': '2026-10-27', 'events': [],
                'daily': [{'source_id': 's', 'title': '任務', 'description': '5回', 'detail_url': '/duty/', 'detail_label': '任務の詳しい進め方'}],
                'tools': [{'source_id': 's', 'title': '攻略', 'description': '説明'}]}
        home = portal.render_portal(data, sources, ['s'])
        resources = portal.render_links(data, sources, ['s'])
        self.assertIn('href="/duty/"', home)
        self.assertIn('任務の詳しい進め方', home)
        self.assertIn('外部サイト', resources)
        self.assertIn('https://example.com/guide', Links(resources).hrefs)

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

    def test_approximate_event_end_has_a_full_day_confirmation_window(self):
        event = {'title': '時刻未公表', 'starts_on': '2026-10-14', 'ends_on': '2026-11-04'}
        schedule = portal.event_schedule(event)
        warning = int(datetime.fromisoformat('2026-11-04T00:00:00+09:00').timestamp() * 1000)
        expired = int(datetime.fromisoformat('2026-11-05T00:00:00+09:00').timestamp() * 1000)
        self.assertIn(f'data-warning="{warning}"', schedule)
        self.assertIn(f'data-end="{expired}"', schedule)
        self.assertNotIn('data-exact-end', schedule)

    def test_exact_event_end_requires_time_zone_and_matching_jst_date(self):
        event = {'title': 'クーポン', 'starts_on': '2026-11-18', 'ends_on': '2027-03-03'}
        for invalid in ('2027-03-03T16:00:00', '2027-03-03T16:00:00+00:00'):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'ends_at'):
                portal.event_schedule({**event, 'ends_at': invalid})
        end = '2027-03-03T16:00:00+09:00'
        schedule = portal.event_schedule({**event, 'ends_at': end})
        self.assertIn('data-exact-end', schedule)
        self.assertIn(f'data-end="{int(datetime.fromisoformat(end).timestamp() * 1000)}"', schedule)

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


    def test_weekly_limits_are_visible_without_expanding_the_panel(self):
        sources = {'s': {'tag': '公式', 'title': '案内'}}
        data = {'checked_at': '2026-11-05', 'events': [],
                'daily': [{'source_id': 's', 'title': '郵便', 'description': '受取'}],
                'weekly': [{'source_id': 's', 'title': '指令書', 'description': '進行手順',
                            'summary': '週12枚'}]}
        output = portal.render_portal(data, sources, ['s'])
        self.assertIn('<section class="task-panel" id="daily"', output)
        self.assertIn('<section class="task-panel" id="weekly"', output)
        self.assertIn('<details class="task-detail">', output)
        self.assertLess(output.index('週12枚'), output.index('<details class="task-detail">'))
        self.assertIn('href="#weekly"', output)
        self.assertLess(output.index('id="daily"'), output.index('id="weekly"'))

    def test_events_have_neutral_fallback_and_distinct_groups(self):
        sources = {'s': {'tag': '公式', 'title': '告知', 'url': 'https://example.com'}}
        def event(title, start, end, category):
            return {'source_id': 's', 'title': title, 'starts_on': start, 'ends_on': end,
                    'period': '期間', 'description': '報酬', 'deadline': 'ゲーム内確認',
                    'short_end': '受取期限', 'category': category}
        data = {'checked_at': '2026-11-05', 'events': [
            event('受取イベント', '2026-10-01', '2026-11-04', 'クーポン'),
            event('通常イベント', '2026-11-01', '2026-11-18', '期間限定'),
            event('パッチ告知', '2026-11-10', '2026-11-10', 'アップデート')]}
        output = portal.render_events(data, sources, ['s'])
        self.assertIn('id="current-events"', output)
        self.assertIn('id="rewards"', output)
        self.assertIn('<details class="event-archive" id="past-events" hidden>', output)
        self.assertEqual(output.count('<span class="status" hidden>'), 2)
        self.assertIn('id="event-s-2"', output)
        self.assertLess(output.index('通常イベント'), output.index('受取イベント'))
        self.assertLess(output.index('id="update-notes"'), output.index('パッチ告知'))
        self.assertNotIn('開催中', output)
        self.assertIn('公式・参照元を確認', output)

    def test_chanter_links_are_prominent_other_classes_are_accessible(self):
        sources = {key: {'tag': '資料', 'title': key, 'url': 'https://example.com/' + key}
                   for key in ('chanter-l', 'chanter-p', 'chanter-g', 'cleric-l', 'cleric-p', 'cleric-g')}
        data = {'classes': [
            {'name': 'クレリック', 'leveling': 'cleric-l', 'pve': 'cleric-p', 'alternative': 'cleric-g'},
            {'name': 'チャンター', 'leveling': 'chanter-l', 'pve': 'chanter-p', 'alternative': 'chanter-g'}]}
        output = portal.render_links(data, sources, list(sources))
        self.assertIn('<section class="featured-build" id="builds">', output)
        self.assertIn('その他の職業ビルド（1職）', output)
        self.assertLess(output.index('チャンターのビルド'), output.index('その他の職業ビルド'))
        self.assertIn('href="https://example.com/cleric-p"', output)


if __name__ == '__main__':
    unittest.main()


