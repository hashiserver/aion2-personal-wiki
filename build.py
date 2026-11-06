"""Generate a lightweight static wiki; no network calls or runtime JavaScript."""
import html
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shutil
from urllib.parse import urlsplit, urlunsplit

import markdown2
from portal import render_portal, render_links, render_events

ROOT = Path(__file__).resolve().parent
NAV = [('', '日課・週課'), ('progression', 'IL育成'), ('duty', '任務・指令'), ('events', 'イベント'), ('gear', '装備厳選'), ('links', 'リンク集')]
MARKER = re.compile(r'\[\[source:([a-z0-9-]+)\]\]')


def load_article(path: Path) -> tuple[dict, str]:
    first, body = path.read_text(encoding='utf-8').split('\n', 1)
    meta = json.loads(first)
    for field in ('slug', 'title', 'checked_at', 'source_ids'):
        if field not in meta:
            raise ValueError(f'missing {field}: {path}')
    return meta, body.strip()


def relative_link(slug: str, target: str) -> str:
    # Match Workers' force-trailing-slash routes without a redirect hop.
    return f'/{target}/' if target else '/'


def canonical_link(slug: str, ref: str, known_slugs: set[str]) -> str:
    url = urlsplit(ref)
    if url.scheme or url.netloc or not url.path:
        return ref
    path = posixpath.normpath(posixpath.join('/' + slug, url.path))
    if path.endswith('/index.html'):
        path = path[:-len('/index.html')]
    target = path.strip('/')
    if target not in known_slugs:
        return ref
    return urlunsplit(('', '', relative_link(slug, target), url.query, url.fragment))


def navigation(slug: str, known_slugs: set[str]) -> str:
    def item(target, title):
        if target not in known_slugs:
            return ''
        current = ' aria-current="page" class="current"' if target == slug else ''
        return f'<a href="{relative_link(slug, target)}"{current}>{html.escape(title)}</a>'
    primary = ''.join(item(s, t) for s, t in NAV)
    return f'<nav aria-label="ページ一覧">{primary}</nav>'


GEAR_CLASSES = [
    ('chanter', 'チャンター'),
    ('gladiator', 'グラディエーター'),
    ('templar', 'テンプラー'),
    ('assassin', 'アサシン'),
    ('ranger', 'レンジャー'),
    ('sorcerer', 'ソーサラー'),
    ('spiritmaster', 'スピリットマスター'),
    ('cleric', 'クレリック'),
]


def gear_subnavigation(slug: str, known_slugs: set[str]) -> str:
    """Secondary navigation shared by gear overview and each class page."""
    if slug != 'gear' and not slug.startswith('gear/'):
        return ''
    tabs = [('gear', '全体方針'), ('gear/transfer', '強化・継承')] + [('gear/' + key, label) for key, label in GEAR_CLASSES]
    links = []
    for target, label in tabs:
        if target not in known_slugs:
            continue
        selected = ' aria-current="page"' if target == slug else ''
        links.append(f'<a href="{relative_link(slug, target)}"{selected}>{html.escape(label)}</a>')
    return ('<nav class="gear-subnav" aria-label="装備厳選：クラス切り替え">'
            '<span class="gear-subnav-title">クラス別の厳選表</span>'
            '<div class="gear-subnav-links">' + ''.join(links) + '</div></nav>')


def render_sources(ids: list[str], sources: dict) -> str:
    rows = []
    for sid in ids:
        s = sources[sid]
        date = f'公開日 {s["published_at"]}' if s['published_at'] else '公開日不明'
        rows.append(f'<li id="source-{sid}"><span class="tag">{html.escape(s["tag"])}</span> '
                    f'<a href="{html.escape(s["url"], quote=True)}" rel="noreferrer">{html.escape(s["title"])} <span class="external-label">外部サイト ↗</span></a>'
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
    css_bytes = (ROOT / 'assets/style.css').read_bytes()
    css_name = f'style.{hashlib.sha256(css_bytes).hexdigest()[:12]}.css'
    for old_css in (output_dir / 'assets').glob('style.*.css'):
        if old_css.name != css_name:
            old_css.unlink()
    (output_dir / 'assets' / css_name).write_bytes(css_bytes)
    # Keep the former URL working for an already-open, older document.
    shutil.copyfile(ROOT / 'assets/style.css', output_dir / 'assets/style.css')
    shutil.copyfile(ROOT / '_redirects', output_dir / '_redirects')
    # Only content-addressed CSS gets an immutable cache. HTML revalidates.
    header_rules = [f'{relative_link("", slug)}\n  Cache-Control: public, max-age=0, must-revalidate' for slug in sorted(known)]
    header_rules.append(f'/assets/{css_name}\n  Cache-Control: public, max-age=31536000, immutable')
    (output_dir / '_headers').write_text('\n\n'.join(header_rules) + '\n', encoding='utf-8')
    template = (ROOT / 'templates/page.html').read_text(encoding='utf-8')
    for meta, body in articles:
        slug = meta['slug']
        body_html = str(markdown2.markdown(body, extras=['tables', 'header-ids'], safe_mode='escape'))
        body_html = MARKER.sub(lambda m: f'<a class="tag source-tag" href="#source-{m[1]}" title="{html.escape(sources[m[1]]["region"] + " / " + sources[m[1]]["scope"], quote=True)}">{html.escape(sources[m[1]]["tag"])}</a>', body_html)
        body_html = re.sub(r'<table>', '<div class="table-scroll" tabindex="0" role="region" aria-label="比較表。横にスクロールできます"><table>', body_html)
        body_html = body_html.replace('</table>', '</table></div>')
        toc = ''.join(f'<a href="#{html.escape(anchor, quote=True)}">{re.sub("<[^>]+>", "", title)}</a>'
                      for anchor, title in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html))
        layout = meta.get('layout')
        is_portal = layout in ('portal', 'resources', 'events')
        if is_portal:
            portal_data = json.loads((ROOT / 'data/portal.json').read_text(encoding='utf-8'))
            if portal_data['checked_at'] != meta['checked_at']:
                raise ValueError('portal checked date does not match article')
            renderer = {'portal': render_portal, 'resources': render_links, 'events': render_events}[layout]
            rendered = renderer(portal_data, sources, meta['source_ids'])
            if layout == 'portal':
                # Daily actions belong above archival patch notes. Leave the Markdown
                # untouched so the scheduled content updater keeps its source of truth.
                body_html = (rendered +
                             '<details class="update-archive" id="updates">'
                             '<summary>更新履歴・地域別の適用状況を読む</summary>'
                             '<div class="update-archive-body">' + body_html + '</div></details>')
            elif layout == 'events':
                # Long official patch summaries remain searchable without pushing
                # the time-sensitive event list below the fold.
                body_html = (rendered +
                             '<details class="update-archive" id="update-notes">'
                             '<summary>パッチ詳細・過去のお知らせを読む</summary>'
                             '<div class="update-archive-body">' + body_html + '</div></details>')
            else:
                body_html = body_html + rendered
        quick_nav = ''.join(f'<a href="{relative_link(slug, target)}"' +
                            (' aria-current="page"' if slug == target else '') + f'>{label}</a>'
                            for target, label in NAV if target in known)
        values = {
            'TITLE': html.escape(meta['title']), 'DATE': html.escape(meta['checked_at']),
            'CSS': f'/assets/{css_name}',
            'HOME': relative_link(slug, ''), 'NAV': navigation(slug, known), 'BODY': gear_subnavigation(slug, known) + body_html,
            'TOC': '<nav class="toc" aria-label="この記事の目次">' + toc + '</nav>' if toc else '',
            'SOURCES': render_sources(meta['source_ids'], sources),
            'PAGE_CLASS': 'page-' + (slug.replace('/', '-') or 'home') + (' page-gear' if slug.startswith('gear/') else ''),
            'ABOUT': relative_link(slug, 'sources'),
            'HEADING': '' if is_portal else '<h1>' + html.escape(meta['title']) + '</h1>',
            'QUICK_NAV': quick_nav,
        }
        page = template
        for key, value in values.items():
            page = page.replace('{{' + key + '}}', value)
        page = re.sub(r'href="([^"]+)"', lambda m: 'href="' + html.escape(
            canonical_link(slug, html.unescape(m[1]), known), quote=True) + '"', page)
        if slug == '' and not all(word in page for word in ('AI', '個人利用', '公開情報')):
            raise ValueError('missing AI notice on homepage')
        dest = output_dir / slug / 'index.html'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_site(ROOT / 'content', ROOT / 'data/sources.json', ROOT / 'dist')
    print(f'Built {len(list((ROOT / "dist").rglob("index.html")))} pages in dist/')

