"""Server-rendered pet priority checklist; filtering/state are optional client enhancements."""
from collections import Counter
from html import escape
import unicodedata

GROUPS = {
    "shop": "購入・箱中心",
    "elyos": "ベルテロン限定",
    "dungeon-single": "IDで1周1体",
    "dungeon": "ID産",
    "rare": "狩場少数",
    "alternate": "共通ID・アビスあり",
    "altgard": "魔族側の狩場",
}
GENERA = {"知性", "野性", "自然", "変形"}


def pet_sort_key(item: dict) -> tuple[str, str]:
    """Sort by Japanese pronunciation, not by Unicode ordering of kanji names."""
    reading = unicodedata.normalize("NFKC", item.get("reading", item["name"]))
    # Unicode hiragana follows gojuon order; normalize katakana to hiragana.
    reading = "".join(chr(ord(c) - 0x60) if 0x30A1 <= ord(c) <= 0x30F6
                      else c for c in reading)
    return reading.replace(" ", ""), item["name"]


def render_pet_tracker(catalog: dict, sources: dict, allowed_ids: list[str]) -> str:
    pets = sorted(catalog["items"], key=pet_sort_key)
    if not pets:
        raise ValueError("empty pet catalog")
    names = set()
    storage_keys = set()
    rows = []
    counts = Counter()

    for index, item in enumerate(pets):
        name = item["name"]
        if any("\u3400" <= c <= "\u9fff" for c in name) and not item.get("reading"):
            raise ValueError("missing reading for kanji pet name: " + name)
        if not name or name in names:
            raise ValueError("duplicate or empty pet name: " + name)
        names.add(name)
        storage_key = item.get("storage_key", name)
        if not storage_key or storage_key in storage_keys:
            raise ValueError("duplicate or empty pet storage key: " + name)
        storage_keys.add(storage_key)
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
        source_id = source_ids[0]
        reading = item.get("reading", name)
        rows.append(
            '<tr class="pet-row" role="row" data-key="' + escape(storage_key, quote=True) + '"'
            ' data-name="' + escape(name, quote=True) + '"'
            ' data-reading="' + escape(reading, quote=True) + '"'
            ' data-groups="' + escape(" ".join(groups), quote=True) + '"'
            ' data-genus="' + escape(genus, quote=True) + '">'
            '<td class="pet-check-cell" role="cell"><label class="pet-check" for="' + pet_id + '">'
            '<input id="' + pet_id + '" type="checkbox" class="pet-done-input"'
            ' aria-label="' + escape(name, quote=True) + 'の完了">'
            '<span>完了</span></label></td>'
            '<th class="pet-name-cell" role="rowheader" scope="row"><strong class="pet-name">' + escape(name) + '</strong>'
            '<small>' + escape(genus) + '</small></th>'
            '<td class="pet-chips" role="cell">' + chips + '</td>'
            '<td class="pet-notes" role="cell">' + escape(notes) + '</td>'
            '<td class="pet-source-cell" role="cell"><a href="#source-' + escape(source_id, quote=True)
            + '">出典</a></td>'
            '</tr>'
        )

    options = "".join(
        '<option value="' + key + '">' + label + '（' + str(counts[key]) + '）</option>'
        for key, label in GROUPS.items()
    )
    rows_html = "".join(rows)
    headers = ('<thead role="rowgroup"><tr role="row"><th role="columnheader" scope="col">済</th>'
               '<th role="columnheader" scope="col">ペット名</th><th role="columnheader" scope="col">入手区分</th>'
               '<th role="columnheader" scope="col">買う理由・代替入手</th>'
               '<th role="columnheader" scope="col">根拠</th></tr></thead>')
    return (
        '<section id="pet-tracker" aria-labelledby="pet-tracker-title">'
        '<h2 id="pet-tracker-title">購入チェックリスト（あいうえお順）</h2>'
        '<div class="pet-summary">'
        '<span>未完了 <strong id="pet-pending-count">' + str(len(rows)) + '</strong></span>'
        '<span>完了 <strong id="pet-done-count">0</strong></span>'
        '<a href="#pet-completed-summary" id="pet-completed-link" hidden>完了済みへ移動</a>'
        '</div>'
        '<div class="pet-controls">'
        '<label for="pet-search">ペット名を検索'
        '<input id="pet-search" type="search" placeholder="名前・よみがな" autocomplete="off"></label>'
        '<label for="pet-group">入手区分'
        '<select id="pet-group"><option value="all">すべての購入候補</option>'
        + options + '</select></label>'
        '<label for="pet-genus">種族'
        '<select id="pet-genus"><option value="all">すべて</option>'
        + "".join('<option value="' + escape(g) + '">' + escape(g) + '</option>'
                  for g in ("知性", "野性", "自然", "変形")) +
        '</select></label></div>'
        '<p class="pet-local-note">チェックはこのブラウザに保存されます。</p>'
        '<noscript><p>絞り込みと完了保存にはJavaScriptが必要です。下の一覧は閲覧できます。</p></noscript>'
        '<p id="pet-results" class="pet-results" role="status"></p>'
        '<div class="pet-table-wrap">'
        '<table id="pet-pending-table" role="table" aria-label="未完了の購入候補一覧">' + headers
        + '<tbody id="pet-pending-body" role="rowgroup">' + rows_html
        + '</tbody></table></div>'
        '<p id="pet-empty" class="pet-empty" hidden>条件に一致する未完了のペットはありません。</p>'
        '<details id="pet-completed-panel" class="pet-completed-panel">'
        '<summary id="pet-completed-summary">完了済みのペット（<span id="pet-done-summary">0</span>種）</summary>'
        '<p class="pet-local-note">チェックを外すと未完了に戻ります。</p>'
        '<div class="pet-table-wrap">'
        '<table id="pet-completed-table" role="table" aria-label="完了済みペット一覧">' + headers
        + '<tbody id="pet-completed-body" role="rowgroup"></tbody></table></div>'
        '<p id="pet-done-empty" class="pet-empty">まだ完了済みのペットはありません。</p>'
        '</details>'
        '<div class="pet-actions"><button type="button" id="pet-reset">全チェックを解除</button>'
        '<p id="pet-action-status" role="status" aria-live="polite"></p></div>'
        '</section>'
    )
