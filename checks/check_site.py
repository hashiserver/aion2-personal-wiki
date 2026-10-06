from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ('href', 'src'):
            if attrs.get(name):
                self.refs.append(attrs[name])


def check_site(root: Path) -> list[str]:
    root = root.resolve()
    files = list(root.rglob('*.html'))
    parsed = {p: Page(p.read_text(encoding='utf-8')) for p in files}
    issues = []
    home = root / 'index.html'
    if not home.exists():
        issues.append('missing homepage')
    elif not all(s in home.read_text(encoding='utf-8') for s in ('AI', '個人利用', '公開情報')):
        issues.append('missing AI / personal use notice')
    for path, page in parsed.items():
        if '[[source:' in path.read_text(encoding='utf-8'):
            issues.append(f'{path.relative_to(root)}: unrendered source marker')
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            target = (root / unquote(url.path.lstrip('/'))) if url.path.startswith('/') else (path.parent / unquote(url.path))
            if not url.path:
                target = path
            if target.is_dir():
                target /= 'index.html'
            target = target.resolve()
            if not target.is_relative_to(root) or not target.exists():
                issues.append(f'{path.relative_to(root)}: missing link {ref}')
            elif url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
                issues.append(f'{path.relative_to(root)}: missing fragment {ref}')
    return issues


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'dist'
    problems = check_site(root)
    if problems:
        print('\n'.join(problems))
        raise SystemExit(1)
    print(f'PASS: {len(list(root.rglob("*.html")))} pages; internal links, source anchors and notice valid')
