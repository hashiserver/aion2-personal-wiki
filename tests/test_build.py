import importlib.util
import json
import re
import shutil
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INTRO = 'このサイトは個人利用を想定し、AIを活用して公開情報を収集・整理しています。'


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.content = self.root / 'content'
        self.content.mkdir()
        self.sources = self.root / 'sources.json'
        self.sources.write_text(json.dumps({'s1': {'title': '資料', 'url': 'https://example.com/guide', 'tag': '日本記事', 'region': 'グローバル', 'scope': '未確認', 'checked_at': '2026-10-06', 'published_at': None}}))

    def build(self, project_root=None):
        spec = importlib.util.spec_from_file_location('wiki_build', ROOT / 'build.py')
        if spec is None or not Path(spec.origin).exists():
            self.fail('build_site is not implemented')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if project_root is not None:
            module.ROOT = project_root
        module.build_site(self.content, self.sources, self.root / 'dist')

    def article(self, filename, slug='', body=INTRO, ids=None):
        meta = {'slug': slug, 'title': '記事', 'checked_at': '2026-10-06', 'source_ids': ids if ids is not None else ['s1']}
        (self.content / filename).write_text(json.dumps(meta) + '\n\n' + body)

    def test_unknown_source_is_rejected(self):
        self.article('index.md', ids=['missing'])
        with self.assertRaisesRegex(ValueError, 'unknown source'):
            self.build()

    def test_duplicate_slug_is_rejected(self):
        self.article('index.md')
        self.article('other.md')
        with self.assertRaisesRegex(ValueError, 'duplicate slug'):
            self.build()

    def test_shared_notice_is_present_with_a_brief_homepage(self):
        self.article('index.md', body='今日やること')
        self.build()
        rendered = (self.root / 'dist/index.html').read_text()
        for word in ('AI', '個人利用', '公開情報'):
            self.assertIn(word, rendered)

    def test_unsafe_slug_is_rejected(self):
        self.article('index.md')
        self.article('other.md', slug='../escape')
        with self.assertRaisesRegex(ValueError, 'unsafe slug'):
            self.build()

    def test_non_http_source_is_rejected(self):
        self.article('index.md')
        data = json.loads(self.sources.read_text())
        data['s1']['url'] = 'javascript:alert(1)'
        self.sources.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'source URL'):
            self.build()

    def test_nested_links_and_unknown_publication_date(self):
        self.article('index.md')
        self.article('class.md', slug='classes/test', body='## 構成\n\n| 技 | 出典 |\n|---|---|\n| 技名 | [[source:s1]] |')
        self.build()
        html = (self.root / 'dist/classes/test/index.html').read_text()
        self.assertRegex(html, r'href="/assets/style\.[0-9a-f]{12}\.css"')
        self.assertIn('公開日不明', html)
        self.assertIn('確認日 2026-10-06', html)
        self.assertIn('tabindex="0"', html)
        self.assertIn('href="#source-s1"', html)
        self.assertNotIn('[[source:', html)

    def test_source_marker_must_be_declared(self):
        self.article('index.md', body=INTRO + '\n[[source:s2]]')
        with self.assertRaisesRegex(ValueError, 'undeclared source'):
            self.build()

    def test_legacy_route_rules_are_shipped_with_generated_pages(self):
        self.article('index.md')
        self.build()
        rules = self.root / 'dist/_redirects'
        self.assertTrue(rules.exists(), 'old URLs must keep working after removing articles')
        self.assertIn('/routine/ /#daily 302', rules.read_text())

    def test_removed_article_disappears_after_rebuild(self):
        self.article('index.md')
        self.article('old.md', slug='classes/old')
        self.build()
        old_page = self.root / 'dist/classes/old/index.html'
        self.assertTrue(old_page.exists())
        (self.content / 'old.md').unlink()
        self.build()
        self.assertFalse(old_page.exists())
        self.assertTrue((self.root / 'dist/index.html').exists())

    def test_navigation_and_body_links_use_canonical_worker_routes(self):
        self.article('index.md', body='[イベント](events/index.html)\n\n[外部](https://example.com/index.html)')
        self.article('events.md', slug='events')
        self.article('links.md', slug='links')
        self.article('sources.md', slug='sources')
        self.article('nested.md', slug='classes/test', body='[イベント](../../events/index.html?view=compact#details)\n\n[出典](#source-s1)')
        self.build()
        for page in (self.root / 'dist').rglob('index.html'):
            text = page.read_text()
            self.assertIn('href="/"', text)
            self.assertIn('href="/events/"', text)
            self.assertIn('href="/links/"', text)
            self.assertNotRegex(text, r'href="(?!https?://)[^"]*index\.html')
        home = (self.root / 'dist/index.html').read_text()
        nested = (self.root / 'dist/classes/test/index.html').read_text()
        self.assertIn('href="https://example.com/index.html"', home)
        self.assertIn('href="/events/?view=compact#details"', nested)
        self.assertIn('href="#source-s1"', nested)

    def test_gear_roll_article_is_linked(self):
        self.article('index.md')
        self.article('gear.md', slug='gear', body='## 4候補\n\n| 部位 | ① | ② | ③ | ④ |\n|---|---|---|---|---|\n| ワンド | 戦闘速度 | 威力 | 正確 | 強打 |')
        self.build()
        home = (self.root / 'dist/index.html').read_text()
        gear = (self.root / 'dist/gear/index.html').read_text()
        self.assertIn('href="/gear/"', home)
        self.assertIn('戦闘速度', gear)
        self.assertIn('aria-label="比較表。横にスクロールできます"', gear)

    def test_gear_class_subnavigation_and_isolated_tables(self):
        self.article('index.md')
        self.article('gear.md', slug='gear', body='## 全体方針\nクラスを選択')
        self.article('gear-chanter.md', slug='gear/chanter',
                     body='## チャンター装備\n\n| 部位 | ① | ② | ③ | ④ |\n|---|---|---|---|---|\n| ガーダー | 戦闘速度 | 威力 | 状態異常的中 | 武器ダメージ増幅 |')
        self.article('gear-cleric.md', slug='gear/cleric',
                     body='## クレリック装備\n\n| 部位 | ① | ② | ③ | ④ |\n|---|---|---|---|---|\n| グローブ | 戦闘速度 | 完璧 | HP | 命中 |')
        self.build()
        overview = (self.root / 'dist/gear/index.html').read_text()
        chanter = (self.root / 'dist/gear/chanter/index.html').read_text()
        cleric = (self.root / 'dist/gear/cleric/index.html').read_text()
        self.assertIn('aria-label="装備厳選：クラス切り替え"', overview)
        self.assertIn('href="/gear/chanter/"', overview)
        self.assertIn('href="/gear/cleric/"', chanter)
        self.assertIn('href="/gear/chanter/" aria-current="page"', chanter)
        self.assertIn('>チャンター</a>', chanter)
        self.assertIn('>グラディエーター</a>', chanter)
        self.assertNotIn('>チャント</a>', chanter)
        self.assertNotIn('>ソード</a>', chanter)
        self.assertIn('href="/gear/" aria-current="page"', overview)
        self.assertIn('page-gear-chanter page-gear', chanter)
        self.assertIn('状態異常的中', chanter)
        self.assertNotIn('クレリック装備', chanter)
        self.assertIn('クレリック装備', cleric)
        self.assertNotIn('チャンター装備', cleric)

    def test_official_gear_class_names_on_all_pages(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('gear_build', ROOT / 'build.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = {'chanter': 'チャンター', 'gladiator': 'グラディエーター',
                    'templar': 'テンプラー', 'assassin': 'アサシン',
                    'ranger': 'レンジャー', 'sorcerer': 'ソーサラー',
                    'spiritmaster': 'スピリットマスター', 'cleric': 'クレリック'}
        self.assertEqual(dict(module.GEAR_CLASSES), expected)
        for slug, name in expected.items():
            with self.subTest(klass=slug):
                meta = json.loads((ROOT / f'content/gear-{slug}.md').read_text(encoding='utf-8').splitlines()[0])
                self.assertEqual(meta['title'], name + '｜装備オプション厳選')
        overview = (ROOT / 'content/gear.md').read_text(encoding='utf-8')
        for slug, name in expected.items():
            self.assertIn(f'[{name}](/gear/{slug}/)', overview)

    def test_gear_class_pages_have_all_original_thirteen_slots(self):
        classes = ['chanter', 'gladiator', 'templar', 'assassin', 'ranger',
                   'sorcerer', 'spiritmaster', 'cleric']
        slots = ['武器', 'ガーダー', 'ヘルム', 'ショルダー', 'トップス',
                 'グローブ', 'ボトムス', 'シューズ', 'マント',
                 'ネックレス', 'イヤリング×2', 'リング×2', 'ブレスレット']
        for name in classes:
            with self.subTest(klass=name):
                data = (ROOT / f'content/gear-{name}.md').read_text(encoding='utf-8')
                for slot in slots:
                    self.assertIn('| ' + slot + ' |', data)
                self.assertEqual(sum(line.startswith('| ') and
                        any(line.startswith('| ' + slot + ' |') for slot in slots)
                        for line in data.splitlines()), 13)

    def test_progression_page_has_its_own_canonical_route(self):
        self.article('index.md')
        self.article('progression.md', slug='progression', body='IL目標の説明')
        self.build()
        homepage = (self.root / 'dist/index.html').read_text()
        roadmap = self.root / 'dist/progression/index.html'
        self.assertTrue(roadmap.exists())
        self.assertIn('href="/progression/"', homepage)
        self.assertIn('IL目標の説明', roadmap.read_text())
        redirects = (self.root / 'dist/_redirects').read_text()
        self.assertNotIn('/progression/ /links/', redirects)

    def test_real_il_roadmap_covers_all_key_global_thresholds(self):
        article = ROOT / 'content/progression.md'
        self.assertTrue(article.exists())
        text = article.read_text(encoding='utf-8')
        for threshold in ('1,000', '1,400', '1,600', '1,900', '2,100',
                          '2,200', '2,500', '2,600', '2,700', '2,800', '3,000'):
            with self.subTest(il=threshold):
                self.assertIn(threshold, text)
        self.assertIn('日本・Asia', text)
        self.assertIn('[[source:global-patch-2026-11-04-official]]', text)

    def test_changed_css_has_new_cache_key_and_old_assets_are_removed(self):
        self.article('index.md')
        project = self.root / 'project'
        shutil.copytree(ROOT / 'assets', project / 'assets')
        shutil.copytree(ROOT / 'templates', project / 'templates')
        shutil.copyfile(ROOT / '_redirects', project / '_redirects')
        def stylesheet():
            page = (self.root / 'dist/index.html').read_text()
            return re.search(r'<link rel="stylesheet" href="([^"]+)"', page)[1]
        self.build(project)
        first = stylesheet()
        self.build(project)
        self.assertEqual(stylesheet(), first)
        css = project / 'assets/style.css'
        css.write_text(css.read_text() + '\nbody{outline:1px solid red}\n')
        self.build(project)
        second = stylesheet()
        self.assertNotEqual(first, second)
        self.assertFalse((self.root / 'dist' / first.lstrip('/')).exists())
        self.assertEqual((self.root / 'dist' / second.lstrip('/')).read_text(), css.read_text())
        headers = (self.root / 'dist/_headers').read_text()
        self.assertIn(second + '\n  Cache-Control: public, max-age=31536000, immutable', headers)
        self.assertNotIn(first, headers)


if __name__ == '__main__':
    unittest.main()
