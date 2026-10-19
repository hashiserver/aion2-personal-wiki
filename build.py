"""Generate a lightweight static wiki; no network calls or runtime JavaScript."""
import html
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

import markdown2
from portal import render_portal, render_links, render_events

ROOT = Path(__file__).resolve().parent
NAV = [('', '日課・週課'), ('events', 'イベント'), ('links', 'ビルド・ツール')]
MARKER = re.compile(r'\[\[source:([a-z0-9-]+)\]\]')


def load_article(path: Path) -> tuple[dict, str]:
    first, body = path.read_text(encoding='utf-8').split('\n', 1)
    meta = json.loads(first)
    for field in ('slug', 'title', 'checked_at', 'source_ids'):
        if field not in meta:
            raise ValueError(f'missing {field}: {path}')
    return meta, body.strip()


def relative_link(slug: str, target: str) -> str:
    start = slug or '.'
    dest = f'{target}/index.html' if target else 'index.html'
    return os.path.relpath(dest, start).replace(os.sep, '/')


def navigation(slug: str, known_slugs: set[str]) -> str:
    def item(target, title):
        if target not in known_slugs:
            return ''
        current = ' aria-current="page" class="current"' if target == slug else ''
        return f'<a href="{relative_link(slug, target)}"{current}>{html.escape(title)}</a>'
    primary = ''.join(item(s, t) for s, t in NAV)
    return f'<nav aria-label="ページ一覧">{primary}</nav>'


def render_sources(ids: list[str], sources: dict) -> str:
    rows = []
    for sid in ids:
        s = sources[sid]
        date = f'公開日 {s["published_at"]}' if s['published_at'] else '公開日不明'
        rows.append(f'<li id="source-{sid}"><span class="tag">{html.escape(s["tag"])}</span> '
                    f'<a href="{html.escape(s["url"], quote=True)}" rel="noreferrer">{html.escape(s["title"])}</a>'
                    f'<p class="source-meta">対象：{html.escape(s["region"])} · {html.escape(date)} · '
                    f'確認日 {html.escape(s["checked_at"])}（JST）</p>'
                    f'<p class="source-scope">{html.escape(s["scope"])}</p></li>')
    return '<details class="sources"><summary>情報源・確認した範囲（' + str(len(ids)) + '件）</summary><ul>' + ''.join(rows) + '</ul></details>' if ids else ''


def build_site(content_dir: Path, sources_path: Path, output_dir: Path) -> None:
    sources = json.loads(sources_path.read_text(encoding='utf-8'))
    for sid, s in sources.items():
        if not re.fullmatch('[a-z0-9-]+', sid):
            raise ValueError(f'unsafe source id: {sid}')
        url = urlsplit(s['url'])
        if url.scheme not in ('http', 'https') or not url.netloc:
            raise ValueError(f'unsafe source URL: {sid}')
        for field in ('title', 'tag', 'region', 'scope', 'checked_at', 'published_at'):
            if field not in s:
                raise ValueError(f'missing source field {field}: {sid}')
    articles = [load_article(p) for p in sorted(content_dir.rglob('*.md'))]
    known = set()
    for meta, body in articles:
        slug = meta['slug']
        if slug and not re.fullmatch(r'[a-z0-9-]+(?:/[a-z0-9-]+)*', slug):
            raise ValueError(f'unsafe slug: {slug}')
        if slug in known:
            raise ValueError(f'duplicate slug: {slug}')
        known.add(slug)
        for sid in meta['source_ids']:
            if sid not in sources:
                raise ValueError(f'unknown source: {sid}')
        for sid in MARKER.findall(body):
            if sid not in meta['source_ids']:
                raise ValueError(f'undeclared source: {sid}')
        if '[[source:' in MARKER.sub('', body):
            raise ValueError(f'invalid source marker: {slug}')
    if '' not in known:
        raise ValueError('missing homepage')

    output_dir.mkdir(parents=True, exist_ok=True)
    expected_pages = {output_dir / slug / 'index.html' for slug in known}
    for old_page in output_dir.rglob('index.html'):
        if old_page not in expected_pages:
            old_page.unlink()
    (output_dir / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'assets/style.css', output_dir / 'assets/style.css')
    shutil.copyfile(ROOT / '_redirects', output_dir / '_redirects')
    template = (ROOT / 'templates/page.html').read_text(encoding='utf-8')
    for meta, body in articles:
        slug = meta['slug']
        body_html = str(markdown2.markdown(body, extras=['tables', 'header-ids'], safe_mode='escape'))
        body_html = MARKER.sub(lambda m: f'<a class="tag source-tag" href="#source-{m[1]}" title="{html.escape(sources[m[1]]["region"] + " / " + sources[m[1]]["scope"], quote=True)}">{html.escape(sources[m[1]]["tag"])}</a>', body_html)
        body_html = re.sub(r'<table>', '<div class="table-scroll" tabindex="0" role="region" aria-label="比較表。横にスクロールできます"><table>', body_html)
        body_html = body_html.replace('</table>', '</table></div>')
        toc = ''.join(f'<a href="#{html.escape(anchor, quote=True)}">{re.sub("<[^>]+>", "", title)}</a>'
                      for anchor, title in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html))
        # Export Markdown directory links as explicit files so downloads work offline too.
        body_html = re.sub(r'href="([^":#?]+/)"', lambda m: 'href="' + m[1] + 'index.html"', body_html)
        layout = meta.get('layout')
        is_portal = layout in ('portal', 'resources', 'events')
        if is_portal:
            portal_data = json.loads((ROOT / 'data/portal.json').read_text(encoding='utf-8'))
            if portal_data['checked_at'] != meta['checked_at']:
                raise ValueError('portal checked date does not match article')
            renderer = {'portal': render_portal, 'resources': render_links, 'events': render_events}[layout]
            body_html = body_html + renderer(portal_data, sources, meta['source_ids'])
        quick_nav = ''.join(f'<a href="{relative_link(slug, target)}"' +
                            (' aria-current="page"' if slug == target else '') + f'>{label}</a>'
                            for target, label in NAV[:5] if target in known)
        values = {
            'TITLE': html.escape(meta['title']), 'DATE': html.escape(meta['checked_at']),
            'CSS': os.path.relpath('assets/style.css', slug or '.').replace(os.sep, '/'),
            'HOME': relative_link(slug, ''), 'NAV': navigation(slug, known), 'BODY': body_html,
            'TOC': '<nav class="toc" aria-label="この記事の目次">' + toc + '</nav>' if toc else '',
            'SOURCES': render_sources(meta['source_ids'], sources),
            'PAGE_CLASS': 'page-' + (slug.replace('/', '-') or 'home'),
            'ABOUT': relative_link(slug, 'sources'),
            'HEADING': '' if is_portal else '<h1>' + html.escape(meta['title']) + '</h1>',
            'QUICK_NAV': quick_nav,
        }
        page = template
        for key, value in values.items():
            page = page.replace('{{' + key + '}}', value)
        if slug == '' and not all(word in page for word in ('AI', '個人利用', '公開情報')):
            raise ValueError('missing AI notice on homepage')
        dest = output_dir / slug / 'index.html'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_site(ROOT / 'content', ROOT / 'data/sources.json', ROOT / 'dist')
    print(f'Built {len(list((ROOT / "dist").rglob("index.html")))} pages in dist/')
