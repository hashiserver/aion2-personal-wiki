import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'index.html').write_text('<html lang="ja"><body>AI 個人利用 公開情報</body></html>')

    def check(self):
        spec = importlib.util.spec_from_file_location('check_site', ROOT / 'checks/check_site.py')
        if not Path(spec.origin).exists():
            self.fail('check_site is not implemented')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.check_site(self.root)

    def test_broken_nested_page_is_reported(self):
        (self.root / 'classes').mkdir()
        (self.root / 'classes/index.html').write_text('<a href="missing/index.html">missing</a>')
        self.assertTrue(any('missing/index.html' in issue for issue in self.check()))

    def test_broken_stylesheet_is_reported(self):
        (self.root / 'index.html').write_text('<link href="assets/style.css" rel="stylesheet">AI 個人利用 公開情報')
        self.assertTrue(any('assets/style.css' in issue for issue in self.check()))

    def test_source_fragment_must_exist(self):
        (self.root / 'index.html').write_text('<a href="#source-nope">日本記事</a>AI 個人利用 公開情報')
        self.assertTrue(any('source-nope' in issue for issue in self.check()))

    def test_valid_nested_page_links_pass(self):
        (self.root / 'classes').mkdir()
        (self.root / 'classes/index.html').write_text('<a href="../index.html">home</a><a href="#source-s1">出典</a><p id="source-s1">source</p>')
        self.assertEqual(self.check(), [])


if __name__ == '__main__':
    unittest.main()
