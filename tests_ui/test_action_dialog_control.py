"""system / file_line の入力 UI と編集モードの振る舞いを検証する。"""
import unittest
from tkinter import filedialog, messagebox
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.dialogs.action_dialog import ActionDialog


class ActionDialogControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.update()
        cls.app.destroy()

    def setUp(self) -> None:
        self.app.update()
        self.app._dialog_result = None
        patcher = patch.object(messagebox, "showerror")
        self.showerror = patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("start", "stop"):
            patcher = patch.object(self.app.hook_coordinator, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def cleanup_window(self, dialog: ActionDialog) -> None:
        if dialog.winfo_exists():
            dialog.grab_release()
            dialog.destroy()
        self.app.update()

    def make_dialog(self, mode: str = "add", initial: dict | None = None, *,
                    call_candidates: list[tuple[str, str]] | None = None,
                    call_check=None) -> ActionDialog:
        dialog = ActionDialog(
            self.app, title="アクション", initial=initial, mode=mode,
            counter_names=["alpha", "beta"], config_root=self.app.config_root,
            call_candidates=call_candidates, call_check=call_check,
        )
        self.addCleanup(self.cleanup_window, dialog)
        return dialog

    def test_system_loop_keeps_count_when_infinite(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("system")
        dialog.control_fields.system_op_var.set("ループ")
        dialog.control_fields.loop_count_var.set("4")
        dialog.control_fields.loop_infinite_var.set(True)
        dialog.control_fields.sync_system()
        self.assertEqual(str(dialog.control_fields.loop_count_entry.cget("state")), "disabled")
        dialog.action_label_var.set("outer")
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "system", "op": "loop_start", "count": 4,
            "infinite": True, "label": "outer",
        })

    def test_infinite_loop_does_not_reject_invalid_disabled_count(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("system")
        dialog.control_fields.system_op_var.set("ループ")
        dialog.control_fields.loop_count_var.set("invalid")
        dialog.control_fields.loop_infinite_var.set(True)
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "system", "op": "loop_start", "count": 1,
            "infinite": True, "label": "",
        })
        self.showerror.assert_not_called()

    def test_system_counter_operations(self) -> None:
        for display, op in (("カウンター +1", "counter_inc"), ("カウンターを 0 に", "counter_reset")):
            dialog = self.make_dialog()
            dialog.type_var.set("system")
            dialog.control_fields.system_op_var.set(display)
            dialog.control_fields.system_counter_var.set("alpha")
            dialog.action_label_var.set("counter")
            dialog.on_ok()
            self.assertEqual(self.app._dialog_result, {
                "type": "system", "op": op, "counter": "alpha", "label": "counter",
            })

    def test_system_wait_back_and_rewind(self) -> None:
        for display, op, fields in (
            ("待機", "wait", {"ms": 25, "label": "pause"}),
            ("戻す", "back", {"label": "back"}),
            ("先頭へ", "rewind", {"label": "rewind"}),
        ):
            dialog = self.make_dialog()
            dialog.type_var.set("system")
            dialog.control_fields.system_op_var.set(display)
            dialog.control_fields.wait_ms_var.set("25")
            dialog.action_label_var.set(fields["label"])
            dialog.on_ok()
            self.assertEqual(self.app._dialog_result, {"type": "system", "op": op, **fields})

    def test_system_stop_hides_fields_and_loads_for_edit(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("system")
        dialog.control_fields.system_op_var.set("停止")
        dialog.control_fields.sync_system()
        for widget in (
            dialog.control_fields.loop_count_label,
            dialog.control_fields.loop_count_entry,
            dialog.control_fields.loop_infinite_check,
            dialog.control_fields.system_counter_label,
            dialog.control_fields.system_counter_combo,
            dialog.control_fields.wait_label,
            dialog.control_fields.wait_entry,
        ):
            self.assertEqual(widget.winfo_manager(), "")

        dialog.action_label_var.set("stop here")
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "system", "op": "stop", "label": "stop here",
        })

        edit_dialog = self.make_dialog(mode="edit", initial={"type": "system", "op": "stop"})
        self.assertEqual(edit_dialog.control_fields.system_op_var.get(), "停止")

    def test_call_shows_only_readonly_target_dropdown_with_formatted_candidates(self) -> None:
        dialog = self.make_dialog(call_candidates=[("f5", "Macro"), ("f6", "")])
        fields = dialog.control_fields
        dialog.type_var.set("system")
        fields.system_op_var.set("呼び出し")
        fields.sync_system()

        self.assertEqual(fields.call_target_combo.cget("values"), ("f5: Macro", "f6"))
        self.assertEqual(str(fields.call_target_combo.cget("state")), "readonly")
        self.assertNotEqual(fields.call_target_combo.winfo_manager(), "")
        for widget in (
            fields.loop_count_label, fields.loop_count_entry, fields.loop_infinite_check,
            fields.system_counter_label, fields.system_counter_combo,
            fields.wait_label, fields.wait_entry,
        ):
            self.assertEqual(widget.winfo_manager(), "")

    def test_call_result_uses_target_key_and_unselected_target_keeps_dialog_open(self) -> None:
        dialog = self.make_dialog(call_candidates=[("f5", "Macro")])
        dialog.type_var.set("system")
        fields = dialog.control_fields
        fields.system_op_var.set("呼び出し")
        fields.call_target_var.set("f5: Macro")
        dialog.action_label_var.set("invoke")
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "system", "op": "call", "target": "f5", "label": "invoke",
        })

        invalid = self.make_dialog(call_candidates=[("f5", "Macro")])
        invalid.type_var.set("system")
        invalid.control_fields.system_op_var.set("呼び出し")
        invalid.on_ok()
        self.assertTrue(invalid.winfo_exists())
        self.showerror.assert_called_with("入力エラー", "呼び出し先を選んでください")

    def test_call_check_rejects_without_closing_and_accepts_none(self) -> None:
        rejected = self.make_dialog(
            call_candidates=[("f5", "Macro")],
            call_check=lambda _target: "呼び出しが循環します",
        )
        rejected.type_var.set("system")
        rejected.control_fields.system_op_var.set("呼び出し")
        rejected.control_fields.call_target_var.set("f5: Macro")
        rejected.on_ok()
        self.assertTrue(rejected.winfo_exists())
        self.assertEqual(self.showerror.call_args.args[1], "呼び出しが循環します")

        accepted = self.make_dialog(
            call_candidates=[("f5", "Macro")], call_check=lambda _target: None,
        )
        accepted.type_var.set("system")
        accepted.control_fields.system_op_var.set("呼び出し")
        accepted.control_fields.call_target_var.set("f5: Macro")
        accepted.on_ok()
        self.assertFalse(accepted.winfo_exists())
        self.assertEqual(self.app._dialog_result["target"], "f5")

    def test_call_edit_selects_existing_and_rejects_missing_target(self) -> None:
        existing = self.make_dialog(
            mode="edit", initial={"type": "system", "op": "call", "target": "f5"},
            call_candidates=[("f5", "Macro"), ("f6", "")],
        )
        self.assertEqual(existing.control_fields.call_target_var.get(), "f5: Macro")

        missing = self.make_dialog(
            mode="edit", initial={"type": "system", "op": "call", "target": "f5"},
            call_candidates=[("f6", "")], call_check=lambda _target: None,
        )
        self.assertEqual(missing.control_fields.call_target_combo.cget("values"),
                         ("f5（参照先なし）", "f6"))
        self.assertEqual(missing.control_fields.call_target_var.get(), "f5（参照先なし）")
        missing.type_var.set("system")
        missing.on_ok()
        self.assertTrue(missing.winfo_exists())
        self.assertEqual(self.showerror.call_args.args[1], "呼び出し先のトリガーがありません（f5）")

    def test_call_missing_target_display_uses_actual_key(self) -> None:
        # 参照先なしの表示は実際のキーから作る（例示の f5 を固定で出さない）。
        missing = self.make_dialog(
            mode="edit", initial={"type": "system", "op": "call", "target": "z9"},
            call_candidates=[("f6", "")], call_check=lambda _target: None,
        )
        self.assertEqual(missing.control_fields.call_target_var.get(), "z9（参照先なし）")
        missing.type_var.set("system")
        missing.on_ok()
        self.assertTrue(missing.winfo_exists())
        self.assertEqual(self.showerror.call_args.args[1], "呼び出し先のトリガーがありません（z9）")

    def test_call_missing_target_uses_call_check_message(self) -> None:
        checked = []
        missing = self.make_dialog(
            mode="edit", initial={"type": "system", "op": "call", "target": "z9"},
            call_candidates=[("f6", "")],
            call_check=lambda target: checked.append(target) or "自分自身は呼び出せません",
        )
        missing.type_var.set("system")
        missing.on_ok()

        self.assertEqual(checked, ["z9"])
        self.assertEqual(self.showerror.call_args.args[1], "自分自身は呼び出せません")
        self.assertTrue(missing.winfo_exists())

    def test_call_note_about_interval_is_shown_only_for_call(self) -> None:
        dialog = self.make_dialog(call_candidates=[("f6", "")])
        dialog.type_var.set("system")
        fields = dialog.control_fields
        fields.system_op_var.set("呼び出し")
        fields.sync_system()
        self.assertTrue(fields.call_note_label.winfo_manager())
        self.assertIn("間隔(ms)", fields.call_note_label.cget("text"))
        fields.system_op_var.set("待機")
        fields.sync_system()
        self.assertFalse(fields.call_note_label.winfo_manager())

    def test_system_operation_order_remains_unchanged_around_call(self) -> None:
        values = list(self.make_dialog().control_fields.system_op_combo.cget("values"))
        self.assertLess(values.index("停止"), values.index("呼び出し"))
        self.assertLess(values.index("呼び出し"), values.index("戻す"))

    def test_file_line_mappings_and_config_relative_path(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("file_line")
        dialog.control_fields.file_path_var.set("C:/config/lines.txt")
        dialog.control_fields.file_counter_var.set("beta")
        dialog.control_fields.encoding_var.set("Shift_JIS")
        dialog.control_fields.out_of_range_var.set("折り返し")
        dialog.action_label_var.set("line")
        with patch.object(self.app.config_service, "to_config_relative_or_absolute", return_value="lines.txt") as convert:
            dialog.on_ok()
        convert.assert_called_once_with("C:/config/lines.txt", self.app.config_root)
        self.assertEqual(self.app._dialog_result, {
            "type": "file_line", "path": "lines.txt", "counter": "beta",
            "encoding": "shift_jis", "out_of_range": "wrap", "label": "line",
        })

    def test_file_line_default_encoding_and_range_policy(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("file_line")
        dialog.control_fields.file_path_var.set("lines.txt")
        dialog.control_fields.file_counter_var.set("line_number")
        with patch.object(self.app.config_service, "to_config_relative_or_absolute", return_value="lines.txt"):
            dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "file_line", "path": "lines.txt", "counter": "line_number",
            "encoding": "utf-8", "out_of_range": "error", "label": "",
        })

    def test_file_browse_uses_parent_dialog(self) -> None:
        dialog = self.make_dialog()
        with patch.object(filedialog, "askopenfilename", return_value="picked.txt") as browse:
            dialog.control_fields.browse_file()
        browse.assert_called_once_with(parent=dialog)
        self.assertEqual(dialog.control_fields.file_path_var.get(), "picked.txt")

    def test_validation_errors_keep_dialog_open(self) -> None:
        cases = (
            ("system", "ループ", "0", "", ""),
            ("system", "ループ", "invalid", "", ""),
            ("system", "待機", "1.5", "", ""),
            ("system", "カウンター +1", "", "", ""),
            ("file_line", "", "", "", "named"),
            ("file_line", "", "", "lines.txt", ""),
        )
        for kind, operation, value, path, counter in cases:
            dialog = self.make_dialog()
            dialog.type_var.set(kind)
            if kind == "system":
                dialog.control_fields.system_op_var.set(operation)
                if operation == "ループ":
                    dialog.control_fields.loop_count_var.set(value)
                elif operation == "待機":
                    dialog.control_fields.wait_ms_var.set(value)
            else:
                dialog.control_fields.file_path_var.set(path)
                dialog.control_fields.file_counter_var.set(counter)
            dialog.on_ok()
            self.assertTrue(dialog.winfo_exists())
        self.assertEqual(self.showerror.call_count, len(cases))

    def test_add_only_append_checkbox_defaults_on(self) -> None:
        add_dialog = self.make_dialog("add")
        self.assertTrue(add_dialog.append_to_end_var.get())
        self.assertTrue(add_dialog.append_to_end)
        add_dialog.append_to_end_var.set(False)
        add_dialog.type_var.set("system")
        add_dialog.control_fields.system_op_var.set("戻す")
        add_dialog.on_ok()
        self.assertFalse(add_dialog.append_to_end)
        edit_dialog = self.make_dialog("edit", {"type": "text", "value": "hello"})
        self.assertFalse(hasattr(edit_dialog, "append_to_end_var"))

    def test_append_choice_applies_to_existing_action_types(self) -> None:
        dialog = self.make_dialog("add")
        dialog.type_var.set("text")
        dialog.value_var.set("hello")
        dialog.append_to_end_var.set(False)
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "text", "value": "hello", "label": "",
        })
        self.assertFalse(dialog.append_to_end)

    def test_edit_excludes_loop_and_loop_edit_is_fixed(self) -> None:
        edit = self.make_dialog("edit", {"type": "system", "op": "counter_inc", "counter": "alpha"})
        self.assertNotIn("ループ", edit.control_fields.system_op_combo.cget("values"))
        loop = self.make_dialog("edit_loop", {
            "type": "system", "op": "loop_start", "count": 3, "infinite": False, "label": "L",
        })
        self.assertEqual(str(loop.type_combo.cget("state")), "disabled")
        self.assertEqual(str(loop.control_fields.system_op_combo.cget("state")), "disabled")
        loop.control_fields.loop_count_var.set("5")
        loop.control_fields.system_op_var.set("戻す")
        loop.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "system", "op": "loop_start", "count": 5, "infinite": False, "label": "L",
        })


if __name__ == "__main__":
    unittest.main()
