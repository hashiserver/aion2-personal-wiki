import importlib.util
import json
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

    def build(self):
        spec = importlib.util.spec_from_file_location('wiki_build', ROOT / 'build.py')
        if spec is None or not Path(spec.origin).exists():
            self.fail('build_site is not implemented')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
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
        self.assertIn('../../assets/style.css', html)
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


if __name__ == '__main__':
    unittest.main()
