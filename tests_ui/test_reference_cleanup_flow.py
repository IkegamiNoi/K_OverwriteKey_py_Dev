from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.config_service.parent_refs_cleanup import (
    CLEANUP_PROTECTED,
    CLEANUP_TARGET,
    ParentRefsCleanupInspection,
    ParentRefsPruneResult,
)
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import keymap_set_io as keymap_set_io_module
from keyseq.presentation.controllers.config_io import reference_cleanup_io as reference_cleanup_io_module
from keyseq.presentation.reference_cleanup_text import CLEANUP_EMPTY_MESSAGE, format_cleanup_plan
from keyseq.presentation.views.menu_bar import build_menu_bar


def _unexpected_showerror(_title, message, *_args, **_kwargs):
    raise AssertionError(f"unexpected messagebox.showerror: {message}")


def _unexpected_filedialog(*_args, **_kwargs):
    raise AssertionError("unexpected filedialog")


def _unexpected_askyesno(*_args, **_kwargs):
    raise AssertionError("unexpected messagebox.askyesno")


class ReferenceCleanupFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self._original_keymap_set_path = self.app.keymap_set_path
        self.addCleanup(setattr, self.app, "keymap_set_path", self._original_keymap_set_path)
        self._showerror_guard = patch.object(
            reference_cleanup_io_module.messagebox,
            "showerror",
            side_effect=_unexpected_showerror,
        )
        self._askyesno_guard = patch.object(
            reference_cleanup_io_module.messagebox,
            "askyesno",
            side_effect=_unexpected_askyesno,
        )
        self._askopen_guard = patch.object(
            keymap_set_io_module.filedialog,
            "askopenfilename",
            side_effect=_unexpected_filedialog,
        )
        self._asksave_guard = patch.object(
            keymap_set_io_module.filedialog,
            "asksaveasfilename",
            side_effect=_unexpected_filedialog,
        )
        self._showerror_guard.start()
        self._askyesno_guard.start()
        self._askopen_guard.start()
        self._asksave_guard.start()
        self.addCleanup(self._showerror_guard.stop)
        self.addCleanup(self._askyesno_guard.stop)
        self.addCleanup(self._askopen_guard.stop)
        self.addCleanup(self._asksave_guard.stop)

    @staticmethod
    def _inspection() -> ParentRefsCleanupInspection:
        return ParentRefsCleanupInspection(
            kind="keymap",
            stored_path="user/keymaps/main.json",
            alive_refs=("user/keymap_sets/current.json",),
            stale_refs=("user/keymap_sets/removed.json",),
            protected_refs=(),
            state=CLEANUP_TARGET,
        )

    @staticmethod
    def _dialog(result: bool) -> SimpleNamespace:
        return SimpleNamespace(result=result, wait_window=Mock())

    def test_zero_inspections_notifies_without_dialog_or_prune(self):
        self.app.keymap_set_path = "saved.json"
        with patch.object(self.app.config_service, "inspect_parent_refs", return_value=[]) as inspect, patch.object(
            self.app.config_service, "prune_parent_refs"
        ) as prune, patch.object(
            reference_cleanup_io_module,
            "ReferenceCleanupDialog",
        ) as dialog, patch.object(
            reference_cleanup_io_module.messagebox,
            "showinfo",
        ) as showinfo:
            self.app.reference_cleanup_io.run_cleanup()

        inspect.assert_called_once_with(
            self.app.data,
            config_root=self.app.config_root,
            keymap_set_path="saved.json",
        )
        dialog.assert_not_called()
        prune.assert_not_called()
        showinfo.assert_called_once_with("参照元の掃除", CLEANUP_EMPTY_MESSAGE)

    def test_protected_only_inspections_notify_without_dialog_or_prune(self):
        self.app.keymap_set_path = "saved.json"
        protected_inspection = ParentRefsCleanupInspection(
            kind="sequence",
            stored_path="user/sequences/copy.json",
            alive_refs=(),
            stale_refs=(),
            protected_refs=("user/trigger_sets/current.json",),
            state=CLEANUP_PROTECTED,
        )
        with patch.object(
            self.app.config_service,
            "inspect_parent_refs",
            return_value=[protected_inspection],
        ) as inspect, patch.object(self.app.config_service, "prune_parent_refs") as prune, patch.object(
            reference_cleanup_io_module,
            "ReferenceCleanupDialog",
        ) as dialog, patch.object(
            reference_cleanup_io_module.messagebox,
            "showinfo",
        ) as showinfo:
            self.app.reference_cleanup_io.run_cleanup()

        inspect.assert_called_once_with(
            self.app.data,
            config_root=self.app.config_root,
            keymap_set_path="saved.json",
        )
        dialog.assert_not_called()
        prune.assert_not_called()
        showinfo.assert_called_once_with("参照元の掃除", CLEANUP_EMPTY_MESSAGE)

    def test_cancel_does_not_prune_or_change_runtime_dirty_or_file(self):
        self.app.keymap_set_path = "saved.json"
        inspection = self._inspection()
        runtime_before = copy.deepcopy(self.app.data)
        dirty_before = self.app.dirty_tracker.has_unsaved_changes()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "child.json"
            target.write_bytes(b'{"_parent_refs": ["removed.json"]}')
            before = target.read_bytes()
            dialog_instance = self._dialog(False)
            with patch.object(
                self.app.config_service,
                "inspect_parent_refs",
                return_value=[inspection],
            ), patch.object(self.app.config_service, "prune_parent_refs") as prune, patch.object(
                reference_cleanup_io_module,
                "ReferenceCleanupDialog",
                return_value=dialog_instance,
            ):
                self.app.reference_cleanup_io.run_cleanup()

            self.assertEqual(target.read_bytes(), before)

        prune.assert_not_called()
        self.assertEqual(self.app.data, runtime_before)
        self.assertEqual(self.app.dirty_tracker.has_unsaved_changes(), dirty_before)

    def test_execute_prunes_inspections_and_notifies_result(self):
        self.app.keymap_set_path = "saved.json"
        inspection = self._inspection()
        result = ParentRefsPruneResult(
            updated_files=((inspection.stored_path, 1),),
            failed_files=(),
        )
        dialog_instance = self._dialog(True)
        with patch.object(
            self.app.config_service,
            "inspect_parent_refs",
            return_value=[inspection],
        ), patch.object(
            self.app.config_service,
            "prune_parent_refs",
            return_value=result,
        ) as prune, patch.object(
            reference_cleanup_io_module,
            "ReferenceCleanupDialog",
            return_value=dialog_instance,
        ) as dialog, patch.object(
            reference_cleanup_io_module.messagebox,
            "showinfo",
        ) as showinfo:
            self.app.reference_cleanup_io.run_cleanup()

        self.assertEqual(dialog.call_args.kwargs["lines"], format_cleanup_plan([inspection]))
        dialog_instance.wait_window.assert_called_once()
        prune.assert_called_once_with(
            [inspection],
            runtime=self.app.data,
            config_root=self.app.config_root,
            keymap_set_path="saved.json",
        )
        showinfo.assert_called_once_with(
            "参照元の掃除",
            "更新したファイル: 1 件、除去した参照元: 1 件",
        )

    def test_execute_does_not_change_runtime_or_dirty_state(self):
        self.app.keymap_set_path = "saved.json"
        inspection = self._inspection()
        result = ParentRefsPruneResult(
            updated_files=((inspection.stored_path, 1),),
            failed_files=(),
        )
        runtime_before = copy.deepcopy(self.app.data)
        dirty_before = self.app.dirty_tracker.has_unsaved_changes()
        dialog_instance = self._dialog(True)
        with patch.object(
            self.app.config_service,
            "inspect_parent_refs",
            return_value=[inspection],
        ), patch.object(
            self.app.config_service,
            "prune_parent_refs",
            return_value=result,
        ) as prune, patch.object(
            self.app.dirty_tracker,
            "set_dirty",
        ) as set_dirty, patch.object(
            reference_cleanup_io_module,
            "ReferenceCleanupDialog",
            return_value=dialog_instance,
        ), patch.object(reference_cleanup_io_module.messagebox, "showinfo"):
            self.app.reference_cleanup_io.run_cleanup()

        dialog_instance.wait_window.assert_called_once()
        prune.assert_called_once()
        set_dirty.assert_not_called()
        self.assertEqual(self.app.data, runtime_before)
        self.assertEqual(self.app.dirty_tracker.has_unsaved_changes(), dirty_before)

    def test_unsaved_no_stops_before_save_or_inspection(self):
        self.app.keymap_set_path = ""
        with patch.object(
            reference_cleanup_io_module.messagebox,
            "askyesno",
            return_value=False,
        ) as ask, patch.object(self.app.keymap_set_io, "save_keymap_set") as save, patch.object(
            self.app.config_service,
            "inspect_parent_refs",
        ) as inspect:
            self.app.reference_cleanup_io.run_cleanup()

        ask.assert_called_once()
        save.assert_not_called()
        inspect.assert_not_called()

    def test_unsaved_yes_successfully_saves_then_inspects(self):
        self.app.keymap_set_path = ""

        def save(*, show_success_dialog: bool) -> bool:
            self.app.keymap_set_path = "saved.json"
            return True

        with patch.object(
            reference_cleanup_io_module.messagebox,
            "askyesno",
            return_value=True,
        ), patch.object(
            self.app.keymap_set_io,
            "save_keymap_set",
            side_effect=save,
        ) as save_keymap_set, patch.object(
            self.app.config_service,
            "inspect_parent_refs",
            return_value=[],
        ) as inspect, patch.object(
            reference_cleanup_io_module.messagebox,
            "showinfo",
        ):
            self.app.reference_cleanup_io.run_cleanup()

        save_keymap_set.assert_called_once_with(show_success_dialog=False)
        inspect.assert_called_once_with(
            self.app.data,
            config_root=self.app.config_root,
            keymap_set_path="saved.json",
        )

    def test_unsaved_yes_failed_save_stops_cleanup(self):
        self.app.keymap_set_path = ""
        with patch.object(
            reference_cleanup_io_module.messagebox,
            "askyesno",
            return_value=True,
        ), patch.object(
            self.app.keymap_set_io,
            "save_keymap_set",
            return_value=False,
        ) as save, patch.object(
            self.app.config_service,
            "inspect_parent_refs",
        ) as inspect, patch.object(self.app.config_service, "prune_parent_refs") as prune:
            self.app.reference_cleanup_io.run_cleanup()

        save.assert_called_once_with(show_success_dialog=False)
        inspect.assert_not_called()
        prune.assert_not_called()

    def _invoke_menu_command(self, label: str) -> bool:
        """メニューバーのカスケードを走査して label のコマンドを実行する。

        top-level menubar は tearoff エントリを持ち得るため、インデックスを固定せず
        カスケードとラベルで探す。
        """
        menubar = self.app.menubar
        for top_index in range(menubar.index("end") + 1):
            if menubar.type(top_index) != "cascade":
                continue
            submenu = self.app.nametowidget(menubar.entrycget(top_index, "menu"))
            for index in range(submenu.index("end") + 1):
                if submenu.type(index) != "command":
                    continue
                if submenu.entrycget(index, "label") == label:
                    submenu.invoke(index)
                    return True
        return False

    def test_settings_menu_command_runs_cleanup(self):
        self.addCleanup(build_menu_bar, self.app)
        with patch.object(self.app.reference_cleanup_io, "run_cleanup") as run_cleanup:
            build_menu_bar(self.app)
            invoked = self._invoke_menu_command("参照元を掃除…")

        self.assertTrue(invoked, "参照元を掃除… メニューが見つかりません")
        run_cleanup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
