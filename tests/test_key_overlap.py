import copy
import unittest

from keyseq.application.key_overlap import analyze_key_overlaps


def make_runtime():
    return {
        "keymaps": [
            {
                "id": "km1",
                "label": "Main",
                "triggers": [{"key": key, "actions": []} for key in ("s", "t", "d", "m", "all", "n", "foreign")],
                "mappings": {"m": "1", "all": "2"},
            },
            {
                "id": "km2",
                "label": "Other",
                "triggers": [{"key": "remote", "actions": []}],
                "mappings": {"foreign": "3", "remote_source": "4"},
            },
            {"id": "km3", "label": "Third", "triggers": [], "mappings": {}},
            {"id": "km4", "label": "Fourth", "triggers": [], "mappings": {}},
        ],
        "active_keymap_id": "km1",
        "keymap_switch_keys": {"d": "km2", "s": "km3", "t": "km4", "all": "km2"},
    }


class KeyOverlapAnalysisTest(unittest.TestCase):
    def test_trigger_and_switch_conflicts_follow_priority(self):
        report = analyze_key_overlaps(make_runtime(), "s", "t")
        self.assertEqual(
            {key: report.trigger_conflict(key).winner for key in ("s", "t", "d", "all")},
            {"s": "stop", "t": "toggle", "d": "switch", "all": "switch"},
        )
        self.assertIsNone(report.trigger_conflict("m"))
        self.assertIsNone(report.trigger_conflict("n"))
        self.assertEqual(
            {(item.key, item.keymap_id, item.winner) for item in report.keymap_switch_conflicts},
            {("s", "km3", "stop"), ("t", "km4", "toggle")},
        )

    def test_separate_keymap_replacement_does_not_shadow_active_trigger(self):
        report = analyze_key_overlaps(make_runtime(), "", "")
        self.assertIn("foreign", report.active_trigger_keys)
        self.assertIn("foreign", report.all_source_keys)
        self.assertNotIn("foreign", report.active_source_keys)
        self.assertIsNone(report.trigger_conflict("foreign"))

    def test_collects_all_assignment_sets_and_stop_toggle_conflict(self):
        runtime = make_runtime()
        original = copy.deepcopy(runtime)
        report = analyze_key_overlaps(runtime, "s", " S ")
        self.assertEqual(runtime, original)
        self.assertEqual(report.active_keymap_id, "km1")
        self.assertIn("remote", report.all_trigger_keys)
        self.assertIn("remote_source", report.all_source_keys)
        self.assertIn("m", report.active_source_keys)
        self.assertTrue(report.stop_toggle_conflict)
        self.assertEqual(
            [(item.kind, item.winner) for item in report.shadowed_for_key("all")],
            [("trigger", "switch")],
        )

    def test_conflict_indexes_are_read_only(self):
        report = analyze_key_overlaps(make_runtime(), "s", "t")
        with self.assertRaises(TypeError):
            report._shadowed_by_key["x"] = ()


if __name__ == "__main__":
    unittest.main()
