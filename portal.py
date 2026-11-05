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
    """Show today's actions first; leave less frequent actions discoverable."""
    def panel(key, title, description, expanded=False):
        items = data.get(key, [])
        if not items:
            return ''
        rows = []
        for item in items:
            detail = ''
            if item.get('detail_url'):
                url = item['detail_url']
                if not url.startswith('/') or url.startswith('//'):
                    raise ValueError('detail_url must be a site path')
                detail = f'<a class="detail-link" href="{escape(url, quote=True)}">{escape(item["detail_label"])} <span aria-hidden="true">→</span></a>'
            evidence = source_tag(item['source_id'], sources, declared_ids)
            if expanded:
                rows.append(f'<li><div><h3>{escape(item["title"])}</h3><p>{escape(item["description"])}</p>{detail}</div>{evidence}</li>')
            else:
                rows.append(f'<li class="compact-task"><details class="task-detail">'
                            f'<summary>{escape(item["title"])}</summary>'
                            f'<div class="task-body"><p>{escape(item["description"])}</p>{detail}{evidence}</div>'
                            '</details></li>')
        contents = '<ul>' + ''.join(rows) + '</ul>'
        if expanded:
            return (f'<section class="task-panel" id="{key}" aria-labelledby="{key}-title">'
                    f'<header><h2 id="{key}-title">{title}</h2><p>{description}</p></header>'
                    f'{contents}</section>')
        return (f'<details class="task-panel collapsible-panel" id="{key}">'
                f'<summary class="panel-summary"><span class="panel-summary-main">'
                f'<span class="panel-heading">{title}</span><span class="panel-description">{description}</span>'
                f'</span><span class="panel-count">{len(items)}件</span></summary>{contents}</details>')

    exchanges = ''.join(
        f'<li><div><h3>{escape(item["title"])}</h3><p>{escape(item["description"])}</p></div>'
        f'{source_tag(item["source_id"], sources, declared_ids)}</li>'
        for item in data.get('exchanges', []))
    exchange_note = ('<details class="guide-note" id="exchanges"><summary>通貨の交換候補を見る</summary>'
                     '<p>購入上限と更新周期は商品ごとに異なります。交換前にゲーム内の残数を確認してください。</p>'
                     f'<ul class="resource-list">{exchanges}</ul></details>') if exchanges else ''

    checked = date.fromisoformat(data['checked_at'])
    active = sorted((item for item in data.get('events', [])
                     if event_state(item, checked) in ('active', 'ending')),
                    key=lambda item: item['ends_on'])
    notice = ''
    if active:
        item = active[0]
        notice = ('<a class="event-notice" href="/events/"><strong>近日の期限</strong><span>' +
                  escape(item['title']) + '：' + escape(item['short_end']) +
                  '</span><span class="notice-action">イベントを確認</span></a>')

    quick = ('<nav class="section-nav" aria-label="このページの項目">'
             '<a href="#daily">毎日</a><a href="#accumulating">上限管理</a>'
             '<a href="#weekly">週課</a><a href="#optional">その他</a>'
             '<a href="#exchanges">交換</a></nav>')
    return (notice + quick +
            '<div class="task-columns">' +
            panel('daily', '毎日確認', '受取と日ごとの報酬枠を確認。', expanded=True) +
            panel('accumulating', '上限前に消化', '毎日補充。上限が近づいたら優先。') +
            panel('weekly', '週の期限までに', '週の残数・購入枠を確認。') +
            panel('optional', '開催時・余裕があれば', '出現状況と目的に合わせて参加。') + '</div>' +
            '<aside class="plain-note"><strong>リセットの時刻について</strong><p>出席簿は毎日16:00 JST。その他はゲーム内の残り時間を優先してください。すべてを毎日消化する必要はありません。</p></aside>' +
            exchange_note + '<div class="related"><a href="/duty/">任務・指令の受け方</a>'
            '<a href="/events/">イベントと受取期限</a><a href="/links/">ビルド・マップ・計算機</a></div>')


def render_links(data, sources, declared_ids):
    e = lambda v: escape(str(v), quote=True)

    def link(sid, text):
        source_tag(sid, sources, declared_ids)
        return (f'<a class="resource-link" href="{e(sources[sid]["url"])}" rel="noreferrer" '
                f'aria-label="{e(text)}：{e(sources[sid]["title"])}（外部サイト）">'
                f'{e(text)}<span class="external-label" aria-hidden="true">外部サイト ↗</span></a>')

    def class_row(item):
        return (f'<li><h3>{e(item["name"])}</h3><div class="class-actions">'
                f'{link(item["leveling"], "育成中")}{link(item["pve"], "Lv45・PvE")}</div></li>')

    classes = data.get('classes', [])
    featured = next((item for item in classes if item['name'] == 'チャンター'), None)
    others = [item for item in classes if item is not featured]
    featured_section = (
        '<section class="featured-build" id="builds"><h2>チャンターのビルド</h2>'
        '<p>用途・スキルポイント・特化段階が異なる場合は、リンク先の完成形をそのまま適用しないでください。</p>'
        f'<ul class="class-list"><li>{class_row(featured)[4:-5]}</li></ul></section>'
    ) if featured else ''
    other_section = (
        f'<details class="guide-note other-builds" id="other-builds"><summary>その他の職業ビルド（{len(others)}職）</summary>'
        f'<ul class="class-list">{"".join(class_row(i) for i in others)}</ul></details>'
    ) if others else ''
    if not featured:
        other_section = ('<section id="builds"><h2>職業別ビルド</h2><ul class="class-list">' +
                         ''.join(class_row(i) for i in classes) + '</ul></section>')

    alternatives = ''.join(link(i['alternative'], i['name']) for i in classes)
    tools = []
    for item in data.get('tools', []):
        sid = item['source_id']
        tools.append(f'<li><div><h3>{link(sid,item["title"])}</h3><p>{e(item["description"])}</p></div>'
                     f'{source_tag(sid,sources,declared_ids)}</li>')
    return (featured_section + other_section +
            f'<details class="guide-note" id="guide-notes"><summary>ビルド構成や海外ガイドを比較</summary>'
            '<p>追加ポイントや装備の有無で最適な配分は変わります。当サイトは最適DPSを実測したものではありません。</p>'
            f'<div class="resource-pairs">{alternatives}</div></details>'
            f'<section id="tools"><h2>マップ・計画ツール</h2><ul class="resource-list">{"".join(tools)}</ul></section>'
            '<details class="guide-note" id="guides"><summary>初心者向け攻略を探す</summary>'
            '<p>カバン整理・強化・ディーヴァニオンの詳細は攻略サイトで確認できます。</p>'
            '<div class="resource-pairs">' +
            ''.join(link(item['source_id'], item['title']) for item in data.get('guides', [])) +
            '</div></details>')


def render_events(data, sources, declared_ids):
    """Active deadlines are prominent; ended items and long notes stay accessible."""
    labels = {'active': '開催中', 'upcoming': '開催予定', 'ending': '終了日・公式確認', 'ended': '終了'}
    grouped = {'current': [], 'upcoming': [], 'ended': []}
    checked = date.fromisoformat(data['checked_at'])
    for item in data.get('events', []):
        sid = item['source_id']
        source_tag(sid, sources, declared_ids)
        state = event_state(item, checked)
        group = 'current' if state in ('active', 'ending') else state
        period = escape(item['period'])
        description = escape(item['description'])
        deadline = escape(item['deadline'])
        short_end = escape(item['short_end'])
        article = (
            f'<article class="event-item"><div class="event-heading">'
            f'<span class="status {state}">{labels[state]}</span><h3>{escape(item["title"])}</h3></div>'
            f'<p class="event-deadline">期限の目安：{short_end}</p>'
            '<details class="event-details"><summary>報酬・条件・注意事項</summary>'
            f'<dl><div><dt>期間</dt><dd>{period}</dd></div>'
            f'<div><dt>やること</dt><dd>{description}</dd></div>'
            f'<div><dt>期限・注意</dt><dd>{deadline}</dd></div></dl>'
            f'<a class="resource-link" href="{escape(sources[sid]["url"],quote=True)}" rel="noreferrer">'
            '公式・参照元を確認 <span class="external-label">外部サイト ↗</span></a>'
            '</details></article>')
        grouped[group].append((item['ends_on'], article))
    current = ''.join(card for _, card in sorted(grouped['current']))
    upcoming = ''.join(card for _, card in sorted(grouped['upcoming']))
    ended = ''.join(card for _, card in sorted(grouped['ended'], reverse=True))
    result = ('<p class="event-context">表示状態は確認日 ' + escape(data['checked_at']) +
              ' 時点の記録です。日本・Asiaへの適用や終了時刻は公式・ゲーム内で再確認してください。</p>')
    result += (f'<section class="event-group" id="current-events"><h2>開催中・期限に注意 '
               f'<span class="group-count">{len(grouped["current"])}件</span></h2>{current}</section>'
               if current else '<p class="event-empty">確認日時点で開催中として登録されたイベントはありません。</p>')
    if upcoming:
        result += (f'<section class="event-group" id="upcoming-events"><h2>開催予定 '
                   f'<span class="group-count">{len(grouped["upcoming"])}件</span></h2>{upcoming}</section>')
    if ended:
        result += (f'<details class="event-archive" id="past-events"><summary>'
                   f'終了したイベント（{len(grouped["ended"])}件）</summary>'
                   f'<div class="event-archive-list">{ended}</div></details>')
    return result
