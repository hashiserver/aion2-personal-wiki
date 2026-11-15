"""Server-rendered pet priority checklist; filtering/state are optional client enhancements."""
from collections import Counter
from html import escape

GROUPS = {
    "shop": "購入・箱中心",
    "elyos": "天族側の狩場",
    "dungeon": "ID（ダンジョン）産",
    "rare": "狩場少数",
}
GENERA = {"知性", "野性", "自然", "変形"}


def render_pet_tracker(catalog: dict, sources: dict, allowed_ids: list[str]) -> str:
    pets = catalog["items"]
    if not pets:
        raise ValueError("empty pet catalog")
    names = set()
    rows = []
    counts = Counter()

    for index, item in enumerate(pets):
        name = item["name"]
        if not name or name in names:
            raise ValueError("duplicate or empty pet name: " + name)
        names.add(name)
        genus = item["genus"]
        if genus not in GENERA:
            raise ValueError("unknown pet genus: " + genus)
        groups = item["groups"]
        if not groups or len(set(groups)) != len(groups) or any(g not in GROUPS for g in groups):
            raise ValueError("invalid pet group: " + name)
        for group in groups:
            counts[group] += 1
        if not item.get("notes"):
            raise ValueError("missing pet notes: " + name)
        source_ids = item["source_ids"]
        if not source_ids or any(sid not in allowed_ids or sid not in sources for sid in source_ids):
            raise ValueError("pet source is not declared: " + name)

        pet_id = "pet-check-" + str(index + 1)
        chips = "".join(
            '<span class="pet-chip pet-chip-' + escape(group, quote=True) + '">'
            + escape(GROUPS[group]) + '</span>' for group in groups
        )
        notes = " / ".join(item["notes"])
        # A link to the page's existing source list makes each classification auditable.
        source_id = source_ids[0]
        rows.append(
            '<tr class="pet-row" data-key="' + escape(name, quote=True) + '"'
            ' data-order="' + str(index) + '"'
            ' data-groups="' + escape(" ".join(groups), quote=True) + '"'
            ' data-genus="' + escape(genus, quote=True) + '">'
            '<td><label class="pet-check" for="' + pet_id + '">'
            '<input id="' + pet_id + '" type="checkbox" class="pet-done-input"'
            ' aria-label="' + escape(name, quote=True) + 'を完了済みにする">'
            '<span>完了</span></label></td>'
            '<td class="pet-name-cell"><strong class="pet-name">' + escape(name) + '</strong>'
            '<small>' + escape(genus) + '</small></td>'
            '<td class="pet-chips">' + chips + '</td>'
            '<td class="pet-notes">' + escape(notes) + '</td>'
            '<td><a href="#source-' + escape(source_id, quote=True)
            + '">出典</a></td>'
            '</tr>'
        )

    options = "".join(
        '<option value="' + key + '">' + label + '（' + str(counts[key]) + '）</option>'
        for key, label in GROUPS.items()
    )
    rows_html = "".join(rows)
    headers = ('<thead><tr><th scope="col">済</th><th scope="col">ペット名</th>'
               '<th scope="col">入手区分</th><th scope="col">買う理由・代替入手</th>'
               '<th scope="col">根拠</th></tr></thead>')
    return (
        '<section id="pet-tracker" aria-labelledby="pet-tracker-title">'
        '<h2 id="pet-tracker-title">最優先：購入チェックリスト</h2>'
        '<p>魔族視点で、<strong>購入中心・天族側の狩場・ID産・狩場少数</strong>を一つの表に集約。'
        '同じペットに理由が複数ある場合はラベルを併記しています。'
        '完了は「ペット理解度Lv3になり、これ以上ショップで魂を買わない」を目安にしてください。</p>'
        '<div class="pet-summary" role="status" aria-live="polite">'
        '<strong id="pet-pending-count">' + str(len(rows)) + '</strong><span>未完了</span>'
        '<strong id="pet-done-count">0</strong><span>完了</span>'
        '<strong id="pet-total-count">' + str(len(rows)) + '</strong><span>対象</span>'
        '</div>'
        '<div class="pet-controls">'
        '<label for="pet-search">ペット名を検索'
        '<input id="pet-search" type="search" placeholder="名前を入力" autocomplete="off"></label>'
        '<label for="pet-group">入手区分'
        '<select id="pet-group"><option value="all">すべての最優先</option>'
        + options + '</select></label>'
        '<label for="pet-genus">種族理解度'
        '<select id="pet-genus"><option value="all">すべて</option>'
        + "".join('<option value="' + escape(g) + '">' + escape(g) + '</option>'
                  for g in ("知性", "野性", "自然", "変形")) +
        '</select></label></div>'
        '<p class="pet-local-note">チェックはこのブラウザのlocalStorageにのみ保存。'
        'ログイン・サーバー保存・端末間同期はありません。ブラウザのデータ削除で消える場合があります。</p>'
        '<noscript><p>絞り込みと完了保存にはJavaScriptが必要です。下の一覧は閲覧できます。</p></noscript>'
        '<div class="table-scroll pet-table-wrap" role="region" aria-label="未完了の優先ペット一覧" tabindex="0">'
        '<table id="pet-pending-table">' + headers + '<tbody id="pet-pending-body">' + rows_html
        + '</tbody></table></div>'
        '<p id="pet-empty" class="pet-empty" hidden>条件に一致する未完了のペットはありません。</p>'
        '<details id="pet-completed-panel" class="pet-completed-panel">'
        '<summary>完了済みのペット（<span id="pet-done-summary">0</span>種）— ここでチェックを外すと未完了へ戻せます</summary>'
        '<div class="table-scroll pet-table-wrap" role="region" aria-label="完了済みペット一覧" tabindex="0">'
        '<table id="pet-completed-table">' + headers + '<tbody id="pet-completed-body"></tbody></table></div>'
        '<p id="pet-done-empty" class="pet-empty">まだ完了済みのペットはありません。</p>'
        '</details>'
        '<div class="pet-actions"><button type="button" id="pet-reset">全チェックを解除</button>'
        '<p id="pet-action-status" role="status" aria-live="polite"></p></div>'
        '</section>'
    )
