"""ボタンに操作名を書いた選択肢の確認ダイアログ（暫定 51 §3.5）を実ダイアログで確かめる。"""
from __future__ import annotations

import time
import tkinter as tk
import unittest
from tkinter import ttk
from unittest.mock import patch

from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import choice_dialog as choice_dialog_module
from keyseq.presentation.modal import grab_modal
from tests_ui.hook_resume_wait import wait_for_hook_pause_count

_REAL_GRAB_MODAL = choice_dialog_module.grab_modal
_CHOICES = [("left", "左の操作"), ("middle", "中の操作"), ("right", "右の操作")]


class ChoiceDialogTest(unittest.TestCase):
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
        # 破棄前に保留中の after(0) を流し、後続モジュールへ持ち越さない。
        cls.app.update()
        cls.app.destroy()

    def _ask(self, interact, *, default: str = "middle", cancel: str = "right"):
        """ダイアログを開き、開いた後に interact(dialog, observed) を走らせて戻り値を返す。"""
        opened: list[tuple[tk.Toplevel, tk.Misc | None]] = []
        observed: dict = {}

        def capture(window, parent=None, *, focus=None):
            opened.append((window, parent))
            _REAL_GRAB_MODAL(window, parent, focus=focus)

        def poll():
            if not opened:
                self.app.after(10, poll)
                return
            dialog = opened[0][0]
            if not dialog.winfo_viewable():
                self.app.after(10, poll)
                return
            try:
                self._wait_for_button_focus(dialog)
                observed["pause_count_open"] = self.app.hook.get_hook_pause_count()
                interact(dialog, observed)
                self.app.update()
                if dialog.winfo_exists():
                    raise AssertionError("操作の後もダイアログが閉じていない")
            except Exception as exc:  # Tk のコールバック内の失敗をテスト側へ持ち帰る。
                observed["error"] = exc
                if dialog.winfo_exists():
                    dialog.destroy()

        self._require_app_focus()
        pause_before = self.app.hook.get_hook_pause_count()
        with patch.object(choice_dialog_module, "grab_modal", side_effect=capture):
            self.app.after(10, poll)
            result = choice_dialog_module.ask_choice(
                self.app,
                title="選択肢の確認",
                message="本文",
                choices=_CHOICES,
                default=default,
                cancel=cancel,
            )
        wait_for_hook_pause_count(self, self.app, pause_before)
        if "error" in observed:
            raise observed["error"]
        observed["pause_before"] = pause_before
        observed["parent"] = opened[0][1]
        return result, observed

    def _require_app_focus(self):
        # 実使用は「アクティブな App から開く」形なので、App 自身の前面化までは行う
        # （ダイアログ側の focus_force はしない。初期の入力先の欠落を隠すため。test_dialog_initial_focus と同じ）。
        if self.app.focus_displayof() is None:
            self.app.focus_force()
            self.app.update()
        if self.app.focus_displayof() is None:
            self.skipTest("アプリが OS の入力フォーカスを取れないため入力先を検査できない")

    def _wait_for_button_focus(self, dialog) -> None:
        """表示直後は OS 側の前面化が遅れるため、ダイアログ内のボタンに入力先が来るまで待つ（期限つき）。"""
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            self.app.update()
            focused = self.app.focus_get()
            if isinstance(focused, ttk.Button) and str(focused).startswith(f"{dialog}."):
                return
            time.sleep(0.001)

    def _press(self, dialog, sequence: str) -> None:
        """ダイアログ内で最後に入力先だったウィジェットへ実際のフォーカスを戻してからキーを送る。"""
        target = dialog.focus_lastfor()
        deadline = time.monotonic() + 2.0
        while self.app.focus_get() is not target:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"focus not acquired: target={target} focused={self.app.focus_get()}")
            target.focus_force()
            self.app.update()
        target.event_generate(sequence)
        self.app.update()

    def _close_by_window_manager(self, dialog) -> None:
        dialog.tk.call(dialog.protocol("WM_DELETE_WINDOW"))

    def test_default_button_has_initial_focus_and_enter_returns_default(self):
        def interact(dialog, observed):
            focused = self.app.focus_get()
            observed["initial_text"] = focused.cget("text") if isinstance(focused, ttk.Button) else None
            self._press(dialog, "<Return>")

        result, observed = self._ask(interact)

        self.assertEqual(observed["initial_text"], "中の操作")
        self.assertEqual(result, "middle")
        self.assertIs(observed["parent"], self.app)

    def test_tab_moves_to_next_button_and_enter_returns_its_id(self):
        def interact(dialog, observed):
            self._press(dialog, "<Tab>")
            focused = self.app.focus_get()
            observed["after_tab_text"] = focused.cget("text") if isinstance(focused, ttk.Button) else None
            self._press(dialog, "<Return>")

        result, observed = self._ask(interact)

        self.assertEqual(observed["after_tab_text"], "右の操作")
        self.assertEqual(result, "right")

    def test_escape_and_close_return_cancel_id(self):
        for case in ("escape", "close"):
            with self.subTest(case=case):
                def interact(dialog, _observed, _case=case):
                    if _case == "escape":
                        self._press(dialog, "<Escape>")
                    else:
                        self._close_by_window_manager(dialog)

                result, _observed = self._ask(interact, default="left", cancel="middle")

                self.assertEqual(result, "middle")

    def test_hook_pause_count_rises_while_open_and_returns_after_each_close(self):
        def by_button(dialog, _observed):
            self.app.focus_get().invoke()

        def by_escape(dialog, _observed):
            self._press(dialog, "<Escape>")

        cases = (("button", by_button), ("escape", by_escape), ("close", lambda d, _o: self._close_by_window_manager(d)))
        for case, interact in cases:
            with self.subTest(case=case):
                _result, observed = self._ask(interact)

                self.assertEqual(observed["pause_count_open"], observed["pause_before"] + 1)
                self.assertEqual(self.app.hook.get_hook_pause_count(), observed["pause_before"])

    def test_parent_is_window_holding_grab(self):
        holder = tk.Toplevel(self.app)
        self.addCleanup(lambda: holder.winfo_exists() and holder.destroy())
        grab_modal(holder, self.app)
        self.app.update()

        def interact(dialog, observed):
            observed["transient"] = str(dialog.transient())
            observed["master"] = dialog.master
            self._close_by_window_manager(dialog)

        _result, observed = self._ask(interact)

        self.assertIs(observed["parent"], holder)
        self.assertIs(observed["master"], holder)
        self.assertEqual(observed["transient"], str(holder))


if __name__ == "__main__":
    unittest.main()
