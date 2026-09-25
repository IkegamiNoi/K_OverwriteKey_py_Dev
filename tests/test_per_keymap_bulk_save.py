"""履歴25 §4.2/4.4/5.1/5.3/5.4/5.5 の一括保存契約。"""
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.app_state import AppState
from keyseq.application.config_service import ConfigService
from keyseq.application.keymap_service import KeymapService
from keyseq.application.save_plan import (
    ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP, CHILD_KEYMAP, CHILD_TRIGGER_SET,
    CHILD_SEQUENCE, ChildSaveEntry, SavePlan, SavePlanError,
    compose_sequence_key, split_sequence_key,
)
from keyseq.domain.keymap_triggers import (
    INTERNAL_TRIGGER_SET_DIRTY,
    INTERNAL_TRIGGER_SET_IMPORTED,
    iter_trigger_sets,
    trigger_set_members,
    trigger_set_owner,
)
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.controllers.config_io.child_save_plan import build_save_plan
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_OTHER_PARENT,
    SHARE_SOLE,
    collect_child_save_rows,
)
from keyseq.presentation.controllers.config_io.child_save_dialog import ChildSaveDialog
from keyseq.presentation.controllers.dirty_state import DirtyStateTracker


class PerKeymapBulkSaveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = self.temp.name
        self.repo = JsonRepository()
        self.service = ConfigService(self.repo)
        self.path = os.path.join(self.root, "user", "keymap_sets", "main.json")

    def write(self, path, payload):
        self.repo.save_json(os.path.join(self.root, path), payload)

    def read(self, path):
        return self.repo.load_json(os.path.join(self.root, path))

    def legacy(self):
        self.write("user/keymaps/a.json", {"label": "A", "mappings": {}})
        self.write("user/keymaps/b.json", {"label": "B", "mappings": {}})
        self.write("user/sequences/old.json", {"actions": [{"type": "text", "value": "old"}]})
        self.write("user/trigger_sets/old.json", {"triggers": [{"key": "f1", "sequence_path": "user/sequences/old.json"}]})
        self.repo.save_json(self.path, {
            "keymaps": [{"path": "user/keymaps/a.json"}, {"path": "user/keymaps/b.json"}],
            "active_keymap_path": "user/keymaps/a.json", "trigger_set_path": "user/trigger_sets/old.json",
        })
        return self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)

    def targets(self, data):
        return self.service.resolve_child_save_targets(data, config_root=self.root, keymap_set_path=self.path)

    def rows(self, data):
        return collect_child_save_rows(data=data, dirty_tracker=None, config_service=self.service,
                                       config_root=self.root, keymap_set_path=self.path)

    def save(self, data, plan=None, *, path=None, post_save_warnings=None):
        return self.service.save_runtime_data(
            path or self.path,
            data,
            config_root=self.root,
            save_plan=plan,
            migration_source_keymap_set_path=self.path,
            post_save_warnings=post_save_warnings,
        )[0]

    def shared_runtime(self):
        self.write("user/keymaps/a.json", {
            "id": "a", "label": "A", "mappings": {},
            "trigger_set_path": "user/trigger_sets/own.json",
        })
        self.write("user/keymaps/b.json", {
            "id": "b", "label": "B", "mappings": {},
            "trigger_set_path": "user/trigger_sets/shared.json",
        })
        self.write("user/sequences/own_f2.json", {"actions": [], "_parent_refs": ["user/trigger_sets/own.json"]})
        self.write("user/sequences/shared_f1.json", {"actions": [], "_parent_refs": ["user/trigger_sets/shared.json"]})
        self.write("user/trigger_sets/own.json", {
            "triggers": [{"key": "f2", "sequence_path": "user/sequences/own_f2.json"}],
            "_parent_refs": ["user/keymaps/a.json"],
        })
        self.write("user/trigger_sets/shared.json", {
            "triggers": [{"key": "f1", "sequence_path": "user/sequences/shared_f1.json"}],
            "_parent_refs": ["user/keymaps/b.json"],
        })
        self.repo.save_json(self.path, {
            "keymaps": [{"path": "user/keymaps/a.json"}, {"path": "user/keymaps/b.json"}],
            "active_keymap_path": "user/keymaps/a.json",
            "keymap_switch_keys": {"f9": "b"},
        })
        return self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)

    def save_all_rows(self, data):
        rows = self.rows(data)
        choices = {(row.kind, row.key): (ACTION_SAVE, "") for row in rows}
        return self.save(
            data,
            build_save_plan(data=data, rows=rows, choices=choices, targets=self.targets(data)),
        )

    def test_trigger_set_load_joins_existing_shared_instance_and_saves_parent_ref(self):
        from keyseq.application.app_state import AppState
        from keyseq.presentation.controllers.config_io.trigger_set_file_io import TriggerSetFileIo

        data = self.shared_runtime()
        tracker = DirtyStateTracker(
            get_data=lambda: data,
            keymap_service=KeymapService(),
            config_service=self.service,
            on_change=Mock(),
        )
        app = SimpleNamespace(
            data=data,
            config_service=self.service,
            config_root=self.root,
            keymap_service=KeymapService(),
            dirty_tracker=tracker,
            state=AppState(),
            trigger_panel=SimpleNamespace(refresh_triggers=Mock(), refresh_actions=Mock()),
            _set_flash_message=Mock(),
        )

        with patch(
            "keyseq.presentation.controllers.config_io.trigger_set_file_io.messagebox.showinfo"
        ):
            TriggerSetFileIo(app)._apply_loaded_trigger_set(
                os.path.join(self.root, "user", "trigger_sets", "shared.json")
            )

        self.assertIs(data["keymaps"][0]["triggers"], data["keymaps"][1]["triggers"])
        self.assertTrue(data["keymaps"][0][INTERNAL_TRIGGER_SET_DIRTY])
        self.assertTrue(data["keymaps"][1][INTERNAL_TRIGGER_SET_DIRTY])
        self.save_all_rows(data)
        self.assertEqual(
            set(self.read("user/trigger_sets/shared.json")[self.service.PARENT_REFS_KEY]),
            {"user/keymaps/a.json", "user/keymaps/b.json"},
        )

    def test_keymap_load_joining_existing_shared_instance_saves_new_parent_ref(self):
        from keyseq.presentation.controllers.config_io.keymap_file_io import KeymapFileIo

        data = self.shared_runtime()
        tracker = DirtyStateTracker(
            get_data=lambda: data,
            keymap_service=KeymapService(),
            config_service=self.service,
            on_change=Mock(),
        )

        def append_imported_keymap(keymap):
            data["keymaps"].append(keymap)
            KeymapService.set_keymap_switch_key(data, "f10", str(keymap.get("id") or ""))
            tracker.mark_keymap_dirty(keymap)
            return True

        app = SimpleNamespace(
            data=data,
            config_service=self.service,
            config_root=self.root,
            keymap_service=KeymapService(),
            dirty_tracker=tracker,
            keymap_panel=SimpleNamespace(add_imported_keymap=Mock(side_effect=append_imported_keymap)),
            paths=SimpleNamespace(
                preferred_keymaps_dir=Mock(return_value=self.root),
                json_dialog_initial_dir=Mock(return_value=self.root),
            ),
            _set_flash_message=Mock(),
        )
        imported_path = os.path.join(self.root, "user", "keymaps", "c.json")
        self.write("user/keymaps/c.json", {
            "id": "c", "label": "C", "mappings": {},
            "trigger_set_path": "user/trigger_sets/shared.json",
        })

        with patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.filedialog.askopenfilename",
            return_value=imported_path,
        ), patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.messagebox.showinfo"
        ):
            KeymapFileIo(app).load_keymap_file()

        imported = KeymapService.find_keymap(data, "c")
        shared = KeymapService.find_keymap(data, "b")
        self.assertIs(imported["triggers"], shared["triggers"])
        self.assertTrue(imported[INTERNAL_TRIGGER_SET_DIRTY])
        self.assertTrue(shared[INTERNAL_TRIGGER_SET_DIRTY])
        self.save_all_rows(data)
        self.assertEqual(
            set(self.read("user/trigger_sets/shared.json")[self.service.PARENT_REFS_KEY]),
            {"user/keymaps/b.json", "user/keymaps/c.json"},
        )

    def test_keymap_default_name_uses_label_or_keymap_set_stem(self):
        data = {"active_keymap_id": "first", "keymaps": [
            {"id": "first", "label": "", "triggers": []},
            {"id": "second", "label": "", "triggers": []},
            {"id": "named", "label": "Named", "triggers": []},
        ]}
        targets = self.service.resolve_child_save_targets(
            data, config_root=self.root, keymap_set_path=self.path,
        )

        self.assertEqual(os.path.basename(targets[(CHILD_KEYMAP, "first")]), "main.json")
        self.assertEqual(os.path.basename(targets[(CHILD_KEYMAP, "second")]), "main_2.json")
        self.assertEqual(os.path.basename(targets[(CHILD_KEYMAP, "named")]), "Named.json")

        without_keymap_set = {"active_keymap_id": "id-only", "keymaps": [
            {"id": "id-only", "label": "", "triggers": []},
        ]}
        targets = self.service.resolve_child_save_targets(
            without_keymap_set, config_root=self.root, keymap_set_path="",
        )
        self.assertEqual(os.path.basename(targets[(CHILD_KEYMAP, "id-only")]), "id-only.json")

    def test_keymap_save_as_recalculates_unsourced_trigger_set_default_name(self):
        from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo

        data = {"active_keymap_id": "owner", "keymaps": [{
            "id": "owner", "label": "Original", "triggers": [{"key": "f1", "actions": []}],
        }]}
        map_entry = ChildSaveEntry(CHILD_KEYMAP, "owner", ACTION_SAVE_AS, "user/keymaps/alias.json")
        trigger_entry = ChildSaveEntry(CHILD_TRIGGER_SET, "owner", ACTION_SAVE)
        plan = SavePlan((map_entry, trigger_entry))
        targets_before = self.service.resolve_child_save_targets(
            data, config_root=self.root, keymap_set_path=self.path,
        )
        io = KeymapSetIo(SimpleNamespace(config_service=self.service, data=data, config_root=self.root))

        self.assertTrue(io._trigger_target_changed(
            trigger_entry, targets_before, self.path, "", plan,
        ))

        targets = self.service.resolve_child_save_targets(
            data, config_root=self.root, keymap_set_path=self.path, save_plan=plan,
        )

        self.assertEqual(os.path.basename(targets[(CHILD_TRIGGER_SET, "owner")]), "alias.json")

    def test_keymap_skip_keeps_old_trigger_set_path_and_dirty_mark(self):
        self.write("user/sequences/keep.json", {"actions": []})
        self.write("user/trigger_sets/keep.json", {
            "triggers": [{"key": "f1", "sequence_path": "user/sequences/keep.json"}],
            "_parent_refs": ["user/keymaps/a.json"],
        })
        self.write("user/keymaps/a.json", {
            "label": "A", "mappings": {}, "trigger_set_path": "user/trigger_sets/keep.json",
            "_parent_refs": ["user/keymap_sets/main.json"],
        })
        self.repo.save_json(self.path, {
            "keymaps": [{"path": "user/keymaps/a.json"}],
            "active_keymap_path": "user/keymaps/a.json", "trigger_set_path": "",
        })
        data = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        source_tracker = DirtyStateTracker(
            get_data=lambda: data, keymap_service=KeymapService(),
            config_service=self.service, on_change=Mock(),
        )
        source_tracker.mark_keymap_dirty(data["keymaps"][0])
        plan = SavePlan((
            ChildSaveEntry(CHILD_KEYMAP, "a", ACTION_SKIP),
            ChildSaveEntry(CHILD_TRIGGER_SET, "a", ACTION_SAVE),
            ChildSaveEntry(CHILD_SEQUENCE, compose_sequence_key("a", "f1"), ACTION_SAVE),
        ))

        saved = self.save(data, plan)
        tracker = DirtyStateTracker(
            get_data=lambda: saved, keymap_service=KeymapService(),
            config_service=self.service, on_change=Mock(),
        )
        tracker.clear_individual_dirty_flags(skipped_keymap_ids=["a"])

        self.assertEqual(
            self.read("user/keymaps/a.json")["trigger_set_path"], "user/trigger_sets/keep.json",
        )
        self.assertTrue(saved["keymaps"][0][self.service.INTERNAL_KEYMAP_DIRTY])
        self.assertTrue(tracker.has_unsaved_changes())

    def test_trigger_list_positions_survive_bulk_save_data_replacement(self):
        data = {"active_keymap_id": "a", "keymaps": [{
            "id": "a", "triggers": [
                {"key": "f1", "actions": [
                    {"type": "text", "value": "one"},
                    {"type": "text", "value": "two"},
                ]},
                {"key": "f2", "actions": []},
            ],
        }]}
        state = AppState()
        trigger_set_id = KeymapService.get_active_trigger_set_id(data)
        state.update_selected_index(1, trigger_set_id)
        state.indices_for(trigger_set_id)["f1"] = 1

        saved = self.save(data)
        saved_trigger_set_id = KeymapService.get_active_trigger_set_id(saved)

        self.assertEqual(saved_trigger_set_id, trigger_set_id)
        self.assertEqual(state.get_selected_index(saved_trigger_set_id), 1)
        self.assertEqual(state.indices_for(saved_trigger_set_id)["f1"], 1)

    def test_trigger_list_positions_survive_individual_save_list_replacement(self):
        from keyseq.presentation.controllers.config_io.trigger_set_file_io import TriggerSetFileIo

        data = {"active_keymap_id": "a", "keymaps": [{
            "id": "a", "triggers": [
                {"key": "f1", "actions": [
                    {"type": "text", "value": "one"},
                    {"type": "text", "value": "two"},
                ]},
                {"key": "f2", "actions": []},
            ],
        }]}
        state = AppState()
        trigger_set_id = KeymapService.get_active_trigger_set_id(data)
        state.update_selected_index(1, trigger_set_id)
        state.indices_for(trigger_set_id)["f1"] = 1
        tracker = DirtyStateTracker(get_data=lambda: data, keymap_service=KeymapService(),
                                    config_service=self.service, on_change=Mock())
        app = SimpleNamespace(
            data=data, config_service=self.service, config_root=self.root,
            keymap_set_path=self.path, dirty_tracker=tracker, trigger_panel=Mock(),
            _set_flash_message=Mock(),
        )

        TriggerSetFileIo(app)._save_trigger_set(
            os.path.join(self.root, "user", "trigger_sets", "individual.json"), SavePlan(),
        )
        saved_trigger_set_id = KeymapService.get_active_trigger_set_id(data)

        self.assertEqual(saved_trigger_set_id, trigger_set_id)
        self.assertEqual(state.get_selected_index(saved_trigger_set_id), 1)
        self.assertEqual(state.indices_for(saved_trigger_set_id)["f1"], 1)

    def test_keymap_import_inherits_shared_trigger_set_dirty_state(self):
        from keyseq.presentation.controllers.config_io.keymap_file_io import KeymapFileIo

        shared = [{"key": "f1", "actions": [{"type": "text", "value": "edited"}]}]
        data = {"active_keymap_id": "a", "keymaps": [{
            "id": "a", "triggers": shared,
            self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH: "user/trigger_sets/shared.json",
            self.service.INTERNAL_TRIGGER_SET_PARENT_REFS: ["user/keymaps/a.json"],
            INTERNAL_TRIGGER_SET_DIRTY: True,
            INTERNAL_TRIGGER_SET_IMPORTED: False,
        }]}
        self.write("user/keymaps/b.json", {
            "id": "b", "mappings": {}, "trigger_set_path": "user/trigger_sets/shared.json",
        })
        app = SimpleNamespace(data=data, config_service=self.service, config_root=self.root, keymap_service=KeymapService())
        imported = KeymapFileIo(app)._load_keymap(os.path.join(self.root, "user", "keymaps", "b.json"))
        data["keymaps"].append(imported)

        self.assertTrue(imported[INTERNAL_TRIGGER_SET_DIRTY])
        self.assertFalse(imported[INTERNAL_TRIGGER_SET_IMPORTED])
        KeymapService.delete_keymap(data, "a")

        rows = self.rows(data)
        self.assertIn((CHILD_TRIGGER_SET, "b"), [(row.kind, row.key) for row in rows])
        saved = self.save(data)
        self.assertEqual(saved["keymaps"][0]["triggers"][0]["actions"][0]["value"], "edited")

    def test_skipped_unsourced_trigger_set_does_not_index_existing_default_file(self):
        data = {"active_keymap_id": "a", "keymaps": [{
            "id": "a", "label": "Main", "triggers": [{
                "key": "f1", "actions": [],
            }],
        }]}
        trigger_key = compose_sequence_key("a", "f1")
        targets = self.targets(data)
        trigger_path = targets[(CHILD_TRIGGER_SET, "a")]
        sequence_path = targets[(CHILD_SEQUENCE, trigger_key)]
        self.repo.save_json(
            self.service._resolve_config_relative_path(trigger_path, self.root),
            {"triggers": [{"key": "other"}]},
        )
        self.repo.save_json(
            self.service._resolve_config_relative_path(sequence_path, self.root),
            {"actions": []},
        )
        data["keymaps"][0]["triggers"][0][self.service.INTERNAL_SEQUENCE_SOURCE_PATH] = sequence_path
        plan = SavePlan((
            ChildSaveEntry(CHILD_TRIGGER_SET, "a", ACTION_SKIP),
            ChildSaveEntry(CHILD_SEQUENCE, trigger_key, ACTION_SKIP),
        ))

        saved = self.save(data, plan)

        keymap_path = saved["keymaps"][0][self.service.INTERNAL_KEYMAP_SOURCE_PATH]
        resolved_keymap_path = self.service._resolve_config_relative_path(keymap_path, self.root)
        self.assertEqual(self.service.repository.load_json(resolved_keymap_path)["trigger_set_path"], "")

    def test_instance_lookup_ignores_missing_ids_and_normalizes_lookup(self):
        shared = []
        missing = {"triggers": shared}
        first = {"id": " A ", "triggers": shared}
        second = {"id": "B", "triggers": shared}
        other = {"id": "c", "triggers": []}
        data = {"keymaps": [missing, first, second, other], "active_keymap_id": " b "}
        groups = list(iter_trigger_sets(data))
        self.assertEqual(len(groups), 2)
        self.assertIs(groups[0][0], first)
        self.assertEqual(trigger_set_members(data), [first, second])
        self.assertIs(trigger_set_owner(data, " a "), first)
        self.assertIs(trigger_set_owner(data, " C "), other)
        self.assertEqual(trigger_set_members(data, ""), [])
        self.assertEqual(trigger_set_owner({"keymaps": [missing]}), {})
        self.assertEqual(self.rows({"keymaps": [missing]}), [])

    def test_trigger_state_access_does_not_create_missing_keymap(self):
        setters = (
            lambda tracker: tracker.set_trigger_set_source_path("saved.json"),
            lambda tracker: tracker.mark_trigger_set_dirty(),
            lambda tracker: setattr(tracker, "trigger_set_imported", True),
            lambda tracker: tracker.reset_trigger_set_state(),
            lambda tracker: tracker.sync_trigger_set_source_path_from_data(),
        )
        for index, setter in enumerate(setters):
            with self.subTest(setter=index):
                data = {"keymaps": [], "active_keymap_id": ""}
                tracker = DirtyStateTracker(get_data=lambda: data, keymap_service=KeymapService(),
                                            config_service=self.service, on_change=Mock())
                self.assertEqual(tracker.trigger_set_source_path, "")
                self.assertFalse(tracker.trigger_set_dirty)
                self.assertFalse(tracker.trigger_set_imported)
                self.assertEqual(data, {"keymaps": [], "active_keymap_id": ""})
                setter(tracker)
                self.assertEqual(data, {"keymaps": [], "active_keymap_id": ""})
                self.assertEqual(tracker.trigger_set_source_path, "")
                self.assertFalse(tracker.trigger_set_dirty)
                self.assertFalse(tracker.trigger_set_imported)

    def test_individual_trigger_save_as_marks_all_shared_parents_for_bulk_save(self):
        from keyseq.presentation.controllers.config_io.trigger_set_file_io import TriggerSetFileIo
        shared = [{"key": "f1", "actions": []}]
        data = self.save({"active_keymap_id": "b", "keymaps": [
            {"id": "a", self.service.INTERNAL_KEYMAP_SOURCE_PATH: "user/keymaps/a.json",
             "triggers": shared},
            {"id": "b", self.service.INTERNAL_KEYMAP_SOURCE_PATH: "user/keymaps/b.json",
             "triggers": shared},
            {"id": "c", "triggers": []},
        ]})
        tracker = DirtyStateTracker(get_data=lambda: data, keymap_service=KeymapService(),
                                    config_service=self.service, on_change=Mock())
        tracker.clear_individual_dirty_flags()
        app = SimpleNamespace(data=data, config_service=self.service, config_root=self.root,
                              keymap_set_path=self.path, dirty_tracker=tracker,
                              child_save_dialog=Mock(), trigger_panel=Mock(), _set_flash_message=Mock())
        target = os.path.join(self.root, "user", "trigger_sets", "renamed.json")
        with patch("keyseq.presentation.controllers.config_io.trigger_set_file_io.messagebox.showinfo"):
            self.assertTrue(TriggerSetFileIo(app).save_trigger_set_to_path(target))
        self.assertEqual(self.read("user/trigger_sets/renamed.json")["_parent_refs"], [
            "user/keymaps/a.json", "user/keymaps/b.json",
        ])
        app.child_save_dialog.ask_child_save_actions.assert_not_called()
        self.assertIs(data["keymaps"][0]["triggers"], data["keymaps"][1]["triggers"])
        for member in data["keymaps"][:2]:
            self.assertTrue(member[self.service.INTERNAL_KEYMAP_DIRTY])
            self.assertEqual(member[self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH], "user/trigger_sets/renamed.json")
        self.assertFalse(data["keymaps"][2][self.service.INTERNAL_KEYMAP_DIRTY])
        rows = self.rows(data)
        self.assertEqual([(row.kind, row.key) for row in rows], [(CHILD_KEYMAP, "a"), (CHILD_KEYMAP, "b")])
        plan = build_save_plan(data=data, rows=rows,
                               choices={(row.kind, row.key): (ACTION_SAVE, "") for row in rows},
                               targets=self.targets(data), confirmed=SavePlan())
        saved = self.save(data, plan)
        self.assertEqual(self.repo.load_json(self.path)["trigger_set_path"], "")
        for member in saved["keymaps"][:2]:
            self.assertEqual(self.read(member[self.service.INTERNAL_KEYMAP_SOURCE_PATH])["trigger_set_path"],
                             "user/trigger_sets/renamed.json")

    def test_rows_use_normalized_owner_id(self):
        data = {"active_keymap_id": " A ", "keymaps": [{
            "id": " A ", self.service.INTERNAL_KEYMAP_SOURCE_PATH: "user/keymaps/a.json",
            "_trigger_set_dirty": True,
            "triggers": [{"key": " F1 ", "actions": [], "_sequence_dirty": True}],
        }]}
        self.assertEqual([(row.kind, row.key) for row in self.rows(data)], [
            (CHILD_TRIGGER_SET, "a"), (CHILD_SEQUENCE, compose_sequence_key("a", "f1")),
        ])

    def test_parent_edit_after_save_preserves_implicit_and_explicit_hook_modes(self):
        for mode in (None, False, True):
            with self.subTest(mode=mode):
                data = {"active_keymap_id": "a", "keymaps": [{
                    "id": "a", "triggers": [{"key": "f1", "actions": []}],
                }]}
                if mode is not None:
                    data["hook_keys_individual"] = mode
                data = self.save(data)
                if mode is None:
                    self.assertNotIn("hook_keys_individual", data)
                else:
                    self.assertIs(data["hook_keys_individual"], mode)
                targets = self.targets(data)
                before = {key: self.repo.load_json(path) for key, path in targets.items()}
                data["hook_stop_key"] = "f11"
                self.save(data, SavePlan(entries=tuple(
                    ChildSaveEntry(kind, key, ACTION_SKIP) for kind, key in targets
                )))
                parent = self.repo.load_json(self.path)
                self.assertEqual(parent["hook_stop_key"], "" if mode is False else "f11")
                self.assertIs(parent["hook_keys_individual"], mode is not False)
                self.assertEqual({key: self.repo.load_json(path) for key, path in targets.items()}, before)

    def test_normal_load_clears_dirty_but_migration_does_not(self):
        from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
        for state in (None, "none", "same", "migrated"):
            with self.subTest(state=state):
                loaded = {} if state is None else {"_legacy_trigger_set": {"state": state}}
                app = Mock()
                app.config_service.load_runtime_data_from_keymap_set_path.return_value = loaded
                app.keymap_set_history_io.record.return_value = (True, "")
                io = KeymapSetIo(app)
                with patch.object(io, "apply_loaded_data_to_ui"), patch.object(io, "notify_migrated_legacy_trigger_set"), patch(
                    "keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.showinfo"
                ):
                    self.assertEqual(io.load_keymap_set_path(self.path), "ok")
                if state == "migrated":
                    app.dirty_tracker.set_dirty.assert_not_called()
                else:
                    app.dirty_tracker.set_dirty.assert_called_once_with(False)

    def test_legacy_round_trip_without_edits(self):
        data = self.legacy()
        owner = data["keymaps"][0]
        self.assertTrue(owner[self.service.INTERNAL_KEYMAP_DIRTY])
        rows = self.rows(data)
        plan = build_save_plan(data=data, rows=rows,
                              choices={(row.kind, row.key): (ACTION_SAVE, "") for row in rows},
                              targets=self.targets(data))
        saved = self.save(data, plan)
        self.assertEqual(self.read("user/keymaps/a.json")["trigger_set_path"], "user/trigger_sets/old.json")
        self.assertEqual(self.repo.load_json(self.path)["trigger_set_path"], "")
        loaded = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        self.assertEqual(loaded["keymaps"][0]["triggers"][0]["actions"][0]["value"], "old")
        self.assertEqual(saved[self.service.INTERNAL_LEGACY_TRIGGER_SET]["state"], "none")
        self.assertNotIn(self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH, saved)
        self.assertNotIn(self.service.INTERNAL_TRIGGER_SET_PARENT_REFS, saved)

    def test_migrated_trigger_set_uses_origin_as_parent_then_prunes_after_overwrite(self):
        data = self.legacy()
        trigger_path = data["keymaps"][0][self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH]
        trigger_payload = self.read(trigger_path)
        trigger_payload[self.service.PARENT_REFS_KEY] = ["user/keymap_sets/main.json"]
        self.write(trigger_path, trigger_payload)

        rows = self.rows(data)
        trigger_row = next(row for row in rows if row.kind == CHILD_TRIGGER_SET)
        self.assertEqual(trigger_row.share_state, SHARE_SOLE)
        self.assertNotEqual(trigger_row.share_state, SHARE_OTHER_PARENT)
        plan = build_save_plan(
            data=data, rows=rows,
            choices={(row.kind, row.key): (ACTION_SAVE, "") for row in rows},
            targets=self.targets(data),
        )
        saved_refs = []
        real_save = self.repo.save_json

        def capture_trigger_refs(path, payload):
            if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(
                os.path.join(self.root, trigger_path)
            )):
                saved_refs.append(list(payload.get(self.service.PARENT_REFS_KEY, [])))
            real_save(path, payload)

        with patch.object(self.repo, "save_json", side_effect=capture_trigger_refs):
            saved = self.save(data, plan)

        self.assertEqual(len(saved_refs), 2)
        self.assertEqual(set(saved_refs[0]), {"user/keymap_sets/main.json", "user/keymaps/a.json"})
        self.assertEqual(saved_refs[1], ["user/keymaps/a.json"])
        self.assertEqual(self.read(trigger_path)[self.service.PARENT_REFS_KEY], ["user/keymaps/a.json"])
        self.assertEqual(
            saved["keymaps"][0][self.service.INTERNAL_TRIGGER_SET_PARENT_REFS],
            ["user/keymaps/a.json"],
        )

    def test_migrated_trigger_set_alias_and_keymap_set_write_failure_keep_origin_ref(self):
        data = self.legacy()
        trigger_path = data["keymaps"][0][self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH]
        trigger_payload = self.read(trigger_path)
        trigger_payload[self.service.PARENT_REFS_KEY] = ["user/keymap_sets/main.json"]
        self.write(trigger_path, trigger_payload)
        alias_path = os.path.join(self.root, "user", "keymap_sets", "alias.json")

        targets = self.service.resolve_child_save_targets(
            data, config_root=self.root, keymap_set_path=alias_path,
        )
        rows = collect_child_save_rows(
            data=data, dirty_tracker=None, config_service=self.service,
            config_root=self.root, keymap_set_path=alias_path,
            migration_source_path=self.path,
        )
        plan = build_save_plan(
            data=data, rows=rows,
            choices={(row.kind, row.key): (ACTION_SAVE, "") for row in rows},
            targets=targets,
        )
        self.save(data, plan, path=alias_path)
        self.assertEqual(
            set(self.read(trigger_path)[self.service.PARENT_REFS_KEY]),
            {"user/keymap_sets/main.json", "user/keymaps/a.json"},
        )

        data = self.legacy()
        trigger_path = data["keymaps"][0][self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH]
        trigger_payload = self.read(trigger_path)
        trigger_payload[self.service.PARENT_REFS_KEY] = ["user/keymap_sets/main.json"]
        self.write(trigger_path, trigger_payload)
        rows = self.rows(data)
        plan = build_save_plan(
            data=data, rows=rows,
            choices={(row.kind, row.key): (ACTION_SAVE, "") for row in rows},
            targets=self.targets(data),
        )
        real_save = self.repo.save_json

        def fail_keymap_set(path, payload):
            if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(self.path)):
                raise OSError("keymap_set write failed")
            real_save(path, payload)

        with patch.object(self.repo, "save_json", side_effect=fail_keymap_set), self.assertRaises(OSError):
            self.save(data, plan)

        self.assertEqual(
            set(self.read(trigger_path)[self.service.PARENT_REFS_KEY]),
            {"user/keymap_sets/main.json", "user/keymaps/a.json"},
        )

    def test_migrated_trigger_set_cleanup_failure_is_a_save_warning(self):
        data = self.legacy()
        trigger_path = data["keymaps"][0][self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH]
        trigger_payload = self.read(trigger_path)
        trigger_payload[self.service.PARENT_REFS_KEY] = ["user/keymap_sets/main.json"]
        self.write(trigger_path, trigger_payload)
        rows = self.rows(data)
        plan = build_save_plan(
            data=data, rows=rows,
            choices={(row.kind, row.key): (ACTION_SAVE, "") for row in rows},
            targets=self.targets(data),
        )
        real_save = self.repo.save_json
        trigger_writes = 0

        def fail_cleanup_write(path, payload):
            nonlocal trigger_writes
            if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(
                os.path.join(self.root, trigger_path)
            )):
                trigger_writes += 1
                if trigger_writes == 2:
                    raise OSError("cleanup write failed")
            real_save(path, payload)

        warnings = []
        with patch.object(self.repo, "save_json", side_effect=fail_cleanup_write):
            saved = self.save(data, plan, post_save_warnings=warnings)

        self.assertEqual(saved[self.service.INTERNAL_LEGACY_TRIGGER_SET]["state"], "none")
        self.assertEqual(len(warnings), 1)
        self.assertIn("参照整理に失敗しました", warnings[0])
        self.assertEqual(
            set(self.read(trigger_path)[self.service.PARENT_REFS_KEY]),
            {"user/keymap_sets/main.json", "user/keymaps/a.json"},
        )

    def test_migration_stays_on_original_keymap_after_active_switch(self):
        data = self.legacy()
        data["active_keymap_id"] = data["keymaps"][1]["id"]
        self.save(data)
        loaded = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        self.assertEqual([trigger["key"] for trigger in loaded["keymaps"][0]["triggers"]], ["f1"])
        self.assertEqual(loaded["keymaps"][1]["triggers"], [])
        self.assertEqual(loaded["active_keymap_id"], loaded["keymaps"][1]["id"])

    def test_migration_rejects_skip_in_plan_dialog_and_executor(self):
        data = self.legacy()
        rows = self.rows(data)
        row = next(row for row in rows if row.kind == CHILD_KEYMAP)
        trigger_set_row = next(row for row in rows if row.kind == CHILD_TRIGGER_SET)
        self.assertFalse(row.allow_skip)
        self.assertFalse(trigger_set_row.allow_skip)
        choices = {(item.kind, item.key): (ACTION_SAVE, "") for item in rows}
        choices[(row.kind, row.key)] = (ACTION_SKIP, "")
        with self.assertRaises(SavePlanError):
            build_save_plan(data=data, rows=rows, choices=choices, targets=self.targets(data))
        choices[(row.kind, row.key)] = (ACTION_SAVE, "")
        choices[(trigger_set_row.kind, trigger_set_row.key)] = (ACTION_SKIP, "")
        with self.assertRaises(SavePlanError):
            build_save_plan(data=data, rows=rows, choices=choices, targets=self.targets(data))
        dialog = ChildSaveDialog(SimpleNamespace())
        module = "keyseq.presentation.controllers.config_io.child_save_dialog"
        with patch(f"{module}.tk.StringVar"), patch(f"{module}.ttk.Frame"), patch(
            f"{module}.ttk.Label"
        ), patch(f"{module}.ttk.Radiobutton") as radio, patch.object(dialog, "_add_text_cell"):
            dialog._add_rows(Mock(), [row], 1)
        self.assertEqual(
            [(call.kwargs["value"], call.kwargs["state"]) for call in radio.call_args_list],
            [(ACTION_SAVE, "normal"), (ACTION_SAVE_AS, "normal"), (ACTION_SKIP, "disabled")],
        )
        with patch(f"{module}.tk.StringVar"), patch(f"{module}.ttk.Frame"), patch(
            f"{module}.ttk.Label"
        ), patch(f"{module}.ttk.Radiobutton") as radio, patch.object(dialog, "_add_text_cell"):
            dialog._add_rows(Mock(), [trigger_set_row], 1)
        self.assertEqual(
            [(call.kwargs["value"], call.kwargs["state"]) for call in radio.call_args_list],
            [(ACTION_SAVE, "normal"), (ACTION_SAVE_AS, "normal"), (ACTION_SKIP, "disabled")],
        )
        with self.assertRaises(ValueError):
            dialog._resolve_action_targets([row], {(row.kind, row.key): SimpleNamespace(get=lambda: ACTION_SKIP)})
        with self.assertRaises(ValueError):
            dialog._resolve_action_targets(
                [trigger_set_row],
                {(trigger_set_row.kind, trigger_set_row.key): SimpleNamespace(get=lambda: ACTION_SKIP)},
            )
        with self.assertRaises(SavePlanError):
            self.save(data, SavePlan((ChildSaveEntry(CHILD_KEYMAP, row.key, ACTION_SKIP),), allow_deferred_index=True))
        with self.assertRaises(SavePlanError):
            self.save(
                data,
                SavePlan((ChildSaveEntry(CHILD_TRIGGER_SET, trigger_set_row.key, ACTION_SKIP),), allow_deferred_index=True),
            )
        self.assertEqual(self.repo.load_json(self.path)["trigger_set_path"], "user/trigger_sets/old.json")

    def test_shared_instance_has_one_row_and_one_file_and_all_parents(self):
        shared = [{"key": "f1", "actions": []}]
        data = {"active_keymap_id": "b", "keymaps": [
            {"id": "a", "label": "A", "triggers": shared, "_trigger_set_dirty": True},
            {"id": "b", "label": "B", "triggers": shared, "_trigger_set_dirty": True},
        ]}
        rows = self.rows(data)
        self.assertEqual([(row.kind, row.key) for row in rows], [
            (CHILD_KEYMAP, "a"),
            (CHILD_KEYMAP, "b"),
            (CHILD_TRIGGER_SET, "a"),
            (CHILD_SEQUENCE, compose_sequence_key("a", "f1")),
        ])
        self.assertEqual(sum(row.kind == CHILD_TRIGGER_SET for row in rows), 1)
        plan = build_save_plan(data=data, rows=[], choices={}, targets=self.targets(data))
        self.assertEqual([entry.key for entry in plan.entries if entry.kind == CHILD_TRIGGER_SET], ["a"])
        saved = self.save(data, plan)
        self.assertEqual(self.read("user/keymaps/A.json")["trigger_set_path"], "user/trigger_sets/A.json")
        self.assertEqual(self.read("user/keymaps/B.json")["trigger_set_path"], "user/trigger_sets/A.json")
        self.assertEqual(os.listdir(os.path.join(self.root, "user", "trigger_sets")), ["A.json"])
        self.assertIs(saved["keymaps"][0]["triggers"], saved["keymaps"][1]["triggers"])
        for owner in saved["keymaps"]:
            self.assertEqual(owner[self.service.INTERNAL_TRIGGER_SET_SOURCE_PATH], "user/trigger_sets/A.json")
            self.assertEqual(owner[self.service.INTERNAL_TRIGGER_SET_PARENT_REFS], ["user/keymaps/A.json", "user/keymaps/B.json"])
        loaded = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        self.assertEqual(len(list(iter_trigger_sets(loaded))), 1)

    def test_same_new_trigger_keys_use_distinct_sequence_files(self):
        data = {"active_keymap_id": "a", "keymaps": [
            {"id": key, "triggers": [{"key": "f1", "actions": [{"type": "text", "value": key}]}]}
            for key in ("a", "b")
        ]}
        targets = self.targets(data)
        first = targets[(CHILD_SEQUENCE, compose_sequence_key("a", "f1"))]
        second = targets[(CHILD_SEQUENCE, compose_sequence_key("b", "f1"))]
        self.assertNotEqual(first, second)
        saved = self.save(data)
        self.assertEqual(self.repo.load_json(first)["actions"][0]["value"], "a")
        self.assertEqual(self.repo.load_json(second)["actions"][0]["value"], "b")
        self.assertNotEqual(saved["keymaps"][0]["triggers"][0]["_sequence_source_path"], saved["keymaps"][1]["triggers"][0]["_sequence_source_path"])

    def test_empty_unsourced_list_has_no_file_but_sourced_empty_list_is_saved(self):
        data = {"active_keymap_id": "a", "keymaps": [
            {"id": "a", "triggers": []},
            {"id": "b", "triggers": [], "_trigger_set_source_path": "user/trigger_sets/b.json"},
        ]}
        self.assertNotIn((CHILD_TRIGGER_SET, "a"), self.targets(data))
        self.save(data)
        self.assertEqual(self.read("user/keymaps/main.json")["trigger_set_path"], "")
        self.assertEqual(os.listdir(os.path.join(self.root, "user", "trigger_sets")), ["b.json"])
        self.assertEqual(self.read("user/trigger_sets/b.json")["triggers"], [])

    def test_separate_active_trigger_reference_moves_legacy_list_to_new_keymap_and_round_trips(self):
        self.legacy()
        self.write("user/trigger_sets/new.json", {"triggers": []})
        self.write("user/keymaps/a.json", {
            "id": "a", "label": "A", "mappings": {}, "trigger_set_path": "user/trigger_sets/new.json",
        })
        data = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        legacy = data[self.service.INTERNAL_LEGACY_TRIGGER_SET]
        self.assertEqual(legacy["state"], "migrated")
        self.assertTrue(legacy["auto_created"])
        self.assertEqual(data["active_keymap_id"], "a")
        target = KeymapService.find_keymap(data, legacy["keymap_id"])
        self.assertEqual(target["label"], "旧トリガー一覧（old）")
        self.assertTrue(target["_keymap_dirty"])
        saved = self.save(data)
        self.assertEqual(self.repo.load_json(self.path)["trigger_set_path"], "")
        self.assertEqual(saved[self.service.INTERNAL_LEGACY_TRIGGER_SET]["state"], "none")
        reloaded = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        restored = KeymapService.find_keymap(reloaded, legacy["keymap_id"])
        self.assertEqual([item["key"] for item in restored["triggers"]], ["f1"])

    def test_explicit_empty_trigger_reference_migrates_and_clears_legacy_path_after_save(self):
        from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo

        self.legacy()
        self.write("user/keymaps/a.json", {
            "id": "a", "label": "A", "mappings": {}, "trigger_set_path": "",
        })
        data = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        legacy = data[self.service.INTERNAL_LEGACY_TRIGGER_SET]
        self.assertEqual(legacy["state"], "migrated")
        self.assertTrue(legacy["auto_created"])
        self.assertEqual(data["active_keymap_id"], "a")
        migrated = KeymapService.find_keymap(data, legacy["keymap_id"])
        self.assertEqual(migrated["label"], "旧トリガー一覧（old）")
        self.assertEqual([item["key"] for item in migrated["triggers"]], ["f1"])
        self.assertEqual(data["keymaps"][0]["triggers"], [])
        app = SimpleNamespace(data=data, keymap_service=KeymapService())
        with patch("keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.showinfo") as show:
            KeymapSetIo(app).notify_migrated_legacy_trigger_set()
        show.assert_called_once_with(
            "読込",
            "旧形式のトリガー一覧 user/trigger_sets/old.json を、キーマップ『旧トリガー一覧（old）』に移しました（切替キーは未設定です）",
        )
        saved = self.save(data)
        self.assertEqual(saved[self.service.INTERNAL_LEGACY_TRIGGER_SET]["state"], "none")
        self.assertEqual(self.repo.load_json(self.path)["trigger_set_path"], "")

    def test_trigger_set_save_as_requires_parent_or_explicit_deferral(self):
        data = self.save({"active_keymap_id": "a", "keymaps": [{"id": "a", "triggers": [{"key": "f1", "actions": []}]}]})
        plan = SavePlan((ChildSaveEntry(CHILD_KEYMAP, "a", ACTION_SKIP),
                         ChildSaveEntry(CHILD_TRIGGER_SET, "a", ACTION_SAVE_AS, "user/trigger_sets/alias.json")))
        blocked = self.service.find_dependency_blocked_parents(data, config_root=self.root, keymap_set_path=self.path, save_plan=plan)
        self.assertEqual(blocked, {(CHILD_KEYMAP, "a"): ["a"]})
        before = self.read("user/keymaps/main.json")
        with self.assertRaises(SavePlanError):
            self.save(data, plan)
        self.assertFalse(os.path.exists(os.path.join(self.root, "user", "trigger_sets", "alias.json")))
        self.save(data, SavePlan(plan.entries, allow_deferred_index=True))
        self.assertEqual(self.read("user/keymaps/main.json"), before)
        self.assertEqual(self.read("user/trigger_sets/alias.json")["triggers"][0]["key"], "f1")

    def test_default_stem_and_parent_follow_keymap_path(self):
        data = {"active_keymap_id": "a", "keymaps": [{
            "id": "a", "_keymap_source_path": "user/keymaps/parent.json",
            "triggers": [{"key": "f1", "actions": []}],
        }]}
        saved = self.save(data)
        self.assertEqual(self.read("user/trigger_sets/parent.json")["_parent_refs"], ["user/keymaps/parent.json"])
        self.assertEqual(saved["keymaps"][0][self.service.INTERNAL_TRIGGER_SET_PARENT_REFS], ["user/keymaps/parent.json"])

    def test_sequence_identity_rejects_ambiguous_parts(self):
        self.assertEqual(split_sequence_key(compose_sequence_key("a", "f1")), ("a", "f1"))
        for owner, key in (("a\x1fb", "f1"), ("a", "f1\x1ff2"), ("", "f1")):
            with self.subTest(owner=owner, key=key), self.assertRaises(SavePlanError):
                compose_sequence_key(owner, key)
        with self.assertRaises(SavePlanError):
            split_sequence_key("a\x1ff1\x1ff2")

    def test_migration_marks_config_dirty_after_loading_ui(self):
        from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
        data = self.legacy()
        tracker = DirtyStateTracker(get_data=lambda: data, keymap_service=KeymapService(),
                                    config_service=self.service, on_change=Mock())
        app = SimpleNamespace(data=data, dirty_tracker=tracker, discard_retained_hook_keys=Mock(),
                              _sync_control_vars_from_data=Mock(), _refresh_key_overlap_report=Mock())
        KeymapSetIo(app).apply_loaded_data_to_ui()
        self.assertTrue(tracker.config_dirty)
        self.assertTrue(data["keymaps"][0][self.service.INTERNAL_KEYMAP_DIRTY])
        # 個別 keymap 保存で自身だけ clear しても構成セットの移行は未保存。
        data["keymaps"][0] = self.service.save_keymap_file(
            "user/keymaps/a.json", data["keymaps"][0], config_root=self.root,
        )
        tracker.sync_dirty_state()
        self.assertTrue(tracker.has_unsaved_changes())

    def test_trigger_set_default_collisions_are_resolved_across_instances(self):
        data = {"active_keymap_id": "a", "keymaps": [
            {"id": "a", "_keymap_source_path": "one/same.json", "triggers": [{"key": "f1"}]},
            {"id": "b", "_keymap_source_path": "two/same.json", "triggers": [{"key": "f1"}]},
        ]}
        saved = self.save(data)
        self.assertEqual(saved["keymaps"][0]["_trigger_set_source_path"], "user/trigger_sets/same.json")
        self.assertEqual(saved["keymaps"][1]["_trigger_set_source_path"], "user/trigger_sets/same_2.json")

    def test_migration_keymap_write_failure_preserves_legacy_index(self):
        from unittest.mock import patch
        data = self.legacy()
        before = self.repo.load_json(self.path)
        real_save = self.repo.save_json

        def save(path, payload):
            if path == os.path.join(self.root, "user", "keymaps", "a.json"):
                raise OSError("keymap write failed")
            real_save(path, payload)

        with patch.object(self.repo, "save_json", side_effect=save), self.assertRaises(OSError):
            self.save(data)
        self.assertEqual(self.repo.load_json(self.path), before)
        self.assertEqual(data[self.service.INTERNAL_LEGACY_TRIGGER_SET]["state"], "migrated")

    def test_individual_trigger_set_save_targets_only_active_instance(self):
        from keyseq.presentation.controllers.config_io.trigger_set_file_io import TriggerSetFileIo
        data = {"active_keymap_id": "b", "keymaps": [
            {"id": key, "triggers": [{"key": "f1", "actions": [{"type": "text", "value": key}], "_sequence_dirty": True}]}
            for key in ("a", "b")
        ]}
        dialog = SimpleNamespace(ask_child_save_actions=lambda rows: {(row.kind, row.key): (ACTION_SAVE, "") for row in rows})
        app = SimpleNamespace(data=data, config_service=self.service, config_root=self.root,
                              keymap_set_path=self.path, dirty_tracker=None, child_save_dialog=dialog)
        path = os.path.join(self.root, "individual.json")
        plan = TriggerSetFileIo(app)._collect_sequence_save_plan(path)
        self.assertEqual([(entry.kind, entry.key) for entry in plan.entries], [(CHILD_SEQUENCE, "f1")])
        triggers, payload = self.service.save_trigger_set_file(path, data, config_root=self.root, save_plan=plan)
        self.assertEqual(triggers[0]["actions"][0]["value"], "b")
        self.assertEqual(self.read(payload["triggers"][0]["sequence_path"])["actions"][0]["value"], "b")
        self.assertNotIn("_sequence_source_path", data["keymaps"][0]["triggers"][0])

    def test_save_rejects_separator_before_key_normalization(self):
        for owner, trigger in (("a\x1f", "f1"), ("a", "f1\x1f")):
            with self.subTest(owner=owner, trigger=trigger), self.assertRaises(SavePlanError):
                self.save({"active_keymap_id": owner, "keymaps": [{"id": owner, "triggers": [{"key": trigger}]}]})
        self.assertFalse(os.path.exists(self.path))

    def test_same_legacy_reference_is_cleared_after_save(self):
        self.legacy()
        self.write("user/keymaps/a.json", {"mappings": {}, "trigger_set_path": "user/trigger_sets/old.json"})
        data = self.service.load_runtime_data_from_keymap_set_path(self.path, config_root=self.root)
        self.assertEqual(data[self.service.INTERNAL_LEGACY_TRIGGER_SET]["state"], "same")
        saved = self.save(data)
        self.assertEqual(self.repo.load_json(self.path)["trigger_set_path"], "")
        self.assertEqual(saved[self.service.INTERNAL_LEGACY_TRIGGER_SET]["state"], "none")

    def test_shared_trigger_set_requires_every_skipped_parent(self):
        shared = [{"key": "f1"}]
        data = {"active_keymap_id": "b", "keymaps": [
            {"id": "a", "triggers": shared}, {"id": "b", "triggers": shared},
        ]}
        plan = SavePlan((ChildSaveEntry(CHILD_KEYMAP, "b", ACTION_SKIP),))
        self.assertEqual(self.service.find_dependency_blocked_parents(
            data, config_root=self.root, keymap_set_path=self.path, save_plan=plan,
        ), {(CHILD_KEYMAP, "b"): ["a"]})
        with self.assertRaises(SavePlanError):
            self.save(data, plan)
        self.assertFalse(os.path.exists(self.path))
