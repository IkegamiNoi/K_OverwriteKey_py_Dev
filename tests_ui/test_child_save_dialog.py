from __future__ import annotations

import os
import tempfile
import tkinter
import unittest
from unittest.mock import patch

from keyseq.application.save_plan import ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP, CHILD_KEYMAP, CHILD_SEQUENCE, CHILD_TRIGGER_SET
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import child_save_dialog as child_save_dialog_module
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_NEW,
    SHARE_OTHER_PARENT,
    SHARE_SHARED,
    SHARE_SOLE,
    SHARE_UNKNOWN,
    ChildSaveRow,
)


def make_data(*, second_sequence: bool = False):
    triggers = [{"key": "f1", "label": "Copy", "actions": [{"type": "text", "value": "old", "label": ""}]}]
    if second_sequence:
        triggers.append({"key": "f2", "label": "Other", "actions": []})
    return {
        "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}}],
        "triggers": triggers,
        "active_keymap_id": "km1",
    }


class _FakeDialogWidget:
    def grid(self, **_kwargs):
        return self

    def pack(self, **_kwargs):
        return self


class _FakeStringVar:
    def __init__(self, *, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _FakeSaveDialog:
    def __init__(self, on_wait):
        self._on_wait = on_wait
        self.buttons = {}
        self.protocols = {}
        self.destroyed = False

    def title(self, _value):
        pass

    def resizable(self, _width, _height):
        pass

    def transient(self, _master):
        pass

    def grab_set(self):
        pass

    def protocol(self, name, command):
        self.protocols[name] = command

    def destroy(self):
        self.destroyed = True

    def wait_window(self):
        self._on_wait(self)


class ChildSaveDialogFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_startup_patch = patch.object(app_module.ConfigService, "load_startup", return_value={})
        cls._makedirs_patch = patch.object(app_module.os, "makedirs")
        cls._load_startup_patch.start()
        cls._makedirs_patch.start()
        try:
            cls.app = app_module.App()
            cls.app.update_idletasks()
        finally:
            cls._makedirs_patch.stop()
            cls._load_startup_patch.stop()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def _prepare(self, root, *, second_sequence: bool = False):
        path = os.path.join(root, "user", "keymap_sets", "main.json")
        self.app.config_root = root
        self.app.data, self.app._startup_settings = self.app.config_service.save_runtime_data(
            path, make_data(second_sequence=second_sequence), config_root=root, startup_data={}
        )
        self.app.keymap_set_path = path
        self.app.dirty_tracker.sync_trigger_set_source_path_from_data()
        self.app.dirty_tracker.clear_individual_dirty_flags()
        self.app.dirty_tracker.set_dirty(False)
        return path

    def _save(self, path):
        with patch.object(self.app.paths, "normalize_keymap_set_save_path", side_effect=lambda value: value), patch.object(
            self.app.keymap_set_io, "choose_split_base_dir_for_keymap_set", return_value=""
        ), patch.object(tkinter.messagebox, "showinfo"):
            return self.app.keymap_set_io.save_keymap_set_to(
                path, flash_message="保存しました。", show_success_dialog=False
            )

    def _targets(self, path):
        return self.app.config_service.resolve_child_save_targets(
            self.app.data, config_root=self.app.config_root, keymap_set_path=path
        )

    def _replace_parent_refs(self, path, refs):
        payload = self.app.config_service.repository.load_json(path)
        payload["_parent_refs"] = refs
        self.app.config_service.repository.save_json(path, payload)

    def _ask_dialog_internally(self, rows, on_wait, *, save_as_path=""):
        variables = []
        dialog = _FakeSaveDialog(lambda current: on_wait(current, variables))

        def make_string_var(*, value):
            variable = _FakeStringVar(value=value)
            variables.append(variable)
            return variable

        def make_button(_master, *, text, command, **_kwargs):
            dialog.buttons[text] = command
            return _FakeDialogWidget()

        with patch.object(child_save_dialog_module.tk, "Toplevel", return_value=dialog), patch.object(
            child_save_dialog_module.tk,
            "StringVar",
            side_effect=make_string_var,
        ), patch.object(child_save_dialog_module.ttk, "Frame", return_value=_FakeDialogWidget()), patch.object(
            child_save_dialog_module.ttk,
            "Label",
            return_value=_FakeDialogWidget(),
        ), patch.object(
            child_save_dialog_module.ttk,
            "Radiobutton",
            return_value=_FakeDialogWidget(),
        ), patch.object(
            child_save_dialog_module.ttk,
            "Button",
            side_effect=make_button,
        ), patch.object(
            self.app.child_save_dialog,
            "_ask_save_as_path",
            return_value=save_as_path,
        ), patch.object(self.app.hook, "suspend_hook_for_dialog") as suspend, patch.object(
            self.app.hook,
            "resume_hook_after_dialog",
        ) as resume:
            result = self.app.child_save_dialog.ask_child_save_actions(rows)

        self.assertEqual(suspend.call_count, resume.call_count)
        return result, variables, dialog

    def test_dialog_internal_rows_use_default_actions(self):
        rows = [
            ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE),
            ChildSaveRow(CHILD_SEQUENCE, "f1", "Copy", "C:/copy.json", SHARE_UNKNOWN, "不明", ACTION_SAVE_AS),
        ]
        result, variables, _dialog = self._ask_dialog_internally(
            rows,
            lambda dialog, _variables: dialog.buttons["キャンセル"](),
        )

        self.assertIsNone(result)
        self.assertEqual([variable.get() for variable in variables], [ACTION_SAVE, ACTION_SAVE_AS])

    def test_dialog_internal_ok_returns_selected_actions(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE)]

        def confirm(dialog, variables):
            variables[0].set(ACTION_SKIP)
            dialog.buttons["OK"]()

        result, variables, dialog = self._ask_dialog_internally(rows, confirm)

        self.assertEqual(result, {(CHILD_KEYMAP, "km1"): (ACTION_SKIP, "")})
        self.assertTrue(dialog.destroyed)

    def test_dialog_internal_save_as_cancel_returns_none(self):
        rows = [
            ChildSaveRow(CHILD_SEQUENCE, "f1", "Copy", "C:/copy.json", SHARE_UNKNOWN, "不明", ACTION_SAVE_AS)
        ]
        result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda dialog, _variables: dialog.buttons["OK"](),
        )

        self.assertIsNone(result)
        self.assertFalse(dialog.destroyed)

    def test_dialog_internal_cancel_and_window_close_return_none(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE)]
        for close in (
            lambda dialog, _variables: dialog.buttons["キャンセル"](),
            lambda dialog, _variables: dialog.protocols["WM_DELETE_WINDOW"](),
        ):
            with self.subTest(close=close):
                result, _variables, dialog = self._ask_dialog_internally(rows, close)
                self.assertIsNone(result)
                self.assertTrue(dialog.destroyed)

    def test_clean_children_do_not_open_dialog_or_change_child_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            before = {key: open(value, "rb").read() for key, value in targets.items()}
            parent_before = open(path, "rb").read()
            self.app.data["hook_stop_key"] = "f11"
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions") as ask:
                self.assertTrue(self._save(path))

            ask.assert_not_called()
            self.assertEqual({key: open(value, "rb").read() for key, value in targets.items()}, before)
            self.assertNotEqual(open(path, "rb").read(), parent_before)

    def test_dirty_choices_control_overwrite_save_as_and_skip(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root, second_sequence=True)
            targets = self._targets(path)
            renamed_sequence = os.path.join(root, "renamed", "copy.json")
            old_sequence = open(targets[(CHILD_SEQUENCE, "f1")], "rb").read()
            old_skipped_sequence = open(targets[(CHILD_SEQUENCE, "f2")], "rb").read()
            self.app.data["keymaps"][0]["mappings"] = {"a": "c"}
            self.app.data["triggers"][0]["actions"] = [{"type": "text", "value": "new", "label": ""}]
            self.app.dirty_tracker.mark_keymap_dirty(self.app.data["keymaps"][0])
            self.app.dirty_tracker.mark_trigger_set_dirty()
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][0])
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][1])
            choices = {
                (CHILD_KEYMAP, "km1"): (ACTION_SAVE, ""),
                (CHILD_TRIGGER_SET, ""): (ACTION_SAVE, ""),
                (CHILD_SEQUENCE, "f1"): (ACTION_SAVE_AS, renamed_sequence),
                (CHILD_SEQUENCE, "f2"): (ACTION_SKIP, ""),
            }
            def choose(rows):
                self.assertEqual(
                    [(row.kind, row.key) for row in rows],
                    [
                        (CHILD_KEYMAP, "km1"),
                        (CHILD_TRIGGER_SET, ""),
                        (CHILD_SEQUENCE, "f1"),
                        (CHILD_SEQUENCE, "f2"),
                    ],
                )
                return choices

            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose) as ask:
                self.assertTrue(self._save(path))

            ask.assert_called_once()
            self.assertTrue(os.path.exists(renamed_sequence))
            self.assertEqual(open(targets[(CHILD_SEQUENCE, "f1")], "rb").read(), old_sequence)
            self.assertEqual(open(targets[(CHILD_SEQUENCE, "f2")], "rb").read(), old_skipped_sequence)

    def test_other_parent_child_reaches_dialog_with_save_as_default(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            keymap_path = self._targets(path)[(CHILD_KEYMAP, "km1")]
            self._replace_parent_refs(keymap_path, ["user/keymap_sets/other.json"])
            self.app.data["keymaps"][0]["mappings"] = {"a": "c"}
            self.app.dirty_tracker.mark_keymap_dirty(self.app.data["keymaps"][0])

            def choose(rows):
                row = rows[0]
                self.assertEqual(row.share_state, SHARE_OTHER_PARENT)
                self.assertEqual(row.default_action, ACTION_SAVE_AS)
                self.assertEqual(row.share_text, "別の構成に属します")
                return {(CHILD_KEYMAP, "km1"): (ACTION_SKIP, "")}

            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose) as ask:
                self.assertTrue(self._save(path))

            ask.assert_called_once()

    def test_shared_child_reaches_dialog_with_warning_and_can_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            keymap_path = self._targets(path)[(CHILD_KEYMAP, "km1")]
            self._replace_parent_refs(
                keymap_path,
                ["user/keymap_sets/main.json", "user/keymap_sets/other.json"],
            )
            self.app.data["keymaps"][0]["mappings"] = {"a": "c"}
            self.app.dirty_tracker.mark_keymap_dirty(self.app.data["keymaps"][0])

            def choose(rows):
                row = rows[0]
                self.assertEqual(row.share_state, SHARE_SHARED)
                self.assertEqual(row.default_action, ACTION_SAVE)
                self.assertEqual(row.share_text, "2 個の上位で共有中・全てに影響します")
                return {(CHILD_KEYMAP, "km1"): (ACTION_SAVE, "")}

            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose) as ask:
                self.assertTrue(self._save(path))

            ask.assert_called_once()
            self.assertEqual(
                self.app.config_service.repository.load_json(keymap_path)["mappings"],
                {"a": "c"},
            )

    def test_cancel_writes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            before = {path: open(path, "rb").read(), **{value: open(value, "rb").read() for value in targets.values()}}
            self.app.dirty_tracker.mark_keymap_dirty(self.app.data["keymaps"][0])
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", return_value=None):
                self.assertFalse(self._save(path))

            self.assertEqual({name: open(name, "rb").read() for name in before}, before)

    def test_dependency_confirmation_can_save_trigger_set(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            renamed_sequence = os.path.join(root, "renamed", "copy.json")
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][0])
            choices = {(CHILD_SEQUENCE, "f1"): (ACTION_SAVE_AS, renamed_sequence)}
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", return_value=choices), patch.object(
                self.app.child_save_dialog, "confirm_trigger_set_dependency", return_value=ACTION_SAVE
            ) as confirm:
                self.assertTrue(self._save(path))

            confirm.assert_called_once()
            self.assertTrue(os.path.exists(renamed_sequence))

    def test_dependency_save_as_keeps_confirmed_trigger_set_target(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            old_trigger_bytes = open(targets[(CHILD_TRIGGER_SET, "")], "rb").read()
            renamed_sequence = os.path.join(root, "renamed", "copy.json")
            renamed_trigger_set = os.path.join(root, "renamed", "trigger_set.json")
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][0])
            choices = {(CHILD_SEQUENCE, "f1"): (ACTION_SAVE_AS, renamed_sequence)}

            def confirm(**_kwargs):
                self.app.child_save_dialog.trigger_set_save_as_path = renamed_trigger_set
                return ACTION_SAVE_AS

            with patch.object(
                self.app.child_save_dialog,
                "ask_child_save_actions",
                side_effect=[choices, choices],
            ) as ask, patch.object(
                self.app.child_save_dialog,
                "confirm_trigger_set_dependency",
                side_effect=confirm,
            ) as dependency:
                self.assertTrue(self._save(path))

            self.assertEqual(ask.call_count, 2)
            dependency.assert_called_once()
            self.assertEqual(open(targets[(CHILD_TRIGGER_SET, "")], "rb").read(), old_trigger_bytes)
            self.assertTrue(os.path.exists(renamed_trigger_set))

    def test_dependency_reselect_then_cancel_keeps_all_files_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            before = {path: open(path, "rb").read(), **{value: open(value, "rb").read() for value in targets.values()}}
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][0])
            choices = {(CHILD_SEQUENCE, "f1"): (ACTION_SAVE_AS, os.path.join(root, "renamed.json"))}
            with patch.object(
                self.app.child_save_dialog, "ask_child_save_actions", side_effect=[choices, None]
            ) as ask, patch.object(
                self.app.child_save_dialog, "confirm_trigger_set_dependency", return_value=""
            ) as confirm:
                self.assertFalse(self._save(path))

            self.assertEqual(ask.call_count, 2)
            confirm.assert_called_once()
            self.assertEqual({name: open(name, "rb").read() for name in before}, before)

    def test_dependency_reselect_with_no_dirty_rows_cancels_save(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            trigger = self.app.data["triggers"][0]
            trigger["label"] = "Renamed"
            trigger.pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions") as ask, patch.object(
                self.app.child_save_dialog,
                "confirm_trigger_set_dependency",
                return_value="",
            ) as confirm:
                self.assertIsNone(self.app.keymap_set_io._collect_child_save_plan(path, ""))

            ask.assert_not_called()
            confirm.assert_called_once()

    def test_skipped_sequence_does_not_require_dependency_confirmation(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][0])
            choices = {(CHILD_SEQUENCE, "f1"): (ACTION_SKIP, "")}
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", return_value=choices), patch.object(
                self.app.child_save_dialog, "confirm_trigger_set_dependency"
            ) as confirm:
                self.assertTrue(self._save(path))

            confirm.assert_not_called()

    def test_skipped_child_remains_dirty_after_parent_save(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            keymap_path = self._targets(path)[(CHILD_KEYMAP, "km1")]
            before = open(keymap_path, "rb").read()
            self.app.data["keymaps"][0]["mappings"] = {"a": "c"}
            self.app.dirty_tracker.mark_keymap_dirty(self.app.data["keymaps"][0])
            choices = {(CHILD_KEYMAP, "km1"): (ACTION_SKIP, "")}
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", return_value=choices):
                self.assertTrue(self._save(path))

            self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())
            self.assertEqual(open(keymap_path, "rb").read(), before)

    def test_trigger_set_save_as_recalculates_sequence_targets_before_saving(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root, second_sequence=True)
            external_trigger_set = os.path.join(root, "external", "trigger_set.json")
            external_other = os.path.join(root, "external", "sequences", "other.json")
            os.makedirs(os.path.dirname(external_other), exist_ok=True)
            with open(external_other, "wb") as stream:
                stream.write(b"existing other")
            self.app.data["triggers"][0].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            self.app.data["triggers"][1].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            self.app.dirty_tracker.mark_trigger_set_dirty()
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][0])
            seen_sequence_targets = []

            def choose(rows):
                sequence_row = next(row for row in rows if row.kind == CHILD_SEQUENCE)
                seen_sequence_targets.append(sequence_row.target_path)
                trigger_action = ACTION_SAVE_AS
                trigger_target = external_trigger_set
                return {
                    (CHILD_TRIGGER_SET, ""): (trigger_action, trigger_target),
                    (CHILD_SEQUENCE, "f1"): (ACTION_SAVE, ""),
                }

            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose) as ask:
                self.assertTrue(self._save(path))

            self.assertEqual(ask.call_count, 2)
            self.assertNotEqual(seen_sequence_targets[0], seen_sequence_targets[1])
            self.assertEqual(open(external_other, "rb").read(), b"existing other")

    def test_dependency_dialog_uses_safe_default_for_unknown_owners(self):
        for share_state, expected_default in ((SHARE_UNKNOWN, tkinter.messagebox.NO), (SHARE_OTHER_PARENT, tkinter.messagebox.NO), (SHARE_SOLE, tkinter.messagebox.YES), (SHARE_NEW, tkinter.messagebox.YES)):
            with self.subTest(share_state=share_state):
                row = ChildSaveRow(CHILD_TRIGGER_SET, "", "トリガー一覧", "C:/trigger.json", share_state, "共有状況", ACTION_SAVE)
                with patch.object(self.app.hook, "suspend_hook_for_dialog"), patch.object(
                    self.app.hook, "resume_hook_after_dialog"
                ), patch.object(tkinter.messagebox, "askyesnocancel", return_value=None) as ask:
                    self.assertEqual(
                        self.app.child_save_dialog.confirm_trigger_set_dependency(
                            blocked_labels=["Copy"], trigger_set_row=row
                        ),
                        "",
                    )

                self.assertEqual(ask.call_args.kwargs["default"], expected_default)


if __name__ == "__main__":
    unittest.main()
