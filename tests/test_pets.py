import json
from pathlib import Path
import unittest

from pets import render_pet_tracker

ROOT = Path(__file__).resolve().parents[1]


class PetPriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "data/pets.json").read_text(encoding="utf-8"))
        cls.sources = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
        cls.meta = json.loads((ROOT / "content/pets.md").read_text(encoding="utf-8").splitlines()[0])

    def test_pet_categories_and_unique_names(self):
        pets = self.catalog["items"]
        self.assertEqual(len(pets), 89)
        self.assertEqual(len({item["name"] for item in pets}), len(pets))
        for reason, expected in (("shop", 32), ("elyos", 38), ("dungeon", 11), ("rare", 11)):
            with self.subTest(group=reason):
                self.assertEqual(sum(reason in item["groups"] for item in pets), expected)
        self.assertEqual(self.catalog["checked_at"], self.meta["checked_at"])

    def test_pets_are_in_purchase_priority_order(self):
        priorities = {"shop": 0, "elyos": 1, "dungeon": 2, "rare": 3}
        actual = [min(priorities[group] for group in pet["groups"]) for pet in self.catalog["items"]]
        self.assertEqual(actual, sorted(actual))

    def test_dungeon_pets_are_not_marked_shop_only(self):
        pets = {item["name"]: item for item in self.catalog["items"]}
        for name in ("ウルググ闘士", "クラオ実験体", "クラオ変異体", "クラオ封印の守護者", "最上級水の精霊", "最上級地の精霊"):
            with self.subTest(pet=name):
                self.assertIn("dungeon", pets[name]["groups"])
                self.assertNotIn("shop", pets[name]["groups"])

    def test_elyos_and_rare_can_share_a_single_row(self):
        pet = next(p for p in self.catalog["items"] if p["name"] == "精鋭ニュート")
        self.assertEqual(set(pet["groups"]), {"elyos", "rare"})

    def test_every_pet_source_is_declared(self):
        for item in self.catalog["items"]:
            for sid in item["source_ids"]:
                self.assertIn(sid, self.meta["source_ids"])
                self.assertIn(sid, self.sources)

    def test_accessible_interactive_table_and_complete_section(self):
        result = render_pet_tracker(self.catalog, self.sources, self.meta["source_ids"])
        self.assertEqual(result.count('class="pet-row"'), 89)
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
