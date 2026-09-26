import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.config_service import ConfigService, split_loading
from keyseq.application.keymap_service import KeymapService
from keyseq.domain.config import DEFAULT_CONFIG, ensure_config_compatibility, normalize_triggers, safe_deepcopy
from keyseq.domain.keymap_triggers import (
    ensure_at_least_one_keymap,
    ensure_active_triggers,
    get_active_triggers,
    migrate_single_json_triggers,
    set_active_triggers,
)
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.keymap_file_io import KeymapFileIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


class PerKeymapDomainTest(unittest.TestCase):
    def test_normalization_preserves_shared_lists_and_internal_keys(self):
        triggers = [None, {"key": " F1 ", "actions": [{"type": " text "}],
                           "_sequence_source_path": " seq.json ",
                           "_sequence_parent_refs": ["set.json"],
                           "_sequence_dirty": True, "_sequence_imported": False}]
        metadata = {"_trigger_set_source_path": "set.json",
                    "_trigger_set_parent_refs": ["km.json"],
                    "_trigger_set_dirty": True, "_trigger_set_imported": False}
        data = {"keymaps": [{"id": name, "triggers": triggers, **metadata}
                            for name in ("a", "b")]}
        normalized = ensure_config_compatibility(data)
        first, second = normalized["keymaps"]
        self.assertIs(first["triggers"], second["triggers"])
        self.assertIsNot(first["triggers"], triggers)
        self.assertEqual(first["triggers"], normalize_triggers(triggers))
        self.assertEqual(first["triggers"][0]["_sequence_parent_refs"], ["set.json"])
        for key, value in metadata.items():
            self.assertEqual(first[key], value)
            self.assertEqual(second[key], value)
        first["triggers"].append({"key": "f2"})
        self.assertEqual(second["triggers"][-1], {"key": "f2"})

    def test_invalid_list_remains_present_and_normalization_does_not_migrate(self):
        for value in (None, {}, "bad", 0):
            with self.subTest(value=value):
                data = ensure_config_compatibility({
                    "triggers": [{"key": "f1"}],
                    "keymaps": [{"id": "a", "triggers": value}, {"id": "b"}],
                })
                self.assertEqual(data["keymaps"][0]["triggers"], [])
                self.assertNotIn("triggers", data["keymaps"][1])
                self.assertEqual(data["triggers"][0]["key"], "f1")
                self.assertEqual(migrate_single_json_triggers(data), "unused")
                self.assertEqual(get_active_triggers(data), [])

    def test_creation_is_idempotent_and_uses_service_rule(self):
        data = {}
        created = ensure_at_least_one_keymap(data)
        self.assertEqual(created, {"id": "keymap_1", "label": "", "mappings": {}})
        self.assertEqual(data["active_keymap_id"], "keymap_1")
        self.assertNotIn("keymap_switch_keys", data)
        self.assertIsNone(ensure_at_least_one_keymap(data))
        self.assertIs(data["keymaps"][0], created)
        self.assertEqual(KeymapService.ensure_active_keymap({}), created)

    def test_migration_states_and_only_active_receives_legacy(self):
        for state, legacy, present in (
            ("none", [], False), ("migrated", [{"key": "f1"}], False),
            ("unused", [{"key": "f1"}], True),
        ):
            with self.subTest(state=state):
                active = {"id": "b"}
                own = [{"key": "f2"}]
                if present:
                    active["triggers"] = own
                data = {"keymaps": [{"id": "a"}, active], "active_keymap_id": "b",
                        "triggers": legacy}
                self.assertEqual(migrate_single_json_triggers(data), state)
                self.assertEqual(data["triggers"], [])
                self.assertEqual(data["keymaps"][0]["triggers"], [])
                self.assertIs(get_active_triggers(data), own if present else active["triggers"])
                if state == "migrated":
                    self.assertIs(get_active_triggers(data), legacy)
                self.assertEqual(migrate_single_json_triggers(data), "none")

    def test_switching_returns_distinct_lists_and_missing_active_is_read_only(self):
        first, second = [{"key": "f1"}], [{"key": "f2"}]
        data = {"keymaps": [{"id": "a", "triggers": first}, {"id": "b", "triggers": second}],
                "active_keymap_id": "a"}
        self.assertIs(get_active_triggers(data), first)
        KeymapService.set_active_keymap_id(data, "b")
        self.assertIs(get_active_triggers(data), second)
        data["active_keymap_id"] = "missing"
        self.assertEqual(get_active_triggers(data), [])
        self.assertEqual(data["active_keymap_id"], "missing")
        self.assertIs(ensure_active_triggers(data), first)
        replacement = []
        set_active_triggers(data, replacement)
        self.assertIs(get_active_triggers(data), replacement)

    def test_defaults_and_empty_data(self):
        service = ConfigService(JsonRepository())
        self.assertEqual(len(DEFAULT_CONFIG["keymaps"]), 1)
        self.assertEqual(DEFAULT_CONFIG["triggers"], [])
        self.assertEqual([t["key"] for t in get_active_triggers(DEFAULT_CONFIG)], ["f1", "f2"])
        empty = service.new_empty_data()
        self.assertEqual(empty["keymaps"], [{"id": "keymap_1", "label": "", "mappings": {}, "triggers": []}])
        self.assertEqual(empty["active_keymap_id"], "keymap_1")
        self.assertEqual(empty["triggers"], [])


class PerKeymapLoadingTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = self.directory.name
        self.service = ConfigService(JsonRepository())

    def write(self, path, data):
        full_path = os.path.join(self.root, path)
        self.service.repository.save_json(full_path, data)
        return full_path

    def load_split(self, keymaps, legacy="", active="b.json"):
        return split_loading.build_runtime_data_from_split(self.service, {
            "keymaps": keymaps, "active_keymap_path": active, "trigger_set_path": legacy,
        }, config_root=self.root)

    def test_split_legacy_moves_to_active_only_and_records_state(self):
        for name in ("a", "b"):
            self.write(name + ".json", {"id": name, "mappings": {}})
        self.write("old.json", {"triggers": [{"key": "f8"}], "_parent_refs": ["set.json"]})
        data = self.load_split(["a.json", "b.json"], "old.json")
        self.assertEqual(data["triggers"], [])
        self.assertEqual(data["keymaps"][0]["triggers"], [])
        self.assertEqual([t["key"] for t in get_active_triggers(data)], ["f8"])
        self.assertEqual(data["_legacy_trigger_set"], {"state": "migrated", "path": "old.json", "keymap_id": "b"})
        self.assertEqual(data["keymaps"][1]["_trigger_set_source_path"], "old.json")
        self.assertEqual(data["keymaps"][1]["_trigger_set_parent_refs"], ["set.json"])
        self.assertTrue(data["keymaps"][1]["_keymap_dirty"])
        self.assertNotIn("_trigger_set_source_path", data)
        self.assertNotIn("_trigger_set_parent_refs", data)

    def test_split_empty_keymaps_and_no_example_contamination(self):
        self.write("old.json", {"triggers": [{"key": "f9"}]})
        for legacy, expected, state in (("", [], "none"), ("old.json", ["f9"], "migrated")):
            with self.subTest(legacy=legacy):
                data = self.load_split([], legacy, active="")
                self.assertEqual(len(data["keymaps"]), 1)
                self.assertEqual(data["active_keymap_id"], "keymap_1")
                self.assertEqual([t["key"] for t in get_active_triggers(data)], expected)
                self.assertEqual(data["_legacy_trigger_set"]["state"], state)
                self.assertEqual(data["triggers"], [])

    def test_split_explicit_empty_reference_moves_legacy_list_to_new_keymap(self):
        self.write("old.json", {"triggers": [{"key": "f8"}]})
        self.write("own.json", {"triggers": [{"key": "f9"}]})
        self.write("b.json", {"id": "b", "trigger_set_path": ""})
        data = self.load_split(["b.json"], "old.json")
        self.assertEqual([item["id"] for item in data["keymaps"]], ["b", "keymap_1"])
        self.assertEqual(data["active_keymap_id"], "b")
        self.assertEqual(data["_legacy_trigger_set"], {
            "state": "migrated", "path": "old.json", "keymap_id": "keymap_1", "auto_created": True,
        })
        self.assertEqual([item["key"] for item in get_active_triggers(data)], [])
        self.assertEqual([item["key"] for item in data["keymaps"][1]["triggers"]], ["f8"])

    def test_active_separate_trigger_set_creates_migration_keymap(self):
        self.write("old.json", {"triggers": [{"key": "f8"}]})
        self.write("own.json", {"triggers": [{"key": "f9"}]})
        self.write("b.json", {"id": "b", "trigger_set_path": "own.json"})
        data = self.load_split(["b.json"], "old.json")
        self.assertEqual(data["active_keymap_id"], "b")
        self.assertEqual([item["id"] for item in data["keymaps"]], ["b", "keymap_1"])
        target = data["keymaps"][1]
        self.assertEqual(target["label"], "旧トリガー一覧（old）")
        self.assertEqual(target["mappings"], {})
        self.assertNotIn("keymap_1", data["keymap_switch_keys"].values())
        self.assertEqual([item["key"] for item in target["triggers"]], ["f8"])
        self.assertEqual(data["_legacy_trigger_set"], {
            "state": "migrated", "path": "old.json", "keymap_id": "keymap_1", "auto_created": True,
        })
        self.assertTrue(target["_keymap_dirty"])

    def test_any_keymap_reference_to_legacy_path_is_same(self):
        self.write("old.json", {"triggers": [{"key": "f8"}]})
        self.write("own.json", {"triggers": [{"key": "f9"}]})
        self.write("a.json", {"id": "a", "trigger_set_path": "./old.json"})
        self.write("b.json", {"id": "b", "trigger_set_path": "own.json"})
        data = self.load_split(["a.json", "b.json"], "old.json")
        self.assertEqual(data["_legacy_trigger_set"]["state"], "same")
        self.assertEqual(len(data["keymaps"]), 2)
        self.assertEqual([item["key"] for item in get_active_triggers(data)], ["f9"])

    def test_missing_legacy_file_without_active_reference_does_not_migrate(self):
        self.write("a.json", {"id": "a", "mappings": {}})
        self.write("b.json", {"id": "b", "mappings": {}})
        data = self.load_split(["a.json", "b.json"], "old.json")

        self.assertEqual(data["_legacy_trigger_set"]["state"], "none")
        self.assertEqual(len(data["keymaps"]), 2)
        self.assertEqual(get_active_triggers(data), [])
        active = next(item for item in data["keymaps"] if item["id"] == "b")
        self.assertFalse(active.get("_keymap_dirty", False))
        self.assertNotIn("_trigger_set_source_path", active)

    def test_missing_legacy_file_with_active_reference_does_not_create_keymap(self):
        self.write("own.json", {"triggers": [{"key": "f9"}]})
        for reference, expected in (("", []), ("own.json", ["f9"])):
            with self.subTest(reference=reference):
                self.write("b.json", {"id": "b", "mappings": {}, "trigger_set_path": reference})
                data = self.load_split(["b.json"], "old.json")

                self.assertEqual(data["_legacy_trigger_set"]["state"], "none")
                self.assertNotIn("auto_created", data["_legacy_trigger_set"])
                self.assertEqual(len(data["keymaps"]), 1)
                self.assertEqual([item["key"] for item in get_active_triggers(data)], expected)

    def test_missing_legacy_file_already_referenced_by_other_keymap_is_same(self):
        self.write("a.json", {"id": "a", "mappings": {}, "trigger_set_path": "old.json"})
        self.write("b.json", {"id": "b", "mappings": {}})
        data = self.load_split(["a.json", "b.json"], "old.json")

        self.assertEqual(data["_legacy_trigger_set"]["state"], "same")
        self.assertEqual(len(data["keymaps"]), 2)

    def test_unreadable_existing_legacy_file_still_migrates(self):
        self.write("b.json", {"id": "b", "mappings": {}})
        for source_kind in ("broken_json", "top_level_list"):
            with self.subTest(source_kind=source_kind):
                legacy_full_path = os.path.join(self.root, "old.json")
                if source_kind == "broken_json":
                    with open(legacy_full_path, "w", encoding="utf-8") as file:
                        file.write("{")
                else:
                    self.write("old.json", [])
                data = self.load_split(["b.json"], "old.json")

                self.assertEqual(data["_legacy_trigger_set"]["state"], "migrated")
                active = data["keymaps"][0]
                self.assertEqual(active["triggers"], [])
                self.assertEqual(active["_trigger_set_source_path"], "old.json")
                self.assertTrue(active["_keymap_dirty"])

    def test_non_string_legacy_reference_is_ignored_even_when_file_exists(self):
        self.write("b.json", {"id": "b", "mappings": {}})
        self.write("old.json", {"triggers": [{"key": "f8"}]})
        for legacy in (1, ["old.json"], {"path": "old.json"}, None, True):
            with self.subTest(legacy=legacy):
                data = self.load_split(["b.json"], legacy)

                self.assertEqual(data["_legacy_trigger_set"]["state"], "none")
                self.assertEqual(data["_legacy_trigger_set"]["path"], "")
                self.assertEqual(len(data["keymaps"]), 1)
                self.assertEqual(data["keymaps"][0]["triggers"], [])

    def test_split_shares_resolved_path_and_reads_once_including_active_only_entry(self):
        self.write("shared.json", {"triggers": [{"key": "f7"}], "_parent_refs": ["a.json", "b.json"]})
        self.write("a.json", {"id": "a", "trigger_set_path": "shared.json"})
        self.write("b.json", {"id": "b", "trigger_set_path": "./shared.json"})
        with patch.object(split_loading, "load_trigger_set", wraps=split_loading.load_trigger_set) as load:
            data = self.load_split(["a.json"], "shared.json")
        load.assert_called_once()
        first, second = data["keymaps"]
        self.assertIs(first["triggers"], second["triggers"])
        self.assertEqual(first["_trigger_set_source_path"], second["_trigger_set_source_path"])
        self.assertEqual(first["_trigger_set_parent_refs"], second["_trigger_set_parent_refs"])
        self.assertEqual(data["_legacy_trigger_set"]["state"], "same")

    def test_individual_keymap_load_rejects_same_canonical_source_path(self):
        source = os.path.join(self.root, "user", "keymaps", "main.json")
        data = {"keymaps": [{
            "id": "main", "label": "Main", "mappings": {}, "triggers": [],
            self.service.INTERNAL_KEYMAP_SOURCE_PATH: source,
        }], "active_keymap_id": "main"}
        app = SimpleNamespace(
            data=data,
            config_root=self.root,
            config_service=self.service,
            keymap_service=KeymapService,
            paths=SimpleNamespace(
                preferred_keymaps_dir=Mock(return_value=self.root),
                json_dialog_initial_dir=Mock(return_value=self.root),
            ),
        )
        io = KeymapFileIo(app)
        before = safe_deepcopy(data)
        alternate_spelling = os.path.join(self.root, "user", "keymaps", ".", "main.json")
        with patch("keyseq.presentation.controllers.config_io.keymap_file_io.filedialog.askopenfilename",
                   return_value=alternate_spelling), patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.messagebox.showerror"
        ) as showerror:
            io.load_keymap_file()
        showerror.assert_called_once_with("読込できません", "このキーマップは既に読み込まれています")
        self.assertEqual(data, before)

    def test_single_import_legacy_and_oldest_format(self):
        for source in ({"triggers": [{"key": "f8"}]}, {"trigger_key": " F8 ", "actions": []}):
            with self.subTest(source=source):
                data = self.service.load_legacy_runtime_data(self.write("import.json", source))
                self.assertEqual(data["active_keymap_id"], "keymap_1")
                self.assertEqual([t["key"] for t in get_active_triggers(data)], ["f8"])
                self.assertEqual(data["triggers"], [])

    def test_single_import_new_format_and_export_round_trip(self):
        source = {"active_keymap_id": "b", "triggers": [{"key": "ignored"}],
                  "keymaps": [{"id": "a", "triggers": [{"key": "f7"}]},
                              {"id": "b", "triggers": [{"key": "f8", "actions": [{"type": "text", "value": "hi"}]}]}]}
        data = self.service.load(self.write("import.json", source))
        self.assertEqual([[t["key"] for t in item["triggers"]] for item in data["keymaps"]], [["f7"], ["f8"]])
        self.assertEqual(data["triggers"], [])
        expected = [safe_deepcopy(item["triggers"]) for item in data["keymaps"]]
        for item in data["keymaps"]:
            item.update(_trigger_set_source_path="set.json", _trigger_set_parent_refs=["km.json"],
                        _trigger_set_dirty=True, _trigger_set_imported=True)
            item["triggers"][0].update(_sequence_source_path="seq.json", _sequence_parent_refs=["set.json"],
                                       _sequence_dirty=True, _sequence_imported=True)
        data["_legacy_trigger_set"] = {"state": "none", "path": "", "keymap_id": ""}
        path = os.path.join(self.root, "export.json")
        self.service.export_runtime_data(path, data)
        exported = self.service.repository.load_json(path)
        self.assertEqual(exported["triggers"], [])
        self.assertNotIn("_legacy_trigger_set", exported)
        for item in exported["keymaps"]:
            self.assertFalse(any(key.startswith("_") for key in item))
            self.assertFalse(any(key.startswith("_") for key in item["triggers"][0]))
        reloaded = self.service.load(path)
        self.assertEqual([item["id"] for item in reloaded["keymaps"]], ["a", "b"])
        for item, original in zip(reloaded["keymaps"], expected):
            self.assertEqual(item["triggers"], original)
        self.assertEqual(reloaded["active_keymap_id"], "b")

        keymap_set_path = os.path.join(self.root, "user", "keymap_sets", "roundtrip.json")
        self.service.save_runtime_data(keymap_set_path, reloaded, config_root=self.root)
        bulk_reloaded = self.service.load_runtime_data_from_keymap_set_path(
            keymap_set_path, config_root=self.root,
        )
        self.assertEqual(
            [
                [(trigger["key"], trigger.get("actions", [])) for trigger in item["triggers"]]
                for item in bulk_reloaded["keymaps"]
            ],
            [
                [(trigger["key"], trigger.get("actions", [])) for trigger in triggers]
                for triggers in expected
            ],
        )

    def test_export_duplicates_shared_content_without_mutating_runtime(self):
        shared = [{"key": "f1", "_sequence_dirty": True, "actions": []}]
        data = {"keymaps": [{"id": "a", "triggers": shared}, {"id": "b", "triggers": shared}],
                "active_keymap_id": "a", "triggers": []}
        path = os.path.join(self.root, "export.json")
        self.service.export_runtime_data(path, data)
        exported = self.service.repository.load_json(path)
        self.assertEqual(exported["keymaps"][0]["triggers"], exported["keymaps"][1]["triggers"])
        self.assertEqual(exported["keymaps"][0]["triggers"][0]["key"], "f1")
        self.assertNotIn("_sequence_dirty", exported["keymaps"][0]["triggers"][0])
        self.assertTrue(shared[0]["_sequence_dirty"])
        self.assertIs(data["keymaps"][0]["triggers"], data["keymaps"][1]["triggers"])


class LegacyNotificationTest(unittest.TestCase):
    def test_normal_load_notifies_after_completion_dialog(self):
        app = Mock()
        app.config_service.load_runtime_data_from_keymap_set_path.return_value = {
            "_legacy_trigger_set": {
                "state": "migrated", "path": "old.json", "keymap_id": "legacy", "auto_created": True,
            },
        }
        app.keymap_service.find_keymap.return_value = {"label": "旧トリガー一覧（old）"}
        app.keymap_set_history_io.record.return_value = (True, "")
        io = KeymapSetIo(app)
        with patch("keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.showinfo") as show:
            self.assertEqual(io.load_keymap_set_path("set.json"), "ok")
        self.assertEqual(show.call_count, 2)
        self.assertEqual(show.call_args_list[0].args, ("読込", "読み込みました:\nset.json"))
        self.assertEqual(show.call_args_list[1].args, (
            "読込", "旧形式のトリガー一覧 old.json を、キーマップ『旧トリガー一覧（old）』に移しました（切替キーは未設定です）",
        ))

    def test_only_auto_created_migration_shows_information(self):
        for state, auto_created in (("none", False), ("migrated", False), ("same", False), ("migrated", True)):
            with self.subTest(state=state), patch("keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.showinfo") as show:
                data = {"_legacy_trigger_set": {
                    "state": state, "path": "old.json", "keymap_id": "legacy", "auto_created": auto_created,
                }}
                app = SimpleNamespace(
                    data=data,
                    keymap_service=SimpleNamespace(find_keymap=Mock(return_value={"label": "Legacy"})),
                )
                io = KeymapSetIo(app)
                io.notify_migrated_legacy_trigger_set()
                if auto_created:
                    show.assert_called_once_with(
                        "読込", "旧形式のトリガー一覧 old.json を、キーマップ『Legacy』に移しました（切替キーは未設定です）",
                    )
                else:
                    show.assert_not_called()

    def test_startup_schedules_notification_once_after_loading(self):
        app = Mock()
        app._startup_settings = {"keymap_set_path": "set.json"}
        app.paths.resolve_keymap_set_path.return_value = "set.json"
        io = StartupIo(app)
        with patch("keyseq.presentation.controllers.config_io.startup_io.os.path.exists", return_value=True):
            io.load_startup_and_config()
        app.after.assert_called_once_with(0, app.keymap_set_io.notify_migrated_legacy_trigger_set)
        app.keymap_set_io.notify_migrated_legacy_trigger_set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
