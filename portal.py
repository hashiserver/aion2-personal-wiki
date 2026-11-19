"""Task-focused, escaped HTML views; no client-side runtime."""
from collections import Counter
from datetime import date, datetime, time, timedelta
from html import escape
from zoneinfo import ZoneInfo


JST = ZoneInfo('Asia/Tokyo')
NOTICE_CATEGORIES = {'アップデート', 'メンテナンス'}


def event_schedule(event):
    """Expose unambiguous timestamps while leaving unknown maintenance times open."""
    def boundaries(field):
        day = date.fromisoformat(event[field + '_on'])
        midnight = datetime.combine(day, time.min, JST)
        exact = event.get(field + '_at')
        if exact is None:
            return midnight, midnight + timedelta(days=1)
        instant = datetime.fromisoformat(exact.removesuffix('Z') + ('+00:00' if exact.endswith('Z') else ''))
        if instant.tzinfo is None or instant.astimezone(JST).date() != day:
            raise ValueError(f'invalid {field}_at for event: {event["title"]}')
        return instant, instant

    start, active = boundaries('starts')
    ending, end = boundaries('ends')
    if end <= start:
        raise ValueError(f'invalid event period: {event["title"]}')
    warning = end - timedelta(days=1) if ending == end else ending
    attrs = dict(start=start, active=active, warning=warning, end=end)
    result = ' '.join(f'data-{key}="{int(value.timestamp() * 1000)}"' for key, value in attrs.items())
    return result + (' data-exact-end' if ending == end else '')


def scheduled_events(data):
    ids = Counter()
    for item in data.get('events', []):
        sid = item['source_id']
        ids[sid] += 1
        suffix = f'-{ids[sid]}' if ids[sid] > 1 else ''
        yield item, 'event-' + sid + suffix


def source_tag(sid, sources, declared_ids):
    if sid not in sources or sid not in declared_ids:
        raise ValueError(f'undeclared portal source: {sid}')
    s = sources[sid]
    return f'<a class="evidence" href="#source-{escape(sid)}" aria-label="出典を見る：{escape(s["title"], quote=True)}">出典</a>'


def render_portal(data, sources, declared_ids):
    """Keep the routine and its limits visible, with details available on demand."""
    def panel(key, title, description, collapsed=False):
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
            if collapsed:
                rows.append(f'<li><div><h3>{escape(item["title"])}</h3><p>{escape(item["description"])}</p>{detail}</div>{evidence}</li>')
                continue
            summary = item.get('summary', item['description'])
            more = ''
            if summary != item['description']:
                more = (f'<details class="task-detail"><summary>進め方</summary>'
                        f'<p>{escape(item["description"])}</p>{detail}</details>')
            else:
                more = detail
            rows.append(f'<li><div><h3>{escape(item["title"])}</h3><p>{escape(summary)}</p>{more}</div>{evidence}</li>')
        contents = '<ul role="list">' + ''.join(rows) + '</ul>'
        if collapsed:
            return (f'<details class="task-panel collapsible-panel" id="{key}">'
                    f'<summary class="panel-summary"><span class="panel-heading">{title}</span></summary>'
                    f'{contents}</details>')
        return (f'<section class="task-panel" id="{key}" aria-labelledby="{key}-title">'
                f'<header><h2 id="{key}-title">{title}</h2><p>{description}</p></header>'
                f'{contents}</section>')

    exchanges = ''.join(
        f'<li><div><h3>{escape(item["title"])}</h3><p>{escape(item["description"])}</p></div>'
        f'{source_tag(item["source_id"], sources, declared_ids)}</li>'
        for item in data.get('exchanges', []))
    exchange_note = ('<details class="guide-note" id="exchanges"><summary>通貨の交換候補を見る</summary>'
                     '<p>購入上限と更新周期は商品ごとに異なります。交換前にゲーム内の残数を確認してください。</p>'
                     f'<ul class="resource-list">{exchanges}</ul></details>') if exchanges else ''

    deadlines = []
    for item, event_id in scheduled_events(data):
        if item.get('category') in NOTICE_CATEGORIES:
            continue
        deadlines.append(
            f'<li hidden {event_schedule(item)}><a href="/events/#{escape(event_id, quote=True)}">'
            f'<strong>{escape(item["title"])}</strong><span>{escape(item["short_end"])}</span>'
            '<span class="deadline-warning" hidden>期限を確認</span></a></li>')
    notice = ('<section class="deadline-panel" aria-labelledby="deadline-title">'
              '<h2 id="deadline-title">イベント・受取期限</h2>'
              '<ul id="home-deadlines" role="list">' + ''.join(deadlines) + '</ul>'
              '<div class="deadline-links"><a href="/events/#current-events">開催情報を見る</a>'
              '<a href="/events/#rewards">クーポン・特典</a></div></section>')

    sections = [('daily', '毎日'), ('weekly', '週課'), ('accumulating', '上限管理'),
                ('optional', 'その他'), ('exchanges', '交換')]
    quick = '<nav class="section-nav" aria-label="このページの項目">' + ''.join(
        f'<a href="#{key}">{label}</a>' for key, label in sections if data.get(key)) + '</nav>'
    return (quick + '<div class="task-columns">' +
            panel('daily', '毎日確認', '日次リセットは16:00 JST') + notice +
            panel('weekly', '週の期限までに', '週次リセットは水曜16:00 JST') +
            panel('accumulating', '上限前に消化', '残り枠と回復タイミングを確認') +
            '</div>' + panel('optional', '開催時・余裕があれば', '', collapsed=True) +
            exchange_note + '<div class="related"><a href="/progression/">IL別の次の育成目標</a>'
            '<a href="/gear/chanter/">チャンターの装備厳選</a>'
            '<a href="/pets/">ショップで買うペット</a><a href="/links/">ビルド・マップ・計算機</a></div>')


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
    """Keep events, claimable rewards and operational notices in distinct sections."""
    events, rewards, notices = [], [], []
    for item, event_id in scheduled_events(data):
        sid = item['source_id']
        source_tag(sid, sources, declared_ids)
        title = escape(item['title'])
        href = escape(sources[sid]['url'], quote=True)
        if item.get('category') in NOTICE_CATEGORIES:
            notices.append((item['starts_on'], f'<li><a href="{href}" rel="noreferrer">{title}</a></li>'))
            continue

        is_reward = item.get('category') in ('郵便・受取', 'クーポン')
        group = rewards if is_reward else events
        action = item.get('action', item['description'])
        details = (f'<div><dt>内容</dt><dd>{escape(item["description"])}</dd></div>'
                   if action != item['description'] else '')
        basis = escape(item.get('status_basis', ''), quote=True)
        group.append((item['ends_on'], (
            f'<article class="event-item" id="{event_id}" {event_schedule(item)} '
            f'data-event-group="{"rewards" if is_reward else "current-events"}" data-status-basis="{basis}">'
            f'<div class="event-heading"><span class="status" hidden></span><h3>{title}</h3></div>'
            f'<p class="event-deadline">{escape(item["short_end"])}</p>'
            f'<p class="event-action">{escape(action)}</p>'
            '<details class="event-details"><summary>期間・条件・公式情報</summary>'
            f'<dl><div><dt>期間</dt><dd>{escape(item["period"])}</dd></div>{details}'
            f'<div><dt>注意事項</dt><dd>{escape(item["deadline"])}</dd></div></dl>'
            f'<a class="resource-link" href="{href}" rel="noreferrer">'
            '公式・参照元を確認 <span class="external-label">外部サイト ↗</span></a>'
            '</details></article>'
        )))

    def section(key, title, items, empty):
        return (f'<section class="event-group" id="{key}"><h2>{title}</h2>'
                f'<div class="event-list">{"".join(card for _, card in sorted(items))}</div>'
                f'<p class="event-empty" hidden>{empty}</p></section>')

    return ('<p class="event-context">時刻は確認できたものを日本時間（JST）で表示します。'
            'メンテナンス前後の期限は、該当する地域の告知を確認してください。</p>'
            '<noscript><p>開催状況は各項目に記載した期限をご確認ください。</p></noscript>'
            '<nav class="section-nav" aria-label="イベントの項目">'
            '<a href="#current-events">イベント</a><a href="#rewards">クーポン・受取</a>'
            '<a href="#update-notes">更新・メンテナンス</a></nav>'
            + section('current-events', 'イベント', events, '掲載中のイベントはありません。')
            + section('rewards', 'クーポン・受取', rewards, '掲載中のクーポン・特典はありません。')
            + '<details class="event-archive" id="past-events" hidden>'
            '<summary>終了したイベント・特典</summary><div class="event-archive-list"></div></details>'
            + '<section class="event-group" id="update-notes"><h2>更新・メンテナンス</h2>'
            + ('<ul class="event-notices">' + ''.join(link for _, link in sorted(notices, reverse=True)[:3]) +
               '</ul>' if notices else '') + '</section>')
