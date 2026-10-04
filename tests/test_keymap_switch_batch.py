import copy
import unittest

from keyseq.application.keymap_switch_batch import validate_switch_batch


def make_keymap(keymap_id, *, label="", triggers=None, mappings=None):
    return {
        "id": keymap_id,
        "label": label,
        "triggers": [{"key": key, "actions": []} for key in triggers or []],
        "mappings": mappings or {},
    }


def make_runtime():
    return {
        "keymaps": [
            make_keymap("existing", label="Existing", triggers=["old_trigger"], mappings={"old_source": "x"}),
            make_keymap("external", label="External map"),
        ],
        "active_keymap_id": "existing",
        "keymap_switch_keys": {"outside": "external"},
    }


class ValidateSwitchBatchTest(unittest.TestCase):
    def test_empty_key_is_reported_at_its_zero_based_row(self):
        result = validate_switch_batch(make_runtime(), "stop", "toggle", [], ["ok", "  "], ["a", "b"])
        self.assertEqual(result, (1, "切替キーは必須です。"))

    def test_stop_and_toggle_conflicts_use_existing_messages(self):
        runtime = make_runtime()
        self.assertEqual(
            validate_switch_batch(runtime, "STOP", "toggle", [], [" stop "], ["a"]),
            (0, "直接切替キーが停止キーと重複しています:\nstop"),
        )
        self.assertEqual(
            validate_switch_batch(runtime, "stop", "Toggle", [], ["toggle"], ["a"]),
            (0, "直接切替キーが一時停止/再開キーと重複しています:\ntoggle"),
        )

    def test_existing_keymap_trigger_conflict(self):
        self.assertEqual(
            validate_switch_batch(make_runtime(), "", "", [], ["OLD_TRIGGER"], ["new"]),
            (0, "直接切替キーが通常トリガーと重複しています:\nold_trigger"),
        )

    def test_new_keymap_own_trigger_is_in_completed_state(self):
        candidate = make_keymap("new", triggers=["candidate_trigger"])
        self.assertEqual(
            validate_switch_batch(make_runtime(), "", "", [candidate], ["candidate_trigger"], ["new"]),
            (0, "直接切替キーが通常トリガーと重複しています:\ncandidate_trigger"),
        )

    def test_trigger_from_another_new_keymap_is_in_completed_state(self):
        candidates = [make_keymap("new1"), make_keymap("new2", triggers=["second_trigger"])]
        self.assertEqual(
            validate_switch_batch(make_runtime(), "", "", candidates, ["second_trigger", "first_switch"], ["new1", "new2"]),
            (0, "直接切替キーが通常トリガーと重複しています:\nsecond_trigger"),
        )

    def test_existing_and_new_keymap_source_conflicts(self):
        runtime = make_runtime()
        self.assertEqual(
            validate_switch_batch(runtime, "", "", [], ["old_source"], ["new"]),
            (0, "直接切替キーがキーマップ元キーと重複しています:\nold_source"),
        )
        candidate = make_keymap("new", mappings={"new_source": "y"})
        self.assertEqual(
            validate_switch_batch(runtime, "", "", [candidate], ["new_source"], ["new"]),
            (0, "直接切替キーがキーマップ元キーと重複しています:\nnew_source"),
        )

    def test_external_switch_conflict_uses_keymap_display_name(self):
        self.assertEqual(
            validate_switch_batch(make_runtime(), "", "", [], ["OUTSIDE"], ["new"]),
            (0, "この切替キーは既に使用されています:\noutside -> External map"),
        )

    def test_switches_assigned_to_any_row_target_are_excluded(self):
        runtime = make_runtime()
        runtime["keymap_switch_keys"].update({"own_key": "new1", "other_row_key": "new2"})
        result = validate_switch_batch(
            runtime,
            "",
            "",
            [make_keymap("new1"), make_keymap("new2")],
            ["own_key", "other_row_key"],
            ["new1", "new2"],
        )
        self.assertIsNone(result)

    def test_duplicate_rows_use_existing_addition_message(self):
        self.assertEqual(
            validate_switch_batch(
                make_runtime(), "", "", [], ["same", " SAME "], ["new1", "new2"]
            ),
            (1, "直接切替キーは既に使用されています:\nsame"),
        )

    def test_stop_conflict_precedes_trigger_source_switch_and_duplicate_conflicts(self):
        runtime = make_runtime()
        runtime["keymaps"][0]["triggers"].append({"key": "stop", "actions": []})
        runtime["keymaps"][0]["mappings"]["stop"] = "x"
        runtime["keymap_switch_keys"]["stop"] = "external"
        self.assertEqual(
            validate_switch_batch(runtime, "stop", "", [], ["stop", "stop"], ["new1", "new2"]),
            (0, "直接切替キーが停止キーと重複しています:\nstop"),
        )

    def test_first_invalid_row_precedes_later_row_with_higher_priority_error(self):
        self.assertEqual(
            validate_switch_batch(
                make_runtime(), "stop", "", [], ["old_trigger", "stop"], ["new1", "new2"]
            ),
            (0, "直接切替キーが通常トリガーと重複しています:\nold_trigger"),
        )

    def test_valid_batch_returns_none_and_does_not_mutate_runtime(self):
        runtime = make_runtime()
        original = copy.deepcopy(runtime)
        result = validate_switch_batch(
            runtime,
            "stop",
            "toggle",
            [make_keymap("new1"), make_keymap("new2")],
            ["switch1", "switch2"],
            ["new1", "new2"],
        )
        self.assertIsNone(result)
        self.assertEqual(runtime, original)

    def test_invalid_batch_does_not_mutate_runtime(self):
        runtime = make_runtime()
        original = copy.deepcopy(runtime)
        validate_switch_batch(runtime, "stop", "toggle", [make_keymap("new")], ["old_trigger"], ["new"])
        self.assertEqual(runtime, original)


if __name__ == "__main__":
    unittest.main()
