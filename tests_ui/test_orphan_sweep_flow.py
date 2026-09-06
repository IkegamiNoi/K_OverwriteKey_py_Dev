from __future__ import annotations

import copy
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.application.config_service.orphan_scan import (
    KIND_KEYMAP, ORPHAN_CANDIDATE, ORPHAN_PROTECTED, OrphanEntry, OrphanScanResult,
)
from keyseq.application.config_service.reference_scan import SOURCE_UNREADABLE
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import orphan_sweep_io as sweep_module
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


if __name__ == "__main__":
    unittest.main()
