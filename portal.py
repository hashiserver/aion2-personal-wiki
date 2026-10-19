"""Small, escaped HTML views for the static portal homepage."""
from datetime import date
from html import escape


def event_state(event, checked):
    start, end = date.fromisoformat(event['starts_on']), date.fromisoformat(event['ends_on'])
    if checked < start:
        return 'upcoming'
    if checked > end:
        return 'ended'
    return 'ending' if checked == end else 'active'


def render_portal(data, sources, declared_ids):
    checked = date.fromisoformat(data['checked_at'])
    e = lambda value: escape(str(value), quote=True)

    def source_link(sid):
        if sid not in sources or sid not in declared_ids:
            raise ValueError(f'undeclared portal source: {sid}')
        return sources[sid]

    def tag(sid):
        source = source_link(sid)
        return f'<a class="tag source-tag" href="#source-{e(sid)}">{e(source["tag"])}</a>'

    events = []
    labels = {'active': '確認日時点で開催', 'upcoming': '開催予定', 'ending': '終了日・公式確認', 'ended': '終了'}
    for item in data['events']:
        source = source_link(item['source_id'])
        state = event_state(item, checked)
        events.append(f'<article class="event-card"><div class="card-top"><span class="status {state}">{labels[state]}</span>'
                      f'<span class="card-category">{e(item["category"])}</span></div>'
                      f'<h3>{e(item["title"])}</h3><p class="event-date">{e(item["period"])}</p>'
                      f'<p>{e(item["description"])}</p><p class="deadline">{e(item["deadline"])}</p>'
                      f'<div class="card-bottom"><a href="{e(source["url"])}" rel="noreferrer">公式の詳細 <span aria-hidden="true">↗</span></a>'
                      f'{tag(item["source_id"])}</div></article>')
    tools = []
    for i, item in enumerate(data['tools'], 1):
        source = source_link(item['source_id'])
        tools.append(f'<article class="tool-card"><span class="tool-number">{i:02}</span><div>'
                     f'<h3><a href="{e(source["url"])}" rel="noreferrer">{e(item["title"])} <span aria-hidden="true">↗</span></a></h3>'
                     f'<p>{e(item["description"])}</p>{tag(item["source_id"])}</div></article>')

    def routine(key, title, sub, href):
        rows = []
        for item in data.get(key, []):
            rows.append(f'<li><span class="routine-marker" aria-hidden="true"></span><div><strong>{e(item["title"])}</strong>'
                        f'<p>{e(item["description"])}</p></div><span class="routine-source">{tag(item["source_id"])}</span></li>')
        return (f'<section class="routine-panel" id="{key}" aria-labelledby="{key}-heading"><div class="panel-heading">'
                f'<span class="eyebrow">{e(sub)}</span><h2 id="{key}-heading">{e(title)}</h2></div>'
                f'<ul class="routine-list">{"".join(rows)}</ul><a class="panel-more" href="{href}">条件・回数を詳しく見る <span aria-hidden="true">→</span></a></section>')

    return f'''<div class="portal-hero"><div><p class="eyebrow">YOUR DAILY GATEWAY TO ATREIA</p>
<h1>今日の冒険を、<br>迷わず始めよう。</h1><p class="hero-description">日課と週課、見逃したくないイベント。<br>必要な情報とツールを、この場所から。</p>
<div class="hero-actions"><a class="button primary" href="#daily">毎日やること</a><a class="button secondary" href="#weekly">毎週やること <span aria-hidden="true">↗</span></a></div></div>
<aside class="featured-tool"><span class="eyebrow">PICK UP RESOURCE</span><h2>AION 2<br>Global Database</h2><p>ビルドも、マップも、育成計画も。</p><a href="https://aion2.gaming.tools/ja" rel="noreferrer">gaming.tools を開く <span aria-hidden="true">↗</span></a><span class="featured-note">外部サイト / 非公式</span></aside></div>
<div class="portal-notice"><span class="notice-label">INFORMATION</span><p>日本・グローバル版向けの非公式ポータル。AIで公開情報を収集・整理した個人利用向けメモです。</p><span class="checked">情報確認 {e(data['checked_at'])} JST</span></div>
<section id="events" class="portal-section" aria-labelledby="events-heading"><div class="section-heading"><div><p class="eyebrow">DON’T MISS</p><h2 id="events-heading">イベント・受取期限</h2></div><a href="events/index.html">一覧・注意点 <span aria-hidden="true">→</span></a></div><div class="event-grid">{''.join(events)}</div><p class="section-note">開催状況は確認日時点。最新の変更・正確な終了時刻は各公式案内をご確認ください。</p></section>
<div class="routine-grid">{routine('daily', '毎日、ここをチェック', 'DAILY ROUTINE', 'routine/index.html#毎日の確認')}{routine('weekly', '週の終わりに忘れずに', 'WEEKLY ROUTINE', 'routine/index.html#毎週の確認')}</div>
<section id="tools" class="portal-section" aria-labelledby="tools-heading"><div class="section-heading"><div><p class="eyebrow">EXPLORE & PLAN</p><h2 id="tools-heading">冒険に役立つツール</h2></div><a href="links/index.html">リンク集 <span aria-hidden="true">→</span></a></div><div class="tool-grid">{''.join(tools)}</div></section>
<section class="build-banner"><div><p class="eyebrow">FIND YOUR PLAYSTYLE</p><h2>ビルドは、目的に合わせて。</h2><p>育成中とLv45、ソロとパーティ。複数ガイドの前提・違いを整理しました。</p></div><a class="button primary" href="build-comparison/index.html">8職のガイド比較 <span aria-hidden="true">→</span></a></section>
<section class="portal-section" aria-labelledby="notes-heading"><div class="section-heading"><div><p class="eyebrow">BEGINNER NOTES</p><h2 id="notes-heading">困ったときのメモ</h2></div></div><div class="note-grid"><a href="inventory/index.html"><span>01</span><strong>カバンがいっぱい</strong><p>残す・倉庫・抽出の目安</p></a><a href="progression/index.html"><span>02</span><strong>育成が進まない</strong><p>次に確認する条件を整理</p></a><a href="daevanion/index.html"><span>03</span><strong>ポイント配分に迷う</strong><p>Lv22の参考記録と現行ツール</p></a></div></section>'''
