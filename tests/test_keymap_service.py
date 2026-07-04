import unittest

from keyseq.application.keymap_service import KeymapService


def make_data():
    return {
        "keymaps": [
            {"id": "km1", "label": "One", "mappings": {"a": "b"}},
            {"id": "km2", "label": "", "mappings": {}},
            {"id": "km3", "label": "Three", "mappings": {}},
        ],
        "active_keymap_id": "km2",
        "keymap_switch_keys": {"1": "km1", "2": "km2"},
    }


class KeymapServiceTest(unittest.TestCase):
    def test_create_keymap_on_empty(self):
        data = {}
        created = KeymapService.create_keymap(data)
        self.assertEqual(created["id"], "keymap_1")
        self.assertEqual(data["active_keymap_id"], "keymap_1")
        second = KeymapService.create_keymap(data)
        self.assertEqual(second["id"], "keymap_2")
        self.assertEqual(data["active_keymap_id"], "keymap_1")

    def test_delete_active_keymap_falls_back(self):
        data = make_data()
        deleted, next_active = KeymapService.delete_keymap(data, "km2")
        self.assertTrue(deleted)
        self.assertEqual(next_active, "km3")
        self.assertEqual(data["keymap_switch_keys"], {"1": "km1"})

    def test_delete_last_keymap_clears_active(self):
        data = {
            "keymaps": [{"id": "km1", "mappings": {}}],
            "active_keymap_id": "km1",
            "keymap_switch_keys": {},
        }
        deleted, next_active = KeymapService.delete_keymap(data, "km1")
        self.assertTrue(deleted)
        self.assertEqual(next_active, "")
        self.assertEqual(data["active_keymap_id"], "")

    def test_set_keymap_switch_key(self):
        data = make_data()
        self.assertTrue(KeymapService.set_keymap_switch_key(data, "3", "km3"))
        # km1 には既に "1" が割当済みなので、別キーの追加は拒否される
        self.assertFalse(KeymapService.set_keymap_switch_key(data, "9", "km1"))
        # 同じ割当のやり直しは「変化なし」= False
        self.assertFalse(KeymapService.set_keymap_switch_key(data, "1", "km1"))
        self.assertFalse(KeymapService.set_keymap_switch_key(data, "5", "nope"))

    def test_get_keymap_by_switch_key(self):
        data = make_data()
        self.assertEqual(KeymapService.get_keymap_by_switch_key(data, "1"), "km1")
        self.assertEqual(KeymapService.get_keymap_by_switch_key(data, "8"), "")

    def test_find_mapping_target_uses_active(self):
        data = make_data()
        data["active_keymap_id"] = "km1"
        self.assertEqual(KeymapService.find_mapping_target(data, "A"), "b")
        self.assertEqual(KeymapService.find_mapping_target(data, "z"), "")
        data["active_keymap_id"] = "km2"
        self.assertEqual(KeymapService.find_mapping_target(data, "a"), "")

    def test_ensure_active_keymap_creates_default(self):
        data = {}
        keymap = KeymapService.ensure_active_keymap(data)
        self.assertEqual(keymap["id"], "default")
        self.assertEqual(data["active_keymap_id"], "default")

    def test_set_and_clear_mapping(self):
        data = make_data()
        data["active_keymap_id"] = "km1"
        keymap_id, changed = KeymapService.set_mapping(data, "X", "Y")
        self.assertEqual(keymap_id, "km1")
        self.assertTrue(changed)
        self.assertEqual(data["keymaps"][0]["mappings"]["x"], "y")
        keymap_id, changed = KeymapService.clear_mapping(data, "x")
        self.assertTrue(changed)
        self.assertNotIn("x", data["keymaps"][0]["mappings"])


if __name__ == "__main__":
    unittest.main()
