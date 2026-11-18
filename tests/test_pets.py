import json
from pathlib import Path
import unittest

from pets import render_pet_tracker, pet_sort_key

ROOT = Path(__file__).resolve().parents[1]


class PetPriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "data/pets.json").read_text(encoding="utf-8"))
        cls.sources = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
        cls.meta = json.loads((ROOT / "content/pets.md").read_text(encoding="utf-8").splitlines()[0])

    def test_pet_categories_and_unique_names(self):
        pets = self.catalog["items"]
        self.assertEqual(len(pets), 92)
        self.assertEqual(len({item["name"] for item in pets}), len(pets))
        expected_counts = {
            "shop": 29, "elyos": 28, "dungeon": 14, "dungeon-single": 7,
            "rare": 8, "alternate": 10, "altgard": 11,
        }
        for reason, expected in expected_counts.items():
            with self.subTest(group=reason):
                self.assertEqual(sum(reason in item["groups"] for item in pets), expected)
        self.assertEqual(self.catalog["checked_at"], self.meta["checked_at"])

    def test_japanese_alphabetical_order_uses_kanji_readings(self):
        catalog = self.catalog["items"]
        self.assertEqual(len(catalog), len({pet["name"] for pet in catalog}))
        sorted_names = [p["name"] for p in sorted(catalog, key=pet_sort_key)]
        self.assertEqual(sorted_names[0], "アウルトロスの分身")
        self.assertLess(sorted_names.index("火炎バルゲスト"),
                        sorted_names.index("監視兵器クナッシュ"))
        self.assertLess(sorted_names.index("精鋭ニュート"),
                        sorted_names.index("手懐けたザイフ"))
        self.assertLess(sorted_names.index("ムームー族監督官"),
                        sorted_names.index("門番ピノピ"))
        html = render_pet_tracker(self.catalog, self.sources, self.meta["source_ids"])
        self.assertIn("あいうえお順", html)
        self.assertLess(html.index('data-key="' + sorted_names[0] + '"'),
                        html.index('data-key="' + sorted_names[1] + '"'))
        self.assertLess(sorted_names.index("クラル強化警戒兵"),
                        sorted_names.index("クラル強化戦闘兵"))
        self.assertTrue(all(pet["reading"] for pet in catalog
                            if any("\u3400" <= c <= "\u9fff" for c in pet["name"])))

    def test_dungeon_pets_are_not_marked_shop_only(self):
        pets = {item["name"]: item for item in self.catalog["items"]}
        for name in ("ウルググ闘士", "クラオ実験体", "クラオ変異体", "クラオ封印の守護者",
                     "最上級水の精霊", "最上級地の精霊", "火炎石の守護像",
                     "火炎バルゲスト", "最上級火の精霊"):
            with self.subTest(pet=name):
                self.assertIn("dungeon", pets[name]["groups"])
                self.assertNotIn("shop", pets[name]["groups"])

    def test_elyos_and_rare_can_share_a_single_row(self):
        pet = next(p for p in self.catalog["items"] if p["name"] == "精鋭ニュート")
        self.assertEqual(set(pet["groups"]), {"elyos", "rare"})

    def test_alternate_routes_and_spawn_counts_adjust_priority(self):
        pets = {item["name"]: item for item in self.catalog["items"]}
        for name in ("沼地のタルゴン", "クラル戦士", "コヌティ作業員"):
            self.assertEqual(pets[name]["groups"], ["alternate"])
        self.assertEqual(pets["ビベル"]["groups"], ["altgard"])
        self.assertIn("71地点", pets["ビベル"]["notes"][0])
        self.assertEqual(pets["ビロータ薬草採り"]["groups"], ["altgard", "rare"])

    def test_renamed_pets_keep_previous_saved_keys(self):
        result = render_pet_tracker(self.catalog, self.sources, self.meta["source_ids"])
        for old, name in (("強化されたクラル戦闘兵", "クラル強化戦闘兵"),
                          ("精鋭魂のない屍ヤブカ", "精鋭魂のない棺蜘蛛")):
            with self.subTest(pet=name):
                self.assertIn(f'data-key="{old}" data-name="{name}"', result)
                self.assertIn(f'aria-label="{name}を完了済みにする"', result)

    def test_every_pet_source_is_declared(self):
        for item in self.catalog["items"]:
            for sid in item["source_ids"]:
                self.assertIn(sid, self.meta["source_ids"])
                self.assertIn(sid, self.sources)

    def test_accessible_interactive_table_and_complete_section(self):
        result = render_pet_tracker(self.catalog, self.sources, self.meta["source_ids"])
        self.assertEqual(result.count('class="pet-row"'), 92)
        for term in ('id="pet-pending-body"', 'id="pet-completed-body"',
                     'id="pet-pending-count"', 'id="pet-done-count"',
                     'id="pet-search"', 'id="pet-group"', 'id="pet-genus"',
                     'id="pet-reset"', 'aria-live="polite"', '精鋭ニュート',
                     "ムームー族監督官"):
            with self.subTest(term=term):
                self.assertIn(term, result)

    def test_saved_state_is_local_only_and_has_recovery_path(self):
        js = (ROOT / "assets/pets.js").read_text(encoding="utf-8")
        for term in ('aion2-pet-completed-v1', 'localStorage.getItem',
                     'localStorage.setItem', 'completed.delete',
                     'pet-completed-body', 'window.confirm', 'data.order'):
            # JS may use dataset.order instead of a literal "data.order".
            if term == "data.order":
                self.assertIn("dataset.order", js)
            else:
                self.assertIn(term, js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("XMLHttpRequest", js)

    def test_html_escapes_untrusted_pet_names(self):
        example = {"items": [{"name": "<img src=x onerror=alert(1)>",
                             "genus": "知性", "groups": ["rare"],
                             "notes": ["special < & >"],
                             "source_ids": [self.meta["source_ids"][0]]}]}
        output = render_pet_tracker(example, self.sources, self.meta["source_ids"])
        self.assertNotIn("<img src=x", output)
        self.assertIn("&lt;img src=x", output)
        self.assertIn("special &lt; &amp; &gt;", output)


if __name__ == "__main__":
    unittest.main()
