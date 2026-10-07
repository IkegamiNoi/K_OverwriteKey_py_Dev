from __future__ import annotations

import os
import tempfile
import tkinter
import unittest
from tkinter import font, ttk
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.domain.keymap_triggers import get_active_triggers
from keyseq.application.save_plan import compose_sequence_key, ACTION_SAVE, ACTION_SAVE_AS, ACTION_SKIP, CHILD_KEYMAP, CHILD_SEQUENCE, CHILD_TRIGGER_SET
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import child_save_dialog as child_save_dialog_module
from keyseq.presentation.controllers.config_io import child_save_columns as child_save_columns_module
from keyseq.presentation.controllers.config_io.child_save_rows import (
    SHARE_NEW,
    SHARE_NEW_COLLIDES,
    SHARE_OTHER_PARENT,
    SHARE_SHARED,
    SHARE_SOLE,
    SHARE_UNKNOWN,
    ChildSaveRow,
    share_text_for,
)


_REAL_CONFIRM_TRIGGER_SET_DEPENDENCY = (
    child_save_dialog_module.ChildSaveDialog.confirm_trigger_set_dependency
)
_REAL_ASK_CHILD_SAVE_ACTIONS = child_save_dialog_module.ChildSaveDialog.ask_child_save_actions
_REAL_CONFIRM_RECALCULATED_OVERWRITE = (
    child_save_dialog_module.ChildSaveDialog.confirm_recalculated_overwrite
)


def _unexpected_trigger_set_dependency(*_args, **_kwargs):
    raise AssertionError(
        "想定外の依存確認ダイアログ。期待するならテスト側で patch すること"
    )


def _unexpected_child_save_actions(*_args, **_kwargs):
    raise AssertionError(
        "想定外の子保存ダイアログ。期待するならテスト側で patch すること"
    )


def _unexpected_recalculated_overwrite(*_args, **_kwargs):
    raise AssertionError(
        "想定外の再計算後上書き確認。期待するならテスト側で patch すること"
    )


def _unexpected_showerror(_title, message, *_args, **_kwargs):
    raise AssertionError(f"想定外のエラーダイアログ: {message}")


def _unexpected_askyesno(*_args, **_kwargs):
    raise AssertionError("想定外の確認ダイアログ。期待するならテスト側で patch すること")


def make_data(*, second_sequence: bool = False):
    triggers = [{"key": "f1", "label": "Copy", "actions": [{"type": "text", "value": "old", "label": ""}]}]
    if second_sequence:
        triggers.append({"key": "f2", "label": "Other", "actions": []})
    return {
        "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}, "triggers": triggers}],
        "triggers": [],
        "active_keymap_id": "km1",
    }


class _FakeDialogWidget:
    pack_history = []

    def __init__(self, *_args, **kwargs):
        self.kwargs = kwargs
        self.bindings = {}
        self.configure_calls = []
        self.create_window_calls = []
        self.itemconfigure_calls = []
        self.grid_calls = []
        self.pack_calls = []
        self.columnconfigure_calls = []
        self.focused = False
        self.place_calls = []
        self._placed = {}

    def grid(self, **kwargs):
        self.grid_calls.append(kwargs)
        return self

    def place(self, **kwargs):
        self.place_calls.append(kwargs)
        self._placed.update(kwargs)
        return self

    def lift(self):
        pass

    def pack(self, **kwargs):
        self.pack_calls.append(kwargs)
        self.pack_history.append(kwargs)
        return self

    def bind(self, sequence, callback, add=None):
        # grab_modal は既存ハンドラを潰さないよう add="+" で結線する。
        self.bindings[sequence] = callback

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)

    def create_window(self, *args, **kwargs):
        self.create_window_calls.append((args, kwargs))
        return 1

    def itemconfigure(self, *args, **kwargs):
        self.itemconfigure_calls.append((args, kwargs))

    def bbox(self, _tag):
        return (0, 0, 100, 100)

    def yview(self, *_args):
        pass

    def yview_scroll(self, *_args):
        pass

    def set(self, *_args):
        pass

    def columnconfigure(self, *args, **kwargs):
        self.columnconfigure_calls.append((args, kwargs))

    def rowconfigure(self, *_args, **_kwargs):
        pass

    def focus_set(self):
        self.focused = True

    def update_idletasks(self):
        pass

    def winfo_width(self):
        return 200

    def winfo_reqwidth(self):
        return 20

    def winfo_reqheight(self):
        return 20

    def winfo_exists(self):
        return True

    def grid_bbox(self, *args):
        start_column = args[0] if args else 0
        end_column = args[2] if len(args) >= 4 else start_column
        final_row = args[3] if len(args) >= 4 else max(
            (call.get("row", 0) for call in self.grid_calls), default=0
        )
        configured = {
            call_args[0]: kwargs["minsize"]
            for call_args, kwargs in self.columnconfigure_calls
            if call_args and "minsize" in kwargs
        }
        if start_column == end_column:
            if start_column in configured:
                width = configured[start_column]
            elif start_column == 4:
                width = 110
            else:
                width = 20
        else:
            width = sum(configured.get(column, 110 if column == 4 else 20)
                        for column in range(start_column, end_column + 1))
        return (0, 0, width, 30 * (final_row + 1))


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
        self.bindings = {}
        self.destroyed = False
        self.geometry_calls = []
        self.minsize_calls = []
        self.resizable_calls = []
        self.call_log = []
        self.screen_width = 1400
        self.screen_height = 1000
        self.root_x = 0
        self.root_y = 30

    def focus_set(self):
        self.call_log.append("focus_set")

    def title(self, _value):
        pass

    def geometry(self, value):
        self.geometry_calls.append(value)

    def minsize(self, width, height):
        self.minsize_calls.append((width, height))
        self.call_log.append("minsize")

    def resizable(self, width, height):
        self.resizable_calls.append((width, height))

    def update_idletasks(self):
        self.call_log.append("update_idletasks")

    def winfo_screenwidth(self):
        return self.screen_width

    def winfo_screenheight(self):
        return self.screen_height

    def winfo_rootx(self):
        return self.root_x

    def winfo_rooty(self):
        return self.root_y

    def winfo_x(self):
        return 0

    def winfo_y(self):
        return 0

    def after_idle(self, callback):
        callback()

    def transient(self, _master):
        pass

    def grab_current(self):
        return None

    def grab_set(self):
        pass

    def protocol(self, name, command):
        self.protocols[name] = command

    def bind(self, sequence, callback, add=None):
        # grab_modal は既存ハンドラを潰さないよう add="+" で結線する。
        self.bindings[sequence] = callback

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
        # 破棄前に保留中の after(0) を流し、後続モジュールへ持ち越さない。
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        self._child_save_actions_guard = patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "ask_child_save_actions",
            side_effect=_unexpected_child_save_actions,
        )
        self._dependency_confirm_guard = patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "confirm_trigger_set_dependency",
            side_effect=_unexpected_trigger_set_dependency,
        )
        self._recalculated_overwrite_guard = patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "confirm_recalculated_overwrite",
            side_effect=_unexpected_recalculated_overwrite,
        )
        self._showerror_guard = patch.object(
            tkinter.messagebox,
            "showerror",
            side_effect=_unexpected_showerror,
        )
        self._askyesno_guard = patch.object(
            tkinter.messagebox,
            "askyesno",
            side_effect=_unexpected_askyesno,
        )
        self._child_save_actions_guard.start()
        self._dependency_confirm_guard.start()
        self._recalculated_overwrite_guard.start()
        self._showerror_guard.start()
        self._askyesno_guard.start()
        self.addCleanup(self._child_save_actions_guard.stop)
        self.addCleanup(self._dependency_confirm_guard.stop)
        self.addCleanup(self._recalculated_overwrite_guard.stop)
        self.addCleanup(self._showerror_guard.stop)
        self.addCleanup(self._askyesno_guard.stop)

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

    def _ask_dialog_internally(
        self, rows, on_wait, *, save_as_path="", screen_width=1400, screen_height=1000
    ):
        variables = []
        dialog = _FakeSaveDialog(lambda current: on_wait(current, variables))
        dialog.screen_width = screen_width
        dialog.screen_height = screen_height
        _FakeDialogWidget.pack_history = []
        dialog.frames = []
        dialog.labels = []

        def make_string_var(*, value):
            variable = _FakeStringVar(value=value)
            variables.append(variable)
            return variable

        def make_button(_master, *, text, command, **_kwargs):
            dialog.buttons[text] = command
            return _FakeDialogWidget()

        canvas = _FakeDialogWidget()
        scrollbar = _FakeDialogWidget()
        dialog.canvas = canvas
        dialog.scrollbar = scrollbar
        dialog.canvas_calls = []
        dialog.scrollbar_calls = []

        def make_canvas(*args, **kwargs):
            dialog.canvas_calls.append((args, kwargs))
            return canvas

        def make_scrollbar(*args, **kwargs):
            dialog.scrollbar_calls.append((args, kwargs))
            return scrollbar

        def make_frame(*args, **kwargs):
            widget = _FakeDialogWidget(*args, **kwargs)
            dialog.frames.append(widget)
            if args and args[0] is canvas:
                dialog.content_frame = widget
            elif args and args[0] is getattr(dialog, "list_frame", None):
                dialog.header_frame = widget
            elif kwargs.get("padding") == 12:
                dialog.outer_frame = widget
            elif args and args[0] is getattr(dialog, "outer_frame", None):
                dialog.outer_frame_child_count = getattr(dialog, "outer_frame_child_count", 0) + 1
                if dialog.outer_frame_child_count == 2:
                    dialog.list_frame = widget
            return widget

        def make_label(*args, **kwargs):
            widget = _FakeDialogWidget(*args, **kwargs)
            dialog.labels.append(widget)
            return widget

        with patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "ask_child_save_actions",
            _REAL_ASK_CHILD_SAVE_ACTIONS,
        ), patch.object(child_save_dialog_module.tk, "Toplevel", return_value=dialog), patch.object(
            child_save_dialog_module.tk,
            "StringVar",
            side_effect=make_string_var,
        ), patch.object(child_save_dialog_module.ttk, "Frame", side_effect=make_frame), patch.object(
            child_save_dialog_module.ttk,
            "Label",
            side_effect=make_label,
        ), patch.object(
            child_save_dialog_module.ttk,
            "Radiobutton",
            return_value=_FakeDialogWidget(),
        ), patch.object(
            child_save_dialog_module.ttk,
            "Button",
            side_effect=make_button,
        ), patch.object(
            child_save_dialog_module.tk,
            "Canvas",
            side_effect=make_canvas,
        ), patch.object(
            child_save_dialog_module.ttk,
            "Scrollbar",
            side_effect=make_scrollbar,
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

    def test_child_save_escape_uses_window_close_handler(self):
        def close(dialog, _variables):
            self.assertIn("<Escape>", dialog.bindings)
            close_handler = dialog.protocols["WM_DELETE_WINDOW"]
            self.assertEqual(close_handler, dialog.destroy)
            with patch.object(dialog, "destroy", wraps=close_handler) as destroy:
                dialog.bindings["<Escape>"](None)
            destroy.assert_called_once_with()

        result, _variables, dialog = self._ask_dialog_internally([], close)
        self.assertIsNone(result)
        self.assertTrue(dialog.destroyed)

    def _ask_dependency_internally(self, row, on_wait, *, save_as_path=""):
        dialog = _FakeSaveDialog(on_wait)
        buttons = {}

        def make_button(_master, *, text, command, **_kwargs):
            widget = _FakeDialogWidget()
            dialog.buttons[text] = command
            buttons[text] = widget
            return widget

        with patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "confirm_trigger_set_dependency",
            _REAL_CONFIRM_TRIGGER_SET_DEPENDENCY,
        ), patch.object(child_save_dialog_module.tk, "Toplevel", return_value=dialog), patch.object(
            child_save_dialog_module.ttk, "Frame", side_effect=_FakeDialogWidget
        ), patch.object(child_save_dialog_module.ttk, "Label", return_value=_FakeDialogWidget()), patch.object(
            child_save_dialog_module.ttk, "Button", side_effect=make_button
        ), patch.object(
            self.app.child_save_dialog, "_ask_save_as_path", return_value=save_as_path
        ), patch.object(self.app.hook, "suspend_hook_for_dialog") as suspend, patch.object(
            self.app.hook, "resume_hook_after_dialog"
        ) as resume:
            result = self.app.child_save_dialog.confirm_trigger_set_dependency(
                blocked_labels=["Copy"], trigger_set_row=row
            )

        self.assertEqual(suspend.call_count, resume.call_count)
        return result, dialog, buttons

    def test_dialog_internal_rows_use_default_actions(self):
        rows = [
            ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE),
            ChildSaveRow(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"), "Copy", "C:/copy.json", SHARE_UNKNOWN, "不明", ACTION_SAVE_AS),
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
            ChildSaveRow(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"), "Copy", "C:/copy.json", SHARE_UNKNOWN, "不明", ACTION_SAVE_AS)
        ]
        result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda dialog, _variables: dialog.buttons["OK"](),
        )

        self.assertIsNone(result)
        self.assertFalse(dialog.destroyed)

    def test_dialog_layout_uses_content_height_and_resizable_width(self):
        rows = [
            ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE),
            ChildSaveRow(CHILD_SEQUENCE, "f1", "Copy", "C:/copy.json", SHARE_UNKNOWN, "不明", ACTION_SAVE),
        ]
        _result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda current, _variables: current.buttons["キャンセル"](),
        )

        self.assertEqual(len(dialog.geometry_calls), 1)
        width, height = (int(value) for value in dialog.geometry_calls[0].split("x"))
        self.assertEqual(width, child_save_columns_module.OPENING_WIDTH)
        self.assertLess(height, 480)
        self.assertEqual(height, 90)
        self.assertEqual(dialog.resizable_calls, [(True, True)])
        self.assertLess(dialog.call_log.index("update_idletasks"), dialog.call_log.index("minsize"))
        self.assertEqual(len(dialog.minsize_calls), 1)
        self.assertGreater(dialog.minsize_calls[0][0], 0)
        self.assertGreater(dialog.minsize_calls[0][1], 0)

    def test_dialog_packs_button_row_before_expandable_list(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE)]
        self._ask_dialog_internally(rows, lambda current, _variables: current.buttons["キャンセル"]())

        button_index = next(
            index for index, kwargs in enumerate(_FakeDialogWidget.pack_history) if kwargs.get("side") == "bottom"
        )
        list_index = next(
            index
            for index, kwargs in enumerate(_FakeDialogWidget.pack_history[button_index + 1 :], start=button_index + 1)
            if kwargs.get("fill") == "both" and kwargs.get("expand") is True
        )
        self.assertLess(button_index, list_index)
        self.assertNotIn("expand", _FakeDialogWidget.pack_history[button_index])
        self.assertEqual(_FakeDialogWidget.pack_history[button_index]["anchor"], "e")

    def test_dialog_configures_fixed_and_flexible_columns(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE)]
        _result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda current, _variables: current.buttons["キャンセル"](),
        )

        configurations = {args[0]: kwargs for args, kwargs in dialog.content_frame.columnconfigure_calls}
        for column in (0, 1, 3, 4):
            self.assertEqual(configurations[column]["weight"], 0)
        self.assertGreaterEqual(configurations[2]["weight"], 1)
        for column in (0, 1, 2, 3):
            self.assertIn("minsize", configurations[column])
        flexible_labels = [label for label in dialog.labels if label.kwargs.get("width") == 1]
        self.assertTrue(flexible_labels)
        self.assertTrue(all(label.kwargs.get("anchor") == "w" for label in flexible_labels))
        self.assertTrue(
            all(any(call.get("sticky") == "ew" for call in label.grid_calls) for label in flexible_labels)
        )
        header_configurations = {
            args[0]: kwargs for args, kwargs in dialog.header_frame.columnconfigure_calls
        }
        self.assertEqual(header_configurations, configurations)

    def test_opening_width_uses_screen_width_below_opening_width(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE)]
        _result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda current, _variables: current.buttons["キャンセル"](),
            screen_width=600,
        )

        width = int(dialog.geometry_calls[0].split("x")[0])
        self.assertEqual(width, 600)
        self.assertLessEqual(dialog.minsize_calls[0][0], dialog.screen_width)

    def test_default_column_widths_and_name_cap_use_opening_list_width(self):
        long_name = "長い対象名" * 30
        row = ChildSaveRow(
            CHILD_SEQUENCE,
            "f1",
            long_name,
            "C:/copy.json",
            SHARE_SOLE,
            "この構成のみが所有・既存を上書き",
            ACTION_SAVE,
        )
        _result, _variables, dialog = self._ask_dialog_internally(
            [row], lambda current, _variables: current.buttons["キャンセル"]()
        )
        columns = dialog._child_save_columns
        measure = font.nametofont("TkDefaultFont").measure

        self.assertEqual(
            columns.widths[0],
            max(columns.minimums[0], measure(child_save_dialog_module._kind_label(row.kind)) + child_save_columns_module.CELL_GAP),
        )
        self.assertEqual(
            columns.widths[3],
            max(columns.minimums[3], measure(row.share_text) + child_save_columns_module.CELL_GAP),
        )
        expected_name_cap = max(
            columns.minimums[1],
            int((child_save_columns_module.OPENING_WIDTH - columns.overhead_width) * .3),
        )
        self.assertEqual(columns.widths[1], expected_name_cap)

    def test_opening_width_uses_minimum_above_opening_width(self):
        row = ChildSaveRow(
            CHILD_SEQUENCE, "f1", "長い対象名" * 30, "C:/copy.json", SHARE_SOLE,
            "共有状況" * 22, ACTION_SAVE,
        )
        with patch.object(
            child_save_columns_module.font, "nametofont",
            return_value=SimpleNamespace(measure=lambda text: len(text) * 10),
        ):
            _result, _variables, dialog = self._ask_dialog_internally(
                [row], lambda current, _variables: current.buttons["キャンセル"](),
                screen_width=2000,
            )
        columns = dialog._child_save_columns
        self.assertEqual(
            columns.widths[1],
            int((child_save_columns_module.OPENING_WIDTH - columns.overhead_width) * .3),
        )
        self.assertGreater(columns.minimum_width(), child_save_columns_module.OPENING_WIDTH)
        self.assertLessEqual(columns.minimum_width(), dialog.screen_width)
        self.assertEqual(int(dialog.geometry_calls[0].split("x")[0]), columns.minimum_width())

    def test_columns_shrink_to_screen_in_name_share_kind_order(self):
        row = ChildSaveRow(
            CHILD_SEQUENCE,
            "f1",
            "Very long target name " * 10,
            "C:/copy.json",
            SHARE_SOLE,
            "この構成のみが所有・既存を上書きする長い共有状況",
            ACTION_SAVE,
        )

        with patch.object(
            child_save_columns_module.font,
            "nametofont",
            return_value=SimpleNamespace(measure=lambda text: len(text) * 10),
        ):
            _result, _variables, wide_dialog = self._ask_dialog_internally(
                [row],
                lambda current, _variables: current.buttons["キャンセル"](),
                screen_width=1400,
            )
            wide = wide_dialog._child_save_columns
            name_reduction = wide.widths[1] - wide.minimums[1]
            share_reduction = wide.widths[3] - wide.minimums[3]
            _result, _variables, narrow_dialog = self._ask_dialog_internally(
                [row],
                lambda current, _variables: current.buttons["キャンセル"](),
                screen_width=wide.minimum_width() - max(1, name_reduction // 2),
            )
            narrow = narrow_dialog._child_save_columns
            _result, _variables, share_dialog = self._ask_dialog_internally(
                [row],
                lambda current, _variables: current.buttons["キャンセル"](),
                screen_width=wide.minimum_width() - name_reduction - 10,
            )
            share = share_dialog._child_save_columns
            _result, _variables, kind_dialog = self._ask_dialog_internally(
                [row],
                lambda current, _variables: current.buttons["キャンセル"](),
                screen_width=wide.minimum_width() - name_reduction - share_reduction - 1,
            )
            kind = kind_dialog._child_save_columns

        self.assertLess(narrow.widths[1], wide.widths[1])
        self.assertEqual(narrow.widths[3], wide.widths[3])
        self.assertEqual(narrow.widths[0], wide.widths[0])
        self.assertEqual(narrow.widths[1], wide.widths[1] - max(1, name_reduction // 2))
        self.assertEqual(share.widths[1], share.minimums[1])
        self.assertLess(share.widths[3], wide.widths[3])
        self.assertEqual(share.widths[0], wide.widths[0])
        self.assertEqual(kind.widths[1], kind.minimums[1])
        self.assertEqual(kind.widths[3], kind.minimums[3])
        self.assertLess(kind.widths[0], wide.widths[0])
        self.assertEqual(narrow.widths[4], wide.widths[4])
        self.assertEqual(share.widths[4], wide.widths[4])
        self.assertEqual(kind.widths[4], wide.widths[4])
        for current_dialog, current_columns in (
            (narrow_dialog, narrow),
            (share_dialog, share),
        ):
            self.assertEqual(current_dialog.minsize_calls[0][0], current_columns.minimum_width())
            self.assertLessEqual(current_dialog.minsize_calls[0][0], current_dialog.screen_width)
        self.assertEqual(kind_dialog.minsize_calls[0][0], kind.minimum_width())
        self.assertLessEqual(kind_dialog.minsize_calls[0][0], kind_dialog.screen_width)

    def test_columns_keep_irreducible_minimum_when_it_exceeds_screen(self):
        row = ChildSaveRow(
            CHILD_SEQUENCE,
            "f1",
            "Very long target name " * 10,
            "C:/copy.json",
            SHARE_SOLE,
            "この構成のみが所有・既存を上書きする長い共有状況",
            ACTION_SAVE,
        )
        _result, _variables, dialog = self._ask_dialog_internally(
            [row],
            lambda current, _variables: current.buttons["キャンセル"](),
            screen_width=100,
        )
        columns = dialog._child_save_columns
        width = int(dialog.geometry_calls[0].split("x")[0])

        for column in (0, 1, 3):
            self.assertEqual(columns.widths[column], columns.minimums[column])
        self.assertEqual(dialog.minsize_calls[0][0], columns.minimum_width())
        self.assertEqual(width, columns.minimum_width())
        self.assertGreater(width, dialog.screen_width)

    def test_configures_track_content_and_text_cell_widths_without_repeat_fitting(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "長い対象名" * 7, "C:/" + "long-directory/" * 5, SHARE_SOLE, "この構成のみが所有・既存を上書き", ACTION_SAVE)]

        def configure_content_and_cells(current, _variables):
            current.canvas.bindings["<Configure>"](SimpleNamespace(width=300))
            current.canvas.bindings["<Configure>"](SimpleNamespace(width=300))
            for _ in range(2):
                for label in current.labels:
                    if "<Enter>" in label.bindings:
                        label.bindings["<Configure>"](SimpleNamespace(width=200))
            current.buttons["キャンセル"]()

        with patch.object(child_save_dialog_module, "_fit_text", wraps=child_save_dialog_module._fit_text) as fit:
            _result, _variables, dialog = self._ask_dialog_internally(
                rows,
                configure_content_and_cells,
            )

        self.assertIn("<Configure>", dialog.canvas.bindings)
        self.assertEqual(dialog.canvas.itemconfigure_calls, [((1,), {"width": 300})])
        text_cell_labels = [label for label in dialog.labels if "<Enter>" in label.bindings]
        self.assertEqual(len(text_cell_labels), 4)
        self.assertEqual(fit.call_count, 4)
        self.assertTrue(all(label.configure_calls for label in text_cell_labels))

    def test_dialog_layout_creates_vertical_scroll_region_without_horizontal_scrollbar(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE)]
        _result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda current, _variables: current.buttons["キャンセル"](),
        )

        self.assertEqual(len(dialog.canvas_calls), 1)
        self.assertEqual(dialog.scrollbar_calls[0][1]["orient"], "vertical")
        self.assertEqual(len(dialog.canvas.create_window_calls), 1)
        self.assertEqual(len(dialog.scrollbar_calls), 1)
        self.assertIn("<MouseWheel>", dialog.bindings)
        self.assertNotIn("<MouseWheel>", dialog.canvas.bindings)

    def test_dialog_binds_tooltips_for_all_cells_but_shows_only_ellipsized_text(self):
        short_row = ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "x", SHARE_SOLE, "新規", ACTION_SAVE)
        long_name = "長い対象名" * 7
        long_path = "C:/" + "long-directory/" * 5 + "target.json"
        long_share = "共有（他の構成セットからも参照されるため上書きします）"
        long_row = ChildSaveRow(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"), long_name, long_path, SHARE_SOLE, long_share, ACTION_SAVE)

        def configure_content_and_cells(current, _variables):
            current.canvas.bindings["<Configure>"](SimpleNamespace(width=100))
            for label in current.labels:
                # bind_hover_tooltip を差し替えているため <Enter> は付かない。
                # 文言のセルは幅の <Configure> で選ぶ。
                if "<Configure>" in label.bindings:
                    label.bindings["<Configure>"](SimpleNamespace(width=80))
            current.buttons["キャンセル"]()

        with patch.object(child_save_dialog_module, "bind_hover_tooltip") as bind_tooltip:
            self._ask_dialog_internally(
                [short_row, long_row],
                configure_content_and_cells,
            )

        self.assertEqual(
            [call.args[1]() for call in bind_tooltip.call_args_list],
            [
                child_save_dialog_module._kind_label(short_row.kind),
                short_row.display_name,
                short_row.target_path,
                short_row.share_text,
                child_save_dialog_module._kind_label(long_row.kind),
                long_name,
                long_path,
                long_row.share_text,
            ],
        )
        self.assertEqual(
            [call.args[2]() for call in bind_tooltip.call_args_list],
            [False, False, False, False, False, True, True, True],
        )

    def test_dialog_layout_caps_height_for_many_rows(self):
        rows = [
            ChildSaveRow(CHILD_SEQUENCE, f"f{index}", f"Copy {index}", f"C:/copy-{index}.json", SHARE_SOLE, "単独", ACTION_SAVE)
            for index in range(60)
        ]
        _result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda current, _variables: current.buttons["キャンセル"](),
        )

        self.assertEqual(len(dialog.geometry_calls), 1)
        _width, height = (int(value) for value in dialog.geometry_calls[0].split("x"))
        self.assertLessEqual(height + dialog.root_y, int(dialog.screen_height * 0.6))

    def test_dialog_prefers_minimum_height_when_screen_limit_is_smaller(self):
        rows = [ChildSaveRow(CHILD_KEYMAP, "km1", "Main", "C:/main.json", SHARE_SOLE, "単独", ACTION_SAVE)]
        _result, _variables, dialog = self._ask_dialog_internally(
            rows,
            lambda current, _variables: current.buttons["キャンセル"](),
            screen_height=100,
        )

        _width, height = (int(value) for value in dialog.geometry_calls[0].split("x"))
        self.assertEqual(height, dialog.minsize_calls[0][1])

    def test_ellipsize_preserves_short_text_and_truncates_long_text(self):
        self.assertEqual(child_save_dialog_module._ellipsize("short", 8), "short")
        self.assertEqual(child_save_dialog_module._ellipsize("abcdefgh", 5), "abcd…")

    def test_ellipsize_path_preserves_ends_and_limit(self):
        self.assertEqual(child_save_dialog_module._ellipsize_path("short", 8), "short")
        result = child_save_dialog_module._ellipsize_path("abcdefghijkl", 8)

        self.assertEqual(result, "ab…hijkl")
        self.assertEqual(len(result), 8)

    def test_fit_text_preserves_text_that_fits(self):
        measure = lambda text: len(text) * 10

        self.assertEqual(child_save_dialog_module._fit_text("short", measure, 50, child_save_dialog_module._ellipsize), "short")

    def test_fit_text_ellipsizes_end_and_path_within_available_width(self):
        measure = lambda text: len(text) * 10
        for ellipsize in (child_save_dialog_module._ellipsize, child_save_dialog_module._ellipsize_path):
            with self.subTest(ellipsize=ellipsize.__name__):
                result = child_save_dialog_module._fit_text("abcdefghijkl", measure, 80, ellipsize)
                self.assertNotEqual(result, "abcdefghijkl")
                self.assertLessEqual(measure(result), 80)

    def test_fit_text_path_handles_the_one_character_suffix_boundary(self):
        measure = lambda text: len(text) * 10

        self.assertEqual(
            child_save_dialog_module._fit_text("abcdefghijkl", measure, 20, child_save_dialog_module._ellipsize_path),
            "…l",
        )

    def test_fit_text_returns_ellipsis_when_no_candidate_fits(self):
        measure = lambda text: len(text) * 10

        self.assertEqual(
            child_save_dialog_module._fit_text("abcdefghijkl", measure, 1, child_save_dialog_module._ellipsize),
            "…",
        )

    def test_initial_layout_refits_text_cells_after_cell_configure(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        row = ChildSaveRow(
            CHILD_SEQUENCE,
            "f1",
            "very-long-target-name-" * 20,
            "C:/" + "very-long-directory/" * 20 + "target.json",
            SHARE_SOLE,
            "この構成のみが所有・既存を上書き",
            ACTION_SAVE,
        )
        dialog = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog([row], {})[0]
        try:
            dialog.deiconify()
            dialog.update()
            frame = dialog.winfo_children()[0]
            list_frame = next(
                widget
                for widget in frame.winfo_children()
                if isinstance(widget, ttk.Frame) and widget.pack_info().get("fill") == "both"
            )
            canvas = next(widget for widget in list_frame.winfo_children() if isinstance(widget, tkinter.Canvas))
            if canvas.winfo_width() <= 1:
                self.skipTest("ウィンドウマネージャーがないため、Canvas の実レイアウトを検証できません")
            content_frame = canvas.winfo_children()[0]
            name_label = content_frame.grid_slaves(row=0, column=1)[0]
            path_label = content_frame.grid_slaves(row=0, column=2)[0]

            self.assertNotEqual(name_label.cget("text"), "…")
            self.assertNotEqual(path_label.cget("text"), "…")
        finally:
            dialog.destroy()
            root.destroy()

    def test_only_path_cell_gains_width_when_dialog_width_changes(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        row = ChildSaveRow(
            CHILD_SEQUENCE,
            "f1",
            "very-long-target-name-" * 20,
            "C:/" + "very-long-directory/" * 20 + "target.json",
            SHARE_SOLE,
            "この構成のみが所有・既存を上書き",
            ACTION_SAVE,
        )
        dialog = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog([row], {})[0]
        try:
            dialog.deiconify()
            dialog.update()
            frame = dialog.winfo_children()[0]
            list_frame = next(
                widget
                for widget in frame.winfo_children()
                if isinstance(widget, ttk.Frame) and widget.pack_info().get("fill") == "both"
            )
            canvas = next(widget for widget in list_frame.winfo_children() if isinstance(widget, tkinter.Canvas))
            if canvas.winfo_width() <= 1:
                self.skipTest("ウィンドウマネージャーがないため、Canvas の実レイアウトを検証できません")
            content_frame = canvas.winfo_children()[0]
            name_label = content_frame.grid_slaves(row=0, column=1)[0]
            path_label = content_frame.grid_slaves(row=0, column=2)[0]
            minimum_width, minimum_height = dialog.minsize()

            dialog.geometry(f"{minimum_width}x{minimum_height}")
            dialog.update()
            narrow_text = (name_label.cget("text"), path_label.cget("text"))
            dialog.geometry(f"{minimum_width + 240}x{minimum_height}")
            dialog.update()
            wide_text = (name_label.cget("text"), path_label.cget("text"))

            self.assertEqual(wide_text[0], narrow_text[0])
            self.assertGreater(len(wide_text[1]), len(narrow_text[1]))
        finally:
            dialog.destroy()
            root.destroy()

    def test_mouse_wheel_on_row_child_scrolls_canvas(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        rows = [
            ChildSaveRow(CHILD_SEQUENCE, f"f{index}", f"Copy {index}", f"C:/copy-{index}.json", SHARE_SOLE, "単独", ACTION_SAVE)
            for index in range(30)
        ]
        dialog = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog(rows, {})[0]
        try:
            dialog.deiconify()
            dialog.update()
            frame = dialog.winfo_children()[0]
            list_frame = next(
                widget
                for widget in frame.winfo_children()
                if isinstance(widget, ttk.Frame) and widget.pack_info().get("fill") == "both"
            )
            canvas = next(widget for widget in list_frame.winfo_children() if isinstance(widget, tkinter.Canvas))
            if canvas.winfo_height() <= 1:
                self.skipTest("ウィンドウマネージャーがないため、Canvas の実レイアウトを検証できません")
            content_frame = canvas.winfo_children()[0]
            row_label = content_frame.grid_slaves(row=0, column=1)[0]
            before = canvas.yview()[0]

            row_label.event_generate("<MouseWheel>", delta=-120)
            dialog.update()

            self.assertGreater(canvas.yview()[0], before)
        finally:
            dialog.destroy()
            root.destroy()

    def test_mouse_wheel_binding_is_scoped_to_dialog(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        row = ChildSaveRow(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"), "Copy", "C:/copy.json", SHARE_SOLE, "単独", ACTION_SAVE)
        dialog = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog([row], {})[0]
        try:
            dialog.deiconify()
            dialog.update()
            frame = dialog.winfo_children()[0]
            list_frame = next(
                widget
                for widget in frame.winfo_children()
                if isinstance(widget, ttk.Frame) and widget.pack_info().get("fill") == "both"
            )
            canvas = next(widget for widget in list_frame.winfo_children() if isinstance(widget, tkinter.Canvas))
            content_frame = canvas.winfo_children()[0]
            row_label = content_frame.grid_slaves(row=0, column=1)[0]

            self.assertIn(str(dialog), row_label.bindtags())
            self.assertTrue(dialog.bind("<MouseWheel>"))
            self.assertFalse(root.bind_all("<MouseWheel>"))
            dialog.destroy()
            self.assertFalse(root.bind_all("<MouseWheel>"))
        finally:
            if dialog.winfo_exists():
                dialog.destroy()
            root.destroy()

    def test_sole_share_text_is_no_wider_than_shared_text(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        try:
            sole_text = share_text_for(SHARE_SOLE, 1)
            shared_text = share_text_for(SHARE_SHARED, 2)

            self.assertEqual(sole_text, "この構成のみが所有・既存を上書き")
            self.assertEqual(shared_text, "2 個の上位で共有中・全てに影響します")
            default_font = font.nametofont("TkDefaultFont")
            self.assertLessEqual(
                default_font.measure(sole_text),
                default_font.measure(shared_text),
            )
        finally:
            root.destroy()

    def test_minimum_size_keeps_buttons_and_radio_column_visible_in_real_tk(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        rows = [
            ChildSaveRow(
                CHILD_SEQUENCE,
                "f1",
                "長い対象名" * 8,
                "C:/" + "long-directory/" * 12 + "target.json",
                SHARE_SOLE,
                "この構成のみが所有・既存を上書き",
                ACTION_SAVE,
            )
        ]
        dialog = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog(rows, {})[0]
        try:
            dialog.deiconify()
            dialog.update()
            minimum_width, minimum_height = dialog.minsize()
            dialog.geometry(f"{minimum_width}x{minimum_height}")
            dialog.update()
            frame = dialog.winfo_children()[0]
            buttons = next(widget for widget in frame.winfo_children() if widget.pack_info()["side"] == "bottom")
            list_frame = next(widget for widget in frame.winfo_children() if widget is not buttons)
            canvas = next(widget for widget in list_frame.winfo_children() if isinstance(widget, tkinter.Canvas))
            content_frame = canvas.winfo_children()[0]
            actions = content_frame.grid_slaves(row=0, column=4)[0]
            name_label = content_frame.grid_slaves(row=0, column=1)[0]
            path_label = content_frame.grid_slaves(row=0, column=2)[0]
            narrow_widths = (name_label.winfo_width(), path_label.winfo_width())

            if canvas.winfo_width() <= 1:
                self.skipTest("ウィンドウマネージャーがないため、Canvas の実レイアウトを検証できません")
            self.assertLessEqual(buttons.winfo_y() + buttons.winfo_height(), dialog.winfo_height())
            self.assertLessEqual(actions.winfo_x() + actions.winfo_width(), canvas.winfo_width())

            dialog.geometry(f"{minimum_width + 240}x{minimum_height}")
            dialog.update()
            self.assertEqual(name_label.winfo_width(), narrow_widths[0])
            self.assertGreater(path_label.winfo_width(), narrow_widths[1])
        finally:
            dialog.destroy()
            root.destroy()

    def test_many_rows_open_at_screen_cap_and_can_scroll_in_real_tk(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        rows = [
            ChildSaveRow(
                CHILD_SEQUENCE,
                f"f{index}",
                f"Copy {index}",
                f"C:/copy-{index}.json",
                SHARE_SOLE,
                "単独",
                ACTION_SAVE,
            )
            for index in range(60)
        ]
        dialog = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog(rows, {})[0]
        try:
            dialog.deiconify()
            dialog.update()
            decoration = max(0, dialog.winfo_rooty() - dialog.winfo_y()) + max(
                0, dialog.winfo_rootx() - dialog.winfo_x()
            )
            self.assertLessEqual(
                dialog.winfo_height() + decoration,
                int(dialog.winfo_screenheight() * 0.6),
            )
            frame = dialog.winfo_children()[0]
            list_frame = next(
                widget
                for widget in frame.winfo_children()
                if isinstance(widget, ttk.Frame) and widget.pack_info().get("fill") == "both"
            )
            canvas = next(widget for widget in list_frame.winfo_children() if isinstance(widget, tkinter.Canvas))
            before = canvas.yview()[0]
            canvas.yview_moveto(1.0)
            dialog.update()
            self.assertGreater(canvas.yview()[0], before)
            columns = dialog._child_save_columns
            header_frame = columns.header_frame
            content = columns.content
            self.assertIs(header_frame.master, list_frame)
            self.assertIs(content.master, canvas)
            self.assertTrue(header_frame.winfo_viewable())
            self.assertTrue(all(handle.winfo_viewable() for handle in columns.handles))
            for column in range(5):
                header = header_frame.grid_slaves(row=0, column=column)[0]
                self.assertIs(header.master, header_frame)
                self.assertTrue(header.winfo_viewable())
            for handle in columns.handles:
                self.assertIs(handle.master, header_frame)
            self.assertEqual(len(rows), 60)
        finally:
            dialog.destroy()
            root.destroy()

    def test_header_handles_resize_adjacent_fixed_columns_and_preserve_selection(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        rows = [
            ChildSaveRow(
                CHILD_SEQUENCE,
                "f1",
                "Very long target name " * 5,
                "C:/long-directory/target.json",
                SHARE_SOLE,
                "この構成のみが所有・既存を上書き",
                ACTION_SAVE,
            )
        ] + [
            ChildSaveRow(
                CHILD_SEQUENCE,
                f"f{index}",
                f"Copy {index}",
                f"C:/copy-{index}.json",
                SHARE_SOLE,
                "単独",
                ACTION_SAVE,
            )
            for index in range(2, 61)
        ]
        dialog, choices = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog(rows, {})
        try:
            dialog.deiconify()
            dialog.update()
            columns = dialog._child_save_columns
            content = columns.content

            def assert_header_columns_aligned():
                header_frame = columns.header_frame
                for column in range(5):
                    header_box = header_frame.grid_bbox(column, 0, column, 0)
                    content_box = content.grid_bbox(column, 0, column, 0)
                    self.assertEqual(
                        header_frame.winfo_rootx() + header_box[0],
                        content.winfo_rootx() + content_box[0],
                    )
                    self.assertEqual(header_box[2], content_box[2])

            assert_header_columns_aligned()
            for column, full_text in (
                (0, child_save_dialog_module._kind_label(rows[0].kind)),
                (3, rows[0].share_text),
            ):
                self.assertEqual(content.grid_slaves(row=0, column=column)[0].cget("text"), full_text)
            dialog.geometry(f"{dialog.winfo_width() + 300}x{dialog.winfo_height()}")
            dialog.update()
            assert_header_columns_aligned()
            frame = dialog.winfo_children()[0]
            list_frame = next(
                widget
                for widget in frame.winfo_children()
                if isinstance(widget, ttk.Frame) and widget.pack_info().get("fill") == "both"
            )
            canvas = next(widget for widget in list_frame.winfo_children() if isinstance(widget, tkinter.Canvas))
            content = canvas.winfo_children()[0]
            canvas.yview_moveto(1.0)
            dialog.update()
            initial_scroll = canvas.yview()[0]
            self.assertGreater(initial_scroll, 0)
            self.assertTrue(columns.header_frame.winfo_viewable())
            self.assertTrue(all(handle.winfo_viewable() for handle in columns.handles))
            minimum_width = dialog.minsize()[0]

            def drag(handle, delta):
                start_x = handle.winfo_rootx() + 3
                start_y = handle.winfo_rooty() + 5
                for sequence, root_x in (
                    ("<ButtonPress-1>", start_x),
                    ("<B1-Motion>", start_x + delta),
                    ("<ButtonRelease-1>", start_x + delta),
                ):
                    handle.event_generate(
                        sequence,
                        x=root_x - handle.winfo_rootx(),
                        y=5,
                        rootx=root_x,
                        rooty=start_y,
                    )

            for handle_index, column, motion_x in ((0, 0, 27), (1, 1, 27), (2, 3, -21)):
                handle = columns.handles[handle_index]
                initial_width = content.grid_bbox(column, 0, column, 0)[2]
                initial_path = content.grid_bbox(2, 0, 2, 0)[2]
                delta = motion_x - 3
                drag(handle, delta)
                dialog.update()
                assert_header_columns_aligned()
                self.assertEqual(content.grid_bbox(column, 0, column, 0)[2], initial_width + abs(delta))
                self.assertEqual(content.grid_bbox(2, 0, 2, 0)[2], initial_path - abs(delta))
                self.assertAlmostEqual(canvas.yview()[0], initial_scroll, places=2)

            self.assertGreater(dialog.minsize()[0], minimum_width)
            self.assertEqual(choices[(CHILD_SEQUENCE, "f1")].get(), ACTION_SAVE)

            handle = columns.handles[0]
            drag(handle, -2003)
            dialog.update()
            self.assertEqual(columns.widths[0], columns.minimums[0])

            handle = columns.handles[1]
            drag(handle, -2003)
            dialog.update()
            self.assertEqual(columns.widths[1], columns.minimums[1])

            handle = columns.handles[2]
            drag(handle, 1997)
            dialog.update()
            self.assertEqual(columns.widths[3], columns.minimums[3])

            handle = columns.handles[0]
            drag(handle, 1997)
            dialog.update()
            path_minimum = columns.minimums[2]
            self.assertEqual(content.grid_bbox(2, 0, 2, 0)[2], path_minimum)
            stopped_width = columns.widths[0]
            drag(handle, 2197)
            dialog.update()
            self.assertEqual(columns.widths[0], stopped_width)

            current = {column: content.grid_bbox(column, 0, column, 0)[2] for column in range(5)}
            dialog.geometry(f"{dialog.winfo_width() + 160}x{dialog.winfo_height()}")
            dialog.update()
            assert_header_columns_aligned()
            expanded = {column: content.grid_bbox(column, 0, column, 0)[2] for column in range(5)}
            for column in (0, 1, 3, 4):
                self.assertEqual(expanded[column], current[column])
            self.assertGreater(expanded[2], current[2])
        finally:
            dialog.destroy()
            root.destroy()

    def test_narrow_kind_and_share_columns_ellipsize_and_enable_full_tooltips(self):
        try:
            root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        root.withdraw()
        share_text = "この構成のみが所有・既存を上書き"
        row = ChildSaveRow(
            CHILD_SEQUENCE,
            "f1",
            "Copy",
            "C:/copy.json",
            SHARE_SOLE,
            share_text,
            ACTION_SAVE,
        )
        tooltip_conditions = []
        real_bind_tooltip = child_save_dialog_module.bind_hover_tooltip

        def bind_tooltip(widget, text, should_show):
            tooltip_conditions.append((widget, text, should_show))
            real_bind_tooltip(widget, text, should_show)

        with patch.object(
            child_save_dialog_module,
            "bind_hover_tooltip",
            side_effect=bind_tooltip,
        ):
            dialog = child_save_dialog_module.ChildSaveDialog(root)._create_action_dialog([row], {})[0]
        try:
            dialog.deiconify()
            dialog.update()
            columns = dialog._child_save_columns
            content = columns.content
            type_label = content.grid_slaves(row=0, column=0)[0]
            share_label = content.grid_slaves(row=0, column=3)[0]

            for handle_index, delta in ((0, -2003), (2, 1997)):
                handle = columns.handles[handle_index]
                start_x = handle.winfo_rootx() + 3
                start_y = handle.winfo_rooty() + 5
                for sequence, root_x in (
                    ("<ButtonPress-1>", start_x),
                    ("<B1-Motion>", start_x + delta),
                    ("<ButtonRelease-1>", start_x + delta),
                ):
                    handle.event_generate(
                        sequence,
                        x=root_x - handle.winfo_rootx(),
                        y=5,
                        rootx=root_x,
                        rooty=start_y,
                    )
                dialog.update()

            full_kind = child_save_dialog_module._kind_label(row.kind)
            self.assertNotEqual(type_label.cget("text"), full_kind)
            self.assertNotEqual(share_label.cget("text"), share_text)
            conditions = {text(): should_show for _widget, text, should_show in tooltip_conditions}
            self.assertTrue(conditions[full_kind]())
            self.assertTrue(conditions[share_text]())
            for full_text in (full_kind, share_text):
                label = next(widget for widget, text, _show in tooltip_conditions if text() == full_text)
                label.event_generate(
                    "<Enter>",
                    x=1,
                    y=1,
                    rootx=label.winfo_rootx() + 1,
                    rooty=label.winfo_rooty() + 1,
                )
                dialog.update()
                tooltip = next(
                    widget
                    for widget in label.winfo_children()
                    if isinstance(widget, tkinter.Toplevel)
                )
                tooltip_text = next(
                    widget.cget("text")
                    for widget in tooltip.winfo_children()
                    if isinstance(widget, ttk.Label)
                )
                self.assertEqual(tooltip_text, full_text)
                label.event_generate("<Leave>")
                dialog.update()
        finally:
            dialog.destroy()
            root.destroy()

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

    def test_sequence_save_as_updates_trigger_set_index_for_new_and_existing_targets(self):
        for target_exists, requires_confirmation in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(target_exists=target_exists, requires_confirmation=requires_confirmation), tempfile.TemporaryDirectory() as root:
                path = self._prepare(root)
                targets = self._targets(path)
                previous_sequence_path = targets[(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"))]
                previous_sequence_bytes = open(previous_sequence_path, "rb").read()
                renamed_sequence = os.path.join(root, "renamed", "copy.json")
                if target_exists:
                    self.app.config_service.repository.save_json(
                        renamed_sequence,
                        {"label": "existing", "actions": []},
                    )
                if requires_confirmation:
                    self._replace_parent_refs(targets[(CHILD_TRIGGER_SET, "km1")], [])
                get_active_triggers(self.app.data)[0]["actions"] = [
                    {"type": "text", "value": "new", "label": ""}
                ]
                self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
                choices = {(CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, renamed_sequence)}

                with patch.object(
                    self.app.child_save_dialog, "ask_child_save_actions", return_value=choices
                ), patch.object(
                    self.app.child_save_dialog,
                    "confirm_trigger_set_dependency",
                    return_value=ACTION_SAVE,
                ) as confirm:
                    self.assertTrue(self._save(path))

                if requires_confirmation:
                    confirm.assert_called_once()
                else:
                    confirm.assert_not_called()
                self.assertTrue(os.path.exists(renamed_sequence))
                if target_exists:
                    self.assertEqual(
                        self.app.config_service.repository.load_json(renamed_sequence)["actions"],
                        [{"type": "text", "value": "new", "label": ""}],
                    )
                self.assertEqual(open(previous_sequence_path, "rb").read(), previous_sequence_bytes)
                trigger_set = self.app.config_service.repository.load_json(
                    targets[(CHILD_TRIGGER_SET, "km1")]
                )
                self.assertEqual(
                    trigger_set["triggers"][0]["sequence_path"],
                    self.app.config_service.to_config_relative_or_absolute(renamed_sequence, root),
                )

    def test_sole_and_new_trigger_set_dependencies_are_saved_without_confirmation(self):
        for share_state in (SHARE_SOLE, SHARE_NEW):
            with self.subTest(share_state=share_state), tempfile.TemporaryDirectory() as root:
                path = self._prepare(root)
                trigger_set_path = self._targets(path)[(CHILD_TRIGGER_SET, "km1")]
                if share_state == SHARE_NEW:
                    os.remove(trigger_set_path)
                    self.app.data["keymaps"][0].pop(self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH, None)
                self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
                renamed_sequence = os.path.join(root, "renamed", "copy.json")
                choices = {
                    (CHILD_TRIGGER_SET, "km1"): (ACTION_SAVE, ""),
                    (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (
                        ACTION_SAVE_AS,
                        renamed_sequence,
                    )
                }
                with patch.object(
                    self.app.child_save_dialog, "ask_child_save_actions", return_value=choices
                ), patch.object(
                    self.app.child_save_dialog, "confirm_trigger_set_dependency"
                ) as confirm, patch.object(self.app, "_set_flash_message") as flash:
                    self.assertTrue(self._save(path))

                confirm.assert_not_called()
                if share_state == SHARE_SOLE:
                    self.assertIn("トリガー一覧も保存して索引を更新しました。", flash.call_args.args[0])
                else:
                    self.assertTrue(os.path.exists(trigger_set_path))
                    trigger_set = self.app.config_service.repository.load_json(
                        trigger_set_path
                    )
                    self.assertEqual(
                        trigger_set["triggers"][0]["sequence_path"],
                        self.app.config_service.to_config_relative_or_absolute(
                            renamed_sequence, root
                        ),
                    )

    def test_unsourced_trigger_set_can_be_explicitly_saved_without_dependency_confirmation(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            trigger_set_path = self._targets(path)[(CHILD_TRIGGER_SET, "km1")]
            self.assertTrue(os.path.exists(trigger_set_path))
            self.assertEqual(
                self.app.config_service.repository.load_json(trigger_set_path)["_parent_refs"],
                ["user/keymaps/Main.json"],
            )
            self.app.data["keymaps"][0].pop(self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH, None)
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            choices = {
                (CHILD_TRIGGER_SET, "km1"): (ACTION_SAVE, ""),
                (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (
                    ACTION_SAVE_AS,
                    os.path.join(root, "renamed", "copy.json"),
                )
            }
            with patch.object(
                self.app.child_save_dialog, "ask_child_save_actions", return_value=choices
            ), patch.object(
                self.app.child_save_dialog, "confirm_trigger_set_dependency", return_value=ACTION_SAVE
            ) as confirm:
                self.assertTrue(self._save(path))

            confirm.assert_not_called()

    def test_nonsole_trigger_set_dependencies_open_four_choice_confirmation(self):
        for share_state in (SHARE_UNKNOWN, SHARE_OTHER_PARENT, SHARE_SHARED):
            with self.subTest(share_state=share_state), tempfile.TemporaryDirectory() as root:
                path = self._prepare(root)
                trigger_set_path = self._targets(path)[(CHILD_TRIGGER_SET, "km1")]
                if share_state == SHARE_UNKNOWN:
                    self._replace_parent_refs(trigger_set_path, [])
                elif share_state == SHARE_OTHER_PARENT:
                    self._replace_parent_refs(trigger_set_path, ["user/keymap_sets/other.json"])
                elif share_state == SHARE_SHARED:
                    self._replace_parent_refs(
                        trigger_set_path,
                        ["user/keymaps/Main.json", "user/keymaps/other.json"],
                    )
                self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
                choices = {
                    (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (
                        ACTION_SAVE_AS,
                        os.path.join(root, "renamed", "copy.json"),
                    )
                }
                with patch.object(
                    self.app.child_save_dialog, "ask_child_save_actions", return_value=choices
                ), patch.object(
                    self.app.child_save_dialog,
                    "confirm_trigger_set_dependency",
                    return_value=ACTION_SAVE,
                ) as confirm:
                    self.assertTrue(self._save(path))

                confirm.assert_called_once()

    def test_deferred_index_marks_trigger_set_dirty_after_save(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            self._replace_parent_refs(self._targets(path)[(CHILD_TRIGGER_SET, "km1")], [])
            self.assertFalse(self.app.dirty_tracker.trigger_set_dirty)
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            choices = {
                (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, os.path.join(root, "renamed", "copy.json"))
            }
            with patch.object(
                self.app.child_save_dialog, "ask_child_save_actions", return_value=choices
            ), patch.object(
                self.app.child_save_dialog,
                "confirm_trigger_set_dependency",
                return_value=ACTION_SKIP,
            ), patch.object(
                self.app.config_service,
                "save_runtime_data",
                wraps=self.app.config_service.save_runtime_data,
            ) as save:
                self.assertTrue(self._save(path))

            self.assertTrue(save.call_args.kwargs["save_plan"].allow_deferred_index)
            self.assertTrue(self.app.dirty_tracker.trigger_set_dirty)

    def test_dependency_dialog_passes_save_as_button_to_grab_modal(self):
        # grab_modal ごとモック化し偽ウィジェットで回すため、実 OS フォーカスに依存しない
        # （= skip ガードを付けない）。固定するのはビルダ戻り値が focus 引数まで届くことだけ。
        row = ChildSaveRow(
            CHILD_TRIGGER_SET, "km1", "トリガー一覧", "C:/trigger.json", SHARE_UNKNOWN, "所有元不明", ACTION_SAVE_AS
        )
        with patch.object(child_save_dialog_module, "grab_modal") as grab_modal:
            _result, _dialog, buttons = self._ask_dependency_internally(
                row, lambda dialog: dialog.buttons["キャンセル"]()
            )

        grab_modal.assert_called_once()
        self.assertIs(grab_modal.call_args.kwargs["focus"], buttons["別名保存"])

    def test_dependency_dialog_defaults_to_save_as_and_escape_or_close_cancels(self):
        row = ChildSaveRow(
            CHILD_TRIGGER_SET, "km1", "トリガー一覧", "C:/trigger.json", SHARE_UNKNOWN, "所有元不明", ACTION_SAVE_AS
        )
        for close in (
            lambda dialog: dialog.bindings["<Escape>"](None),
            lambda dialog: dialog.protocols["WM_DELETE_WINDOW"](),
        ):
            with self.subTest(close=close):
                result, dialog, buttons = self._ask_dependency_internally(row, close)
                self.assertEqual(result, "")
                self.assertTrue(dialog.destroyed)
                self.assertTrue(buttons["別名保存"].focused)

    def test_new_child_collision_defaults_to_save_as_without_overwriting(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            sequence_path = self._targets(path)[(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"))]
            before = open(sequence_path, "rb").read()
            get_active_triggers(self.app.data)[0].pop(
                self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH,
                None,
            )
            renamed_sequence = os.path.join(root, "renamed", "copy.json")
            get_active_triggers(self.app.data)[0]["actions"] = [
                {"type": "text", "value": "new", "label": ""}
            ]
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])

            def choose(rows):
                row = rows[0]
                self.assertEqual(row.share_state, SHARE_NEW_COLLIDES)
                self.assertEqual(row.share_text, "同名の既存ファイルあり・安全のため別名")
                self.assertEqual(row.default_action, ACTION_SAVE_AS)
                return {(CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, renamed_sequence)}

            with patch.object(
                self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose
            ), patch.object(
                self.app.child_save_dialog, "confirm_trigger_set_dependency", return_value=ACTION_SAVE
            ) as confirm:
                self.assertTrue(self._save(path))

            confirm.assert_not_called()
            self.assertEqual(open(sequence_path, "rb").read(), before)
            self.assertEqual(
                self.app.config_service.repository.load_json(renamed_sequence)["actions"],
                [{"type": "text", "value": "new", "label": ""}],
            )

    def test_dirty_choices_control_overwrite_save_as_and_skip(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root, second_sequence=True)
            targets = self._targets(path)
            renamed_sequence = os.path.join(root, "renamed", "copy.json")
            old_sequence = open(targets[(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"))], "rb").read()
            old_skipped_sequence = open(targets[(CHILD_SEQUENCE, compose_sequence_key("km1", "f2"))], "rb").read()
            self.app.data["keymaps"][0]["mappings"] = {"a": "c"}
            get_active_triggers(self.app.data)[0]["actions"] = [{"type": "text", "value": "new", "label": ""}]
            self.app.dirty_tracker.mark_keymap_dirty(self.app.data["keymaps"][0])
            self.app.dirty_tracker.mark_trigger_set_dirty()
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[1])
            choices = {
                (CHILD_KEYMAP, "km1"): (ACTION_SAVE, ""),
                (CHILD_TRIGGER_SET, "km1"): (ACTION_SAVE, ""),
                (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, renamed_sequence),
                (CHILD_SEQUENCE, compose_sequence_key("km1", "f2")): (ACTION_SKIP, ""),
            }
            def choose(rows):
                self.assertEqual(
                    [(row.kind, row.key) for row in rows],
                    [
                        (CHILD_KEYMAP, "km1"),
                        (CHILD_TRIGGER_SET, "km1"),
                        (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")),
                        (CHILD_SEQUENCE, compose_sequence_key("km1", "f2")),
                    ],
                )
                return choices

            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose) as ask:
                self.assertTrue(self._save(path))

            ask.assert_called_once()
            self.assertTrue(os.path.exists(renamed_sequence))
            self.assertEqual(open(targets[(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"))], "rb").read(), old_sequence)
            self.assertEqual(open(targets[(CHILD_SEQUENCE, compose_sequence_key("km1", "f2"))], "rb").read(), old_skipped_sequence)

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
            self.app.data["keymaps"][0][
                self.app.config_service.INTERNAL_KEYMAP_SOURCE_PATH
            ] = self.app.config_service.to_config_relative_or_absolute(
                keymap_path,
                self.app.config_root,
            )
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
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            choices = {(CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, renamed_sequence)}
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", return_value=choices), patch.object(
                self.app.child_save_dialog, "confirm_trigger_set_dependency", return_value=ACTION_SAVE
            ) as confirm:
                self.assertTrue(self._save(path))

            confirm.assert_not_called()
            self.assertTrue(os.path.exists(renamed_sequence))

    def test_dependency_save_as_keeps_confirmed_trigger_set_target(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            self._replace_parent_refs(targets[(CHILD_TRIGGER_SET, "km1")], [])
            old_trigger_bytes = open(targets[(CHILD_TRIGGER_SET, "km1")], "rb").read()
            renamed_sequence = os.path.join(root, "renamed", "copy.json")
            renamed_trigger_set = os.path.join(root, "renamed", "trigger_set.json")
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            choices = {(CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, renamed_sequence)}

            def confirm(**_kwargs):
                self.app.child_save_dialog.trigger_set_save_as_path = renamed_trigger_set
                return ACTION_SAVE_AS

            with patch.object(
                self.app.child_save_dialog,
                "ask_child_save_actions",
                return_value=choices,
            ) as ask, patch.object(
                self.app.child_save_dialog,
                "confirm_trigger_set_dependency",
                side_effect=confirm,
            ) as dependency:
                self.assertTrue(self._save(path))

            self.assertEqual(ask.call_count, 1)
            dependency.assert_called_once()
            self.assertEqual(open(targets[(CHILD_TRIGGER_SET, "km1")], "rb").read(), old_trigger_bytes)
            self.assertTrue(os.path.exists(renamed_trigger_set))

    def test_dependency_reselect_then_cancel_keeps_all_files_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            targets = self._targets(path)
            self._replace_parent_refs(targets[(CHILD_TRIGGER_SET, "km1")], [])
            before = {path: open(path, "rb").read(), **{value: open(value, "rb").read() for value in targets.values()}}
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            choices = {(CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, os.path.join(root, "renamed.json"))}
            with patch.object(
                self.app.child_save_dialog, "ask_child_save_actions", side_effect=[choices, None]
            ) as ask, patch.object(
                self.app.child_save_dialog, "confirm_trigger_set_dependency", return_value=""
            ) as confirm:
                self.assertFalse(self._save(path))

            self.assertEqual(ask.call_count, 2)
            confirm.assert_called_once()
            self.assertEqual({name: open(name, "rb").read() for name in before}, before)

    def test_dependency_reselect_with_unsourced_sequence_cancels_save(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            trigger = get_active_triggers(self.app.data)[0]
            trigger["label"] = "Renamed"
            trigger.pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            self._replace_parent_refs(self._targets(path)[(CHILD_TRIGGER_SET, "km1")], [])
            with patch.object(self.app.child_save_dialog, "ask_child_save_actions") as ask, patch.object(
                self.app.child_save_dialog,
                "confirm_trigger_set_dependency",
                return_value="",
            ) as confirm:
                ask.side_effect = [
                    {
                        (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE, ""),
                    },
                    None,
                ]
                self.assertIsNone(self.app.keymap_set_io._collect_child_save_plan(path, "")[0])

            self.assertEqual(ask.call_count, 2)
            confirm.assert_called_once()

    def test_skipped_sequence_does_not_require_dependency_confirmation(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root)
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            choices = {(CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SKIP, "")}
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
            get_active_triggers(self.app.data)[0].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            get_active_triggers(self.app.data)[1].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            self.app.dirty_tracker.mark_trigger_set_dirty()
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            seen_sequence_targets = []
            save_as_sequence = os.path.join(root, "external", "sequences", "saved-other.json")

            def choose(rows):
                sequence_row = next(row for row in rows if row.kind == CHILD_SEQUENCE)
                seen_sequence_targets.append(sequence_row.target_path)
                trigger_action = ACTION_SAVE_AS
                trigger_target = external_trigger_set
                return {
                    (CHILD_TRIGGER_SET, "km1"): (trigger_action, trigger_target),
                    (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE, ""),
                    (CHILD_SEQUENCE, compose_sequence_key("km1", "f2")): (ACTION_SAVE_AS, save_as_sequence),
                }

            with patch.object(self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose) as ask, patch.object(
                self.app.child_save_dialog,
                "_ask_save_as_path",
                side_effect=AssertionError("明示済みの別名保存先を再選択しない"),
            ) as ask_save_as:
                self.assertTrue(self._save(path))

            saved_sequence_path = get_active_triggers(self.app.data)[0][
                self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH
            ]
            self.assertEqual(ask.call_count, 1)
            ask_save_as.assert_not_called()
            self.assertNotEqual(seen_sequence_targets[0], saved_sequence_path)
            # source_path は config_root 内なら相対で入るため root と結合してから存在確認する
            self.assertTrue(os.path.exists(os.path.join(root, saved_sequence_path)))
            self.assertTrue(os.path.exists(save_as_sequence))
            self.assertEqual(open(external_other, "rb").read(), b"existing other")

    def test_recalculated_overwrite_confirmation_handles_yes_no_and_cancel(self):
        for decision in ("yes", "no", "cancel"):
            with self.subTest(decision=decision), tempfile.TemporaryDirectory() as root:
                path = self._prepare(root, second_sequence=True)
                external_trigger_set = os.path.join(root, "external", "trigger_set.json")
                recalculated_sequence = os.path.join(root, "external", "sequences", "copy.json")
                external_other = os.path.join(root, "external", "sequences", "other.json")
                renamed_sequence = os.path.join(root, "renamed", "copy.json")
                renamed_other_sequence = os.path.join(root, "renamed", "other.json")
                os.makedirs(os.path.dirname(recalculated_sequence), exist_ok=True)
                # _parent_refs を後から差し込むため、既存ファイルは妥当な JSON にしておく
                self.app.config_service.repository.save_json(
                    recalculated_sequence, {"label": "existing copy", "actions": []}
                )
                with open(external_other, "wb") as stream:
                    stream.write(b"existing other")
                self._replace_parent_refs(
                    recalculated_sequence,
                    ["user/trigger_sets/other.json"],
                )
                get_active_triggers(self.app.data)[0].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
                get_active_triggers(self.app.data)[1].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
                get_active_triggers(self.app.data)[0]["actions"] = [{"type": "text", "value": "new", "label": ""}]
                self.app.dirty_tracker.mark_trigger_set_dirty()
                self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
                choices = {
                    (CHILD_TRIGGER_SET, "km1"): (ACTION_SAVE_AS, external_trigger_set),
                    (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE, ""),
                    (CHILD_SEQUENCE, compose_sequence_key("km1", "f2")): (ACTION_SAVE_AS, renamed_other_sequence),
                }
                replacements = {
                    "yes": {},
                    "no": {(CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE_AS, renamed_sequence)},
                    "cancel": None,
                }[decision]
                before_parent = open(path, "rb").read()
                before_sequence = open(recalculated_sequence, "rb").read()

                with patch.object(
                    self.app.child_save_dialog, "ask_child_save_actions", return_value=choices
                ), patch.object(
                    self.app.child_save_dialog,
                    "confirm_recalculated_overwrite",
                    return_value=replacements,
                ) as confirm, patch.object(
                    self.app.child_save_dialog,
                    "_ask_save_as_path",
                    side_effect=AssertionError("明示済みの別名保存先を再選択しない"),
                ) as ask_save_as:
                    self.assertEqual(self._save(path), decision != "cancel")

                confirm.assert_called_once()
                ask_save_as.assert_not_called()
                confirmed_rows = confirm.call_args.args[0]
                self.assertEqual(
                    [(row.kind, row.key) for row in confirmed_rows],
                    [(CHILD_SEQUENCE, compose_sequence_key("km1", "f1"))],
                )
                self.assertEqual(confirmed_rows[0].default_action, ACTION_SAVE_AS)
                if decision == "yes":
                    self.assertNotEqual(open(recalculated_sequence, "rb").read(), before_sequence)
                    self.assertTrue(os.path.exists(renamed_other_sequence))
                elif decision == "no":
                    self.assertEqual(open(recalculated_sequence, "rb").read(), before_sequence)
                    self.assertTrue(os.path.exists(renamed_sequence))
                    self.assertTrue(os.path.exists(renamed_other_sequence))
                else:
                    self.assertEqual(open(path, "rb").read(), before_parent)
                    self.assertEqual(open(recalculated_sequence, "rb").read(), before_sequence)
                    self.assertFalse(os.path.exists(renamed_other_sequence))
                self.assertEqual(open(external_other, "rb").read(), b"existing other")

    def test_recalculated_overwrite_is_not_confirmed_for_new_target(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._prepare(root, second_sequence=True)
            external_trigger_set = os.path.join(root, "external", "trigger_set.json")
            external_other = os.path.join(root, "external", "sequences", "other.json")
            os.makedirs(os.path.dirname(external_other), exist_ok=True)
            with open(external_other, "wb") as stream:
                stream.write(b"existing other")
            get_active_triggers(self.app.data)[0].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            get_active_triggers(self.app.data)[1].pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH, None)
            self.app.dirty_tracker.mark_trigger_set_dirty()
            self.app.dirty_tracker.mark_sequence_dirty(get_active_triggers(self.app.data)[0])
            save_as_sequence = os.path.join(root, "external", "sequences", "saved-other.json")
            choices = {
                (CHILD_TRIGGER_SET, "km1"): (ACTION_SAVE_AS, external_trigger_set),
                (CHILD_SEQUENCE, compose_sequence_key("km1", "f1")): (ACTION_SAVE, ""),
                (CHILD_SEQUENCE, compose_sequence_key("km1", "f2")): (ACTION_SAVE_AS, save_as_sequence),
            }

            with patch.object(
                self.app.child_save_dialog, "ask_child_save_actions", return_value=choices
            ), patch.object(self.app.child_save_dialog, "confirm_recalculated_overwrite") as confirm, patch.object(
                self.app.child_save_dialog,
                "_ask_save_as_path",
                side_effect=AssertionError("明示済みの別名保存先を再選択しない"),
            ) as ask_save_as:
                self.assertTrue(self._save(path))

            confirm.assert_not_called()
            ask_save_as.assert_not_called()
            self.assertTrue(os.path.exists(save_as_sequence))
            self.assertEqual(open(external_other, "rb").read(), b"existing other")

    def test_recalculated_overwrite_dialog_uses_safe_default(self):
        row = ChildSaveRow(
            CHILD_SEQUENCE,
            "f1",
            "Copy",
            "C:/copy.json",
            SHARE_OTHER_PARENT,
            "別の構成に属します",
            ACTION_SAVE,
        )
        with patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "confirm_recalculated_overwrite",
            _REAL_CONFIRM_RECALCULATED_OVERWRITE,
        ), patch.object(self.app.hook, "suspend_hook_for_dialog"), patch.object(
            self.app.hook, "resume_hook_after_dialog"
        ), patch.object(tkinter.messagebox, "askyesnocancel", return_value=None) as ask:
            self.assertIsNone(self.app.child_save_dialog.confirm_recalculated_overwrite([row]))

        self.assertEqual(ask.call_args.kwargs["default"], tkinter.messagebox.NO)

    def test_dependency_dialog_returns_save_save_as_and_skip_actions(self):
        row = ChildSaveRow(
            CHILD_TRIGGER_SET, "km1", "トリガー一覧", "C:/trigger.json", SHARE_UNKNOWN, "所有元不明", ACTION_SAVE_AS
        )
        cases = (
            ("保存", ACTION_SAVE, ""),
            ("別名保存", ACTION_SAVE_AS, "C:/renamed.json"),
            ("別名保存", "", ""),
            ("保存しない", ACTION_SKIP, ""),
        )
        for button, expected, save_as_path in cases:
            with self.subTest(button=button):
                result, _dialog, buttons = self._ask_dependency_internally(
                    row,
                    lambda dialog, _button=button: dialog.buttons[_button](),
                    save_as_path=save_as_path,
                )
                self.assertEqual(result, expected)
                self.assertEqual(
                    set(buttons),
                    {"保存", "別名保存", "保存しない", "キャンセル"},
                )


    def test_trigger_set_save_as_resolves_keymap_dependency_and_deferral(self):
        for action in (ACTION_SAVE, ACTION_SKIP):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as root:
                path = self._prepare(root)
                targets = self._targets(path)
                keymap_path = targets[(CHILD_KEYMAP, "km1")]
                self._replace_parent_refs(keymap_path, [])
                before = open(keymap_path, "rb").read()
                target = os.path.join(root, "renamed", "list.json")
                self.app.dirty_tracker.mark_trigger_set_dirty()
                choices = {(CHILD_TRIGGER_SET, "km1"): (ACTION_SAVE_AS, target)}
                with patch.object(self.app.child_save_dialog, "ask_child_save_actions", return_value=choices), patch.object(
                    self.app.child_save_dialog, "confirm_trigger_set_dependency", return_value=action,
                ) as confirm:
                    self.assertTrue(self._save(path))
                confirm.assert_called_once()
                self.assertEqual(confirm.call_args.kwargs["trigger_set_row"].kind, CHILD_KEYMAP)
                self.assertEqual(confirm.call_args.kwargs["trigger_set_row"].key, "km1")
                self.assertTrue(os.path.exists(target))
                if action == ACTION_SKIP:
                    self.assertEqual(open(keymap_path, "rb").read(), before)
                    self.assertTrue(self.app.data["keymaps"][0]["_keymap_dirty"])
                else:
                    self.assertEqual(self.app.config_service.repository.load_json(keymap_path)["trigger_set_path"], "renamed/list.json")
                    self.assertFalse(self.app.data["keymaps"][0]["_keymap_dirty"])

if __name__ == "__main__":
    unittest.main()
