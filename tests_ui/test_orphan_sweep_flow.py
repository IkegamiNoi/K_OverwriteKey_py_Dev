from __future__ import annotations

import copy
import json
import os
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from keyseq.application.config_service.orphan_scan import (
    KIND_KEYMAP, ORPHAN_CANDIDATE, ORPHAN_PROTECTED, OrphanEntry, OrphanScanResult,
)
from keyseq.application.config_service.reference_scan import SOURCE_UNREADABLE
from keyseq.application.save_plan import SavePlan
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import orphan_sweep_io as sweep_module
from keyseq.presentation.dialogs import orphan_sweep_dialog
from keyseq.presentation.orphan_sweep_text import format_orphan_notice, format_orphan_plan
from keyseq.presentation.views.menu_bar import build_menu_bar


class OrphanSweepFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self._patch(self.app, "keymap_set_path", "saved.json")
        self._patch(self.app, "_startup_settings", {"keymap_set_path": " startup.json "})
        self.dirty = self._patch(self.app.dirty_tracker, "has_unsaved_changes", return_value=False)
        self.ask = self._patch(sweep_module.messagebox, "askyesno", return_value=False)
        self.info = self._patch(sweep_module.messagebox, "showinfo")
        self.save = self._patch(self.app.keymap_set_io, "save_keymap_set", return_value=True)
        self.save_as = self._patch(self.app.keymap_set_io, "save_as", return_value=True)
        self._patch(self.app.keymap_set_io, "confirm_save_if_dirty",
                    side_effect=AssertionError("逆の確認フローを呼んではならない"))
        self._patch(sweep_module.messagebox, "askyesnocancel",
                    side_effect=AssertionError("保存する / 中止する以外の選択肢"))
        self.dialog = Mock(result=True)
        self.dialog_dirs = None
        self.open_dialog = self._patch(sweep_module, "OrphanSweepDialog",
                                       side_effect=self._open_dialog)

    def _open_dialog(self, parent, *, scan_dirs, initial_dir):
        self.dialog.scan_dirs = scan_dirs if self.dialog_dirs is None else self.dialog_dirs
        return self.dialog

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    @staticmethod
    def _result(state=None, *, unreadable=False):
        entries = () if state is None else (OrphanEntry(KIND_KEYMAP, "user/keymaps/child.json", state),)
        sources = (("broken.json", SOURCE_UNREADABLE),) if unreadable else ()
        return OrphanScanResult(entries, sources, (), ())

    def test_unsaved_no_stops_before_save_collection_and_scan(self):
        self.dirty.return_value = True
        with patch.object(self.app.config_service, "collect_protected_paths") as collect, patch.object(
            self.app.config_service, "scan_orphans",
        ) as scan:
            self.app.orphan_sweep_io.run_sweep()
        self.ask.assert_called_once_with("孤児ファイルの棚卸し", "棚卸しの前に保存が必要です。保存しますか？")
        self.save.assert_not_called()
        self.save_as.assert_not_called()
        collect.assert_not_called()
        scan.assert_not_called()
        self.info.assert_not_called()

    def test_unsaved_yes_saves_existing_set_before_collection_and_scan(self):
        self.dirty.return_value = self.ask.return_value = True
        events = []
        self.save.side_effect = lambda **kwargs: events.append("save") or True
        with patch.object(self.app.config_service, "collect_protected_paths",
                          side_effect=lambda *args, **kwargs: events.append("collect") or ()):
            with patch.object(self.app.config_service, "scan_orphans",
                              side_effect=lambda **kwargs: events.append("scan") or self._result()):
                self.app.orphan_sweep_io.run_sweep()
        self.assertEqual(events, ["save", "collect", "scan"])
        self.save.assert_called_once_with(show_success_dialog=False)
        self.save_as.assert_not_called()

    def test_save_as_success_uses_updated_runtime_and_path(self):
        self.app.keymap_set_path = ""
        self.dirty.return_value = self.ask.return_value = True
        self._patch(self.app, "data", {})

        def save_as(**kwargs):
            self.app.keymap_set_path = "newly-saved.json"
            self.app.data = {"hotkey_presets_path": "new-presets.json"}
            return True

        self.save_as.side_effect = save_as
        with patch.object(self.app.config_service, "collect_protected_paths", return_value=()) as collect:
            with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
                self.app.orphan_sweep_io.run_sweep()
        self.save_as.assert_called_once_with(show_success_dialog=False)
        self.save.assert_not_called()
        collect.assert_called_once_with({"hotkey_presets_path": "new-presets.json"},
                                        keymap_set_path="newly-saved.json")
        self.assertEqual(scan.call_args.kwargs["current_keymap_set_path"], "newly-saved.json")

    def test_save_failure_or_save_as_cancel_stops_collection_and_scan(self):
        self.dirty.return_value = self.ask.return_value = True
        self.save.return_value = self.save_as.return_value = False
        for source in ("saved.json", ""):
            with self.subTest(source=source):
                self.app.keymap_set_path = source
                with patch.object(self.app.config_service, "collect_protected_paths") as collect:
                    with patch.object(self.app.config_service, "scan_orphans") as scan:
                        self.app.orphan_sweep_io.run_sweep()
                collect.assert_not_called()
                scan.assert_not_called()
        self.save.assert_called_once_with(show_success_dialog=False)
        self.save_as.assert_called_once_with(show_success_dialog=False)
        self.info.assert_not_called()

    def test_clean_runtime_scans_without_save_confirmation(self):
        with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
            self.app.orphan_sweep_io.run_sweep()
        scan.assert_called_once()
        self.ask.assert_not_called()
        self.save.assert_not_called()
        self.save_as.assert_not_called()

    def test_zero_candidates_only_notifies_without_opening_dialog(self):
        for state in (None, ORPHAN_PROTECTED):
            with self.subTest(state=state):
                result = self._result(state, unreadable=True)
                self.info.reset_mock()
                with patch.object(self.app.config_service, "scan_orphans", return_value=result):
                    with patch.object(tk.Toplevel, "__init__", side_effect=AssertionError("unexpected dialog")):
                        self.app.orphan_sweep_io.run_sweep()
                self.info.assert_called_once_with("孤児ファイルの棚卸し", "\n".join(format_orphan_notice(result)))
        self.ask.assert_not_called()

    def test_candidates_are_presented_with_warning_first(self):
        result = self._result(ORPHAN_CANDIDATE, unreadable=True)
        with patch.object(self.app.config_service, "scan_orphans", return_value=result):
            self.app.orphan_sweep_io.run_sweep()
        self.info.assert_called_once_with("孤児ファイルの棚卸し", "\n".join(format_orphan_plan(result)))
        self.assertTrue(self.info.call_args.args[1].startswith("警告:"))
        self.ask.assert_not_called()

    def test_scan_arguments_use_config_root_startup_current_and_protected_paths(self):
        protected = ("saved.json", "user/keymaps/runtime.json")
        with patch.object(self.app.config_service, "collect_protected_paths", return_value=protected) as collect:
            with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
                self.app.orphan_sweep_io.run_sweep()
        collect.assert_called_once_with(self.app.data, keymap_set_path=self.app.keymap_set_path)
        self.assertTrue(self.app.config_root)
        scan.assert_called_once_with(config_root=self.app.config_root, scan_dirs=[],
                                     startup_keymap_set_path="startup.json",
                                     current_keymap_set_path=self.app.keymap_set_path,
                                     protected_paths=protected)

    def _invoke_settings_command(self, label):
        menubar = self.app.menubar
        for top_index in range(menubar.index("end") + 1):
            if menubar.type(top_index) != "cascade" or menubar.entrycget(top_index, "label") != "設定":
                continue
            submenu = self.app.nametowidget(menubar.entrycget(top_index, "menu"))
            for index in range(submenu.index("end") + 1):
                if submenu.type(index) == "command" and submenu.entrycget(index, "label") == label:
                    submenu.invoke(index)
                    return True
        return False

    def test_settings_menu_runs_sweep(self):
        self.addCleanup(build_menu_bar, self.app)
        with patch.object(self.app.orphan_sweep_io, "run_sweep") as run:
            build_menu_bar(self.app)
            invoked = self._invoke_settings_command("孤児ファイルの棚卸し…")
        self.assertTrue(invoked, "孤児ファイルの棚卸し… メニューが見つかりません")
        run.assert_called_once()

    @staticmethod
    def _snapshot(root):
        return {
            path.relative_to(root).as_posix(): (
                None if path.is_dir() else (path.read_bytes(), path.stat().st_mtime_ns)
            )
            for path in root.rglob("*")
        }

    def test_real_sweep_does_not_write_files_or_change_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / "user" / "keymaps" / "unused.json"
            child.parent.mkdir(parents=True)
            child.write_bytes(b'{"mappings": {}}')
            before = self._snapshot(root)
            with patch.object(self.app, "config_root", str(root)), patch.object(
                self.app, "keymap_set_path", "",
            ), patch.object(self.app, "_startup_settings", {}), patch.object(self.app, "data", {}):
                runtime = copy.deepcopy(self.app.data)
                self.app.orphan_sweep_io.run_sweep()
                self.assertEqual(self.app.data, runtime)
            self.assertEqual(self._snapshot(root), before)
        self.assertIn("キーマップ: user/keymaps/unused.json", self.info.call_args.args[1])
        self.save.assert_not_called()
        self.save_as.assert_not_called()
        self.ask.assert_not_called()


    def test_stored_scan_dirs_are_normalized_for_dialog_and_scan(self):
        root = Path(self.app.config_root)
        self.app._startup_settings[sweep_module.SCAN_DIRS_KEY] = [
            " extra ", str(root / "extra"), "other",
        ]
        with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
            self.app.orphan_sweep_io.run_sweep()
        self.open_dialog.assert_called_once_with(
            self.app, scan_dirs=("extra", "other"), initial_dir=self.app.config_root,
        )
        self.dialog.wait_window.assert_called_once_with()
        self.assertEqual(scan.call_args.kwargs["scan_dirs"], ["extra", "other"])

    def test_broken_scan_dir_settings_do_not_stop_scan(self):
        for value, expected in ((None, []), ("extra", []), ({}, []),
                                ([None, 1, {}, [], "extra", " "], ["extra"])):
            with self.subTest(value=value):
                self.app._startup_settings[sweep_module.SCAN_DIRS_KEY] = value
                with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
                    self.app.orphan_sweep_io.run_sweep()
                self.assertEqual(scan.call_args.kwargs["scan_dirs"], expected)

    def test_dialog_run_scans_and_close_does_not_scan(self):
        for result in (True, False):
            with self.subTest(result=result):
                self.dialog.result = result
                with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
                    self.app.orphan_sweep_io.run_sweep()
                self.assertEqual(scan.call_count, int(result))

    def test_changed_settings_are_saved_even_when_dialog_is_closed(self):
        self.dialog_dirs = (" extra ", str(Path(self.app.config_root) / "extra"), "other")
        for result in (True, False):
            with self.subTest(result=result):
                self.dialog.result = result
                with patch.object(self.app.startup_io, "write_startup", return_value=True) as write:
                    with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
                        self.app.orphan_sweep_io.run_sweep()
                write.assert_called_once_with({sweep_module.SCAN_DIRS_KEY: ["extra", "other"]})
                self.assertEqual(scan.call_count, int(result))

    def test_unchanged_normalized_settings_are_not_written(self):
        self.app._startup_settings[sweep_module.SCAN_DIRS_KEY] = ["extra"]
        self.dialog_dirs = (str(Path(self.app.config_root) / "extra"), "extra")
        with patch.object(self.app.startup_io, "write_startup") as write:
            with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()):
                self.app.orphan_sweep_io.run_sweep()
        write.assert_not_called()

    def test_failed_settings_write_does_not_stop_scan(self):
        self.dialog_dirs = ("extra",)
        with patch.object(self.app.startup_io, "write_startup", return_value=False) as write:
            with patch.object(self.app.config_service, "scan_orphans", return_value=self._result()) as scan:
                self.app.orphan_sweep_io.run_sweep()
        write.assert_called_once_with({sweep_module.SCAN_DIRS_KEY: ["extra"]})
        self.assertEqual(scan.call_args.kwargs["scan_dirs"], ["extra"])

    def test_settings_save_only_uses_startup_io(self):
        self.dialog.result = False
        self.dialog_dirs = ("extra",)
        with patch.object(self.app.startup_io, "write_startup", return_value=True) as write:
            with patch.object(self.app.config_service, "save_startup") as save_startup:
                self.app.orphan_sweep_io.run_sweep()
        write.assert_called_once_with({sweep_module.SCAN_DIRS_KEY: ["extra"]})
        save_startup.assert_not_called()
        with patch.object(self.app.config_service, "save_startup") as save_startup:
            self.assertTrue(self.app.startup_io.write_startup({sweep_module.SCAN_DIRS_KEY: ["extra"]}))
        save_startup.assert_called_once()
        self.assertEqual(save_startup.call_args.args[1][sweep_module.SCAN_DIRS_KEY], ["extra"])

    def _prepare_real_keymap_save(self, root):
        path = str(root / "user" / "keymap_sets" / "saved.json")
        self._patch(self.app, "config_root", str(root))
        self._patch(self.app, "startup_path", str(root / "config.json"))
        self._patch(self.app, "data", self.app.config_service.new_default_data())
        self._patch(self.app.paths, "preferred_startup_path", return_value=str(root / "config.json"))
        self._patch(self.app.paths, "normalize_keymap_set_save_path", return_value=path)
        self._patch(self.app.keymap_set_io, "choose_split_base_dir_for_keymap_set", return_value="")
        self._patch(self.app.keymap_set_io, "_collect_child_save_plan", return_value=(SavePlan(), "", False))
        self._patch(self.app.keymap_set_io, "_clear_saved_child_dirty_flags")
        self._patch(self.app.dirty_tracker, "sync_trigger_set_source_path_from_data")
        self._patch(self.app.dirty_tracker, "set_dirty")
        self._patch(self.app.dirty_tracker, "sync_dirty_state")
        self._patch(self.app, "_set_flash_message")
        return path

    def test_scan_dirs_and_existing_settings_survive_real_keymap_set_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._prepare_real_keymap_save(root)
            self.app._startup_settings = {"ui_font_delta_pt": 2, "custom_setting": {"keep": True}}
            self.dialog.result = False
            self.dialog_dirs = ("extra",)
            self.app.orphan_sweep_io.run_sweep()
            startup_path = root / "config.json"
            before = json.loads(startup_path.read_text(encoding="utf-8"))
            self.assertEqual(before[sweep_module.SCAN_DIRS_KEY], ["extra"])
            self.assertTrue(self.app.keymap_set_io.save_keymap_set_to(
                path, flash_message="保存しました。", show_success_dialog=False,
            ))
            self.assertTrue(Path(path).is_file())
            after = json.loads(startup_path.read_text(encoding="utf-8"))
            for key in (sweep_module.SCAN_DIRS_KEY, "ui_font_delta_pt", "custom_setting"):
                self.assertEqual(after[key], before[key])

    def test_missing_scan_dirs_are_retained_and_reported_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = {sweep_module.SCAN_DIRS_KEY: ["missing"]}
            self._patch(self.app, "config_root", directory)
            self._patch(self.app, "keymap_set_path", "")
            self._patch(self.app, "_startup_settings", settings)
            self._patch(self.app, "data", {})
            before = self._snapshot(root)
            with patch.object(self.app.startup_io, "write_startup") as write:
                with patch.object(self.app.config_service, "scan_orphans",
                                  wraps=self.app.config_service.scan_orphans) as scan:
                    self.app.orphan_sweep_io.run_sweep()
            self.assertEqual(self.app._startup_settings, settings)
            write.assert_not_called()
            self.assertEqual(self._snapshot(root), before)
            result = self.app.config_service.scan_orphans(**scan.call_args.kwargs)
            self.assertEqual(result.missing_scan_dirs,
                             (os.path.join(directory, "user", "keymap_sets"), "missing"))
        message = self.info.call_args.args[1]
        self.assertIn("見つからなかった走査ディレクトリ: 2 件", message)
        for path in result.missing_scan_dirs:
            self.assertIn(f"  {path}", message)
        self.assertNotIn("警告", message)


class OrphanSweepDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def _dialog(self, scan_dirs=("one", "two")):
        dialog = orphan_sweep_dialog.OrphanSweepDialog(
            self.app, scan_dirs=scan_dirs, initial_dir=self.app.config_root,
        )
        self.addCleanup(lambda: dialog.destroy() if dialog.winfo_exists() else None)
        return dialog

    def test_initial_list_and_scan_dirs_match_input(self):
        dialog = self._dialog()
        self.assertEqual(dialog.listbox.get(0, tk.END), ("one", "two"))
        self.assertEqual(dialog.scan_dirs, ("one", "two"))
        self.assertFalse(dialog.result)
        dialog.destroy()
        self.assertEqual(dialog.scan_dirs, ("one", "two"))

    def test_add_directory_cancel_and_duplicate(self):
        dialog = self._dialog()
        with patch.object(orphan_sweep_dialog.filedialog, "askdirectory",
                          side_effect=["three", "", "three"]) as ask:
            for _ in range(3):
                dialog._add()
        self.assertEqual(dialog.listbox.get(0, tk.END), ("one", "two", "three"))
        self.assertEqual(ask.call_count, 3)
        ask.assert_called_with(parent=dialog, initialdir=self.app.config_root)
        dialog.destroy()
        self.assertEqual(dialog.scan_dirs, ("one", "two", "three"))

    def test_remove_selection_without_confirmation_and_ignore_no_selection(self):
        dialog = self._dialog()
        with patch.object(sweep_module.messagebox, "askyesno") as ask:
            dialog.listbox.selection_clear(0, tk.END)
            dialog._remove()
            self.assertEqual(dialog.listbox.get(0, tk.END), ("one", "two"))
            dialog.listbox.selection_set(0)
            dialog._remove()
        ask.assert_not_called()
        self.assertEqual(dialog.listbox.get(0, tk.END), ("two",))
        dialog.destroy()
        self.assertEqual(dialog.scan_dirs, ("two",))

    def test_run_empty_list_sets_result_and_resumes_hook(self):
        with patch.object(self.app.hook, "suspend_hook_for_dialog") as suspend:
            with patch.object(self.app.hook, "resume_hook_after_dialog") as resume:
                dialog = self._dialog(())
                self.assertFalse(dialog.result)
                dialog._run()
        self.assertTrue(dialog.result)
        self.assertEqual(dialog.scan_dirs, ())
        suspend.assert_called_once_with()
        resume.assert_called_once_with()

    def test_escape_and_window_close_keep_result_false(self):
        for close in ("escape", "window"):
            with self.subTest(close=close):
                dialog = self._dialog()
                if close == "escape":
                    self.assertTrue(dialog.bind("<Escape>"))
                    dialog.deiconify()
                    dialog.update_idletasks()
                    dialog.focus_force()
                    dialog.event_generate("<Escape>")
                else:
                    dialog.tk.call(dialog.protocol("WM_DELETE_WINDOW"))
                self.assertFalse(dialog.winfo_exists())
                self.assertFalse(dialog.result)
                self.assertEqual(dialog.scan_dirs, ("one", "two"))


if __name__ == "__main__":
    unittest.main()
