import unittest

from keyseq.presentation.controllers.config_io.save_target_snapshot import (
    capture_active,
    capture_all,
    snapshot_matches,
)


def _data(*trigger_sets, active="map0"):
    keymaps = [
        {"id": f"map{index}", "triggers": triggers}
        for index, triggers in enumerate(trigger_sets)
    ]
    return {"keymaps": keymaps, "active_keymap_id": active}


class SaveTargetSnapshotTest(unittest.TestCase):
    def test_unchanged_data_matches_for_all_and_active(self):
        data = _data([{"key": "a"}], [{"key": "b"}], active="map0")
        self.assertTrue(snapshot_matches(data, capture_all(data)))
        self.assertTrue(snapshot_matches(data, capture_active(data)))

    def test_keymap_without_triggers_matches_for_all_and_active(self):
        data = {
            "keymaps": [{"id": "keymap_1", "label": "", "mappings": {}}],
            "active_keymap_id": "keymap_1",
        }
        self.assertTrue(snapshot_matches(data, capture_all(data)))
        self.assertTrue(snapshot_matches(data, capture_active(data)))

    def test_active_rows_reordering_addition_and_deletion_do_not_match(self):
        for mutation in (
            lambda rows: rows.reverse(),
            lambda rows: rows.append({"key": "b"}),
            lambda rows: rows.pop(),
        ):
            with self.subTest(mutation=mutation):
                data = _data([{"key": "a"}, {"key": "b"}])
                snapshot = capture_active(data)
                mutation(data["keymaps"][0]["triggers"])
                self.assertFalse(snapshot_matches(data, snapshot))

    def test_replacing_list_with_equal_contents_does_not_match(self):
        rows = [{"key": "a"}]
        data = _data(rows)
        snapshot = capture_active(data)
        data["keymaps"][0]["triggers"] = [{"key": "a"}]
        self.assertFalse(snapshot_matches(data, snapshot))

    def test_switching_active_trigger_set_does_not_match(self):
        data = _data([{"key": "a"}], [{"key": "b"}])
        snapshot = capture_active(data)
        data["active_keymap_id"] = "map1"
        self.assertFalse(snapshot_matches(data, snapshot))

    def test_adding_or_removing_trigger_set_does_not_match_all_snapshot(self):
        data = _data([{"key": "a"}])
        snapshot = capture_all(data)
        data["keymaps"].append({"id": "map1", "triggers": []})
        self.assertFalse(snapshot_matches(data, snapshot))

        snapshot = capture_all(data)
        data["keymaps"].pop()
        self.assertFalse(snapshot_matches(data, snapshot))

    def test_equal_replacement_objects_do_not_match(self):
        row = {"key": "a"}
        triggers = [row]
        data = _data(triggers)
        snapshot = capture_all(data)
        data["keymaps"][0]["triggers"][0] = {"key": "a"}
        self.assertFalse(snapshot_matches(data, snapshot))

        data = _data([{"key": "a"}])
        snapshot = capture_all(data)
        data["keymaps"][0] = {"id": "map0", "triggers": data["keymaps"][0]["triggers"]}
        self.assertFalse(snapshot_matches(data, snapshot))


if __name__ == "__main__":
    unittest.main()
