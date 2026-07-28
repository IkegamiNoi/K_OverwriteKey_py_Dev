from __future__ import annotations

import os
import tempfile
import tkinter
import unittest
from unittest.mock import patch

from keyseq.application.save_plan import ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP, CHILD_KEYMAP, CHILD_SEQUENCE, CHILD_TRIGGER_SET
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_NEW,
    SHARE_OTHER_PARENT,
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

    def test_clean_children_do_not_open_dialog_or_change_child_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            before = {key: open(value, "rb").read() for key, value in targets.items()}
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions") as ask:
                self.assertTrue(self._save(path))

            ask.assert_not_called()
            self.assertEqual({key: open(value, "rb").read() for key, value in targets.items()}, before)

    def test_dirty_choices_control_overwrite_save_as_and_skip(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            renamed_sequence = os.path.join(root, "renamed", "copy.json")
            old_sequence = open(targets[(CHILD_SEQUENCE, "f1")], "rb").read()
            self.app.data["keymaps"][0]["mappings"] = {"a": "c"}
            self.app.data["triggers"][0]["actions"] = [{"type": "text", "value": "new", "label": ""}]
            self.app.dirty_tracker.mark_keymap_dirty(self.app.data["keymaps"][0])
            self.app.dirty_tracker.mark_trigger_set_dirty()
            self.app.dirty_tracker.mark_sequence_dirty(self.app.data["triggers"][0])
            choices = {
                (CHILD_KEYMAP, "km1"): (ACTION_SAVE, ""),
                (CHILD_TRIGGER_SET, ""): (ACTION_SAVE, ""),
                (CHILD_SEQUENCE, "f1"): (ACTION_SAVE_AS, renamed_sequence),
            }
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", return_value=choices) as ask:
                self.assertTrue(self._save(path))

            ask.assert_called_once()
            self.assertTrue(os.path.exists(renamed_sequence))
            self.assertEqual(open(targets[(CHILD_SEQUENCE, "f1")], "rb").read(), old_sequence)

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
