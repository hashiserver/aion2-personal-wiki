"""Task-focused, escaped HTML views; no client-side runtime."""
from datetime import date
from html import escape


def event_state(event, checked):
    start, end = date.fromisoformat(event['starts_on']), date.fromisoformat(event['ends_on'])
    if checked < start:
        return 'upcoming'
    if checked > end:
        return 'ended'
    return 'ending' if checked == end else 'active'


def source_tag(sid, sources, declared_ids):
    if sid not in sources or sid not in declared_ids:
        raise ValueError(f'undeclared portal source: {sid}')
    s = sources[sid]
    return f'<a class="evidence" href="#source-{escape(sid)}" aria-label="出典を見る：{escape(s["title"], quote=True)}">出典</a>'


def render_portal(data, sources, declared_ids):
    def panel(key, title, description):
        rows = []
        for item in data.get(key, []):
            detail = ''
            if item.get('detail_url'):
                url = item['detail_url']
                if not url.startswith('/') or url.startswith('//'):
                    raise ValueError('detail_url must be a site path')
                detail = f'<a class="detail-link" href="{escape(url, quote=True)}">{escape(item["detail_label"])} <span aria-hidden="true">→</span></a>'
            rows.append(f'<li><div><h3>{escape(item["title"])}</h3><p>{escape(item["description"])}</p>{detail}</div>'
                        f'{source_tag(item["source_id"], sources, declared_ids)}</li>')
        return f'<section class="task-panel" id="{key}" aria-labelledby="{key}-title"><header><h2 id="{key}-title">{title}</h2><p>{description}</p></header><ul>{"".join(rows)}</ul></section>'
    exchanges = ''.join(
        f'<li><div><h3>{escape(item["title"])}</h3><p>{escape(item["description"])}</p></div>'
        f'{source_tag(item["source_id"], sources, declared_ids)}</li>'
        for item in data.get('exchanges', []))
    exchange_note = ('<details class="guide-note" id="exchanges"><summary>通貨の交換候補を見る</summary>'
                     '<p>購入上限と更新周期は商品ごとに異なります。交換前にゲーム内の残数を確認してください。</p>'
                     f'<ul class="resource-list">{exchanges}</ul></details>') if exchanges else ''
    active = sorted((item for item in data.get('events', []) if event_state(item, date.fromisoformat(data['checked_at'])) in ('active', 'ending')), key=lambda item: item['ends_on'])
    notice = ''
    if active:
        item = active[0]
        notice = ('<a class="event-notice" href="/events/"><strong>開催中イベント</strong><span>' + escape(item['title']) + '：' + escape(item['short_end']) + '</span><span class="notice-action">期限・受取を確認</span></a>')
    return (notice + '<div class="task-columns">' +
            panel('daily', '毎日確認', '受取と日ごとの報酬枠を確認。') +
            panel('accumulating', '上限前に消化', '毎日補充。残数に余裕があればまとめて消化。') +
            panel('weekly', '週の期限までに', '週の残数と購入枠を確認。') +
            panel('optional', '開催時・余裕があれば', '出現状況や目的に合わせて参加。') + '</div>' +
            '<aside class="plain-note"><strong>リセットの時刻について</strong><p>出席簿は毎日16:00 JST。その他はゲーム内の残り時間を優先してください。すべてを毎日消化する必要はありません。</p></aside>' +
            exchange_note + '<div class="related"><a href="/events/">開催中イベントと受取期限を見る</a><a href="/links/">職業ビルド・マップ・計算機を探す</a></div>')


def render_links(data, sources, declared_ids):
    e = lambda v: escape(str(v), quote=True)
    def link(sid, text):
        source_tag(sid, sources, declared_ids)
        return f'<a class="resource-link" href="{e(sources[sid]["url"])}" rel="noreferrer" aria-label="{e(text)}：{e(sources[sid]["title"])}（外部サイト）">{e(text)}<span class="external-label" aria-hidden="true">外部サイト ↗</span></a>'
    classes = []
    for item in data.get('classes', []):
        classes.append(f'<li><h3>{e(item["name"])}</h3><div class="class-actions">{link(item["leveling"], "育成中")}{link(item["pve"], "Lv45・PvE")}</div></li>')
    alternatives = ''.join(link(i['alternative'], i['name']) for i in data.get('classes', []))
    tools = []
    for item in data.get('tools', []):
        sid = item['source_id']
        tools.append(f'<li><div><h3>{link(sid,item["title"])}</h3><p>{e(item["description"])}</p></div>'
                     f'{source_tag(sid,sources,declared_ids)}</li>')
    return ('<section id="builds"><h2>職業別ビルド</h2><p>配分はgaming.toolsへ直接。自分のキャラLvと、周回・ボス・パーティの用途を合わせてください。</p>'
            f'<ul class="class-list">{"".join(classes)}</ul></section>'
            f'<details class="guide-note" id="guide-notes"><summary>ガイドによって構成が違うときは？</summary><p>装備・アルカナ込みのスキルLv16〜20目標と、追加ポイントなしの初期配分は前提が違います。同じ用途・手持ちの条件を揃えて読み比べてください。当サイトでは最適火力を実測していません。</p><p>別の回し方を調べる海外ガイド（英語）：</p><div class="resource-pairs">{alternatives}</div></details>'
            f'<section id="tools"><h2>マップ・計画ツール</h2><ul class="resource-list">{"".join(tools)}</ul></section>'
            '<section id="guides"><h2>初心者向けの調べ先</h2><p>カバン整理・強化・ディーヴァニオンの詳しい説明は、各攻略サイトで確認できます。</p><div class="resource-pairs">' +
            ''.join(link(item['source_id'], item['title']) for item in data.get('guides', [])) + '</div></section>')


def render_events(data, sources, declared_ids):
    labels = {'active': '開催中', 'upcoming': '開催予定', 'ending': '終了日・公式確認', 'ended': '終了'}
    items = []
    for item in data['events']:
        sid = item['source_id']; source_tag(sid,sources,declared_ids)
        state = event_state(item,date.fromisoformat(data['checked_at']))
        items.append(f'<article class="event-item"><div class="event-heading"><span class="status {state}">{labels[state]}</span><h2>{escape(item["title"])}</h2></div>'
                     f'<dl><div><dt>期間</dt><dd>{escape(item["period"])}</dd></div>'
                     f'<div><dt>やること</dt><dd>{escape(item["description"])}</dd></div>'
                     f'<div><dt>期限・注意</dt><dd>{escape(item["deadline"])}</dd></div></dl>'
                     f'<a class="resource-link" href="{escape(sources[sid]["url"],quote=True)}" rel="noreferrer">報酬・条件を公式で確認 <span class="external-label">外部サイト ↗</span></a></article>')
    return ''.join(items)


