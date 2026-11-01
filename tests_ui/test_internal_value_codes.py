import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.shared.i18n import fix_language

fix_language("ja")

from keyseq.domain.sequence_control import OP_COUNTER_INC, OUT_OF_RANGE_WRAP
from keyseq.presentation.dialogs.action_key_hold_fields import ActionKeyHoldFields
from keyseq.presentation.dialogs.action_control_fields import ActionControlFields
from keyseq.presentation.dialogs.action_control_fields import _system_labels, _out_of_range_labels
from keyseq.presentation.dialogs.action_mouse_scroll_fields import ActionMouseScrollFields
from keyseq.presentation.controllers.keymap_panel.keymap_add_flow import KeymapAddFlow
from keyseq.presentation.controllers.trigger_panel.trigger_panel_controller import TriggerPanelController


class InternalValueCodesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_dialog_label_functions_translate_at_call_time(self):
        cases = (
            ("keyseq.presentation.dialogs.action_control_fields.tr", _system_labels),
            ("keyseq.presentation.dialogs.action_control_fields.tr", _out_of_range_labels),
            ("keyseq.presentation.dialogs.action_key_hold_fields.tr", ActionKeyHoldFields._target_labels),
            ("keyseq.presentation.dialogs.action_key_hold_fields.tr", ActionKeyHoldFields._edge_labels),
            ("keyseq.presentation.dialogs.action_key_hold_fields.tr", ActionKeyHoldFields._button_labels),
            ("keyseq.presentation.dialogs.action_mouse_scroll_fields.tr", ActionMouseScrollFields._direction_labels),
        )
        for target, labels in cases:
            original = labels()
            with self.subTest(labels=labels.__name__), patch(target, side_effect=lambda key: f"translated:{key}"):
                translated = labels()
                self.assertEqual(translated.keys(), original.keys())
                self.assertTrue(all(value.startswith("translated:") for value in translated.values()))
                self.assertEqual(len(set(translated.values())), len(translated))

    def test_key_hold_codes_survive_changed_labels(self):
        with patch.object(ActionKeyHoldFields, "_target_labels", return_value={"key": "Key", "mouse_button": "Mouse"}), \
             patch.object(ActionKeyHoldFields, "_edge_labels", return_value={"down": "Press", "up": "Release"}), \
             patch.object(ActionKeyHoldFields, "_button_labels",
                          return_value={"left": "Left", "right": "Right", "middle": "Middle"}):
            fields = ActionKeyHoldFields(self.root, capture_mouse_position=Mock())
            fields.target_var.set("Mouse")
            fields.edge_var.set("Release")
            fields.button_var.set("Right")
            self.assertEqual(fields.target_kind(), "mouse_button")
            self.assertEqual(fields.build_action("x"), {"type": "key_hold", "edge": "up", "button": "right", "label": "x"})
            fields.frame.destroy()

    def test_control_operation_and_range_codes_survive_changed_labels(self):
        with patch("keyseq.presentation.dialogs.action_control_fields._system_labels",
                   return_value={OP_COUNTER_INC: "Counter", "loop_start": "Loop"}), \
             patch("keyseq.presentation.dialogs.action_control_fields._out_of_range_labels",
                   return_value={OUT_OF_RANGE_WRAP: "Wrap"}), \
             patch("keyseq.presentation.dialogs.action_control_fields.messagebox.showerror",
                   side_effect=AssertionError("unexpected input error")):
            fields = ActionControlFields(self.root, counter_names=[], config_root="", config_service=Mock(), mode=None)
            fields.system_op_var.set("Counter")
            fields.system_counter_var.set("c1")
            self.assertEqual(fields.build_result("system", "x")["op"], OP_COUNTER_INC)
            fields.file_path_var.set("lines.txt")
            fields.file_counter_var.set("c1")
            fields.out_of_range_var.set("Wrap")
            self.assertEqual(fields._build_file_result("x")["out_of_range"], OUT_OF_RANGE_WRAP)
            fields.system_frame.destroy()
            fields.file_frame.destroy()

    def test_mouse_scroll_direction_survives_changed_labels(self):
        with patch.object(ActionMouseScrollFields, "_direction_labels",
                          return_value={"up": "Up", "down": "Down", "left": "Left", "right": "Right"}):
            fields = ActionMouseScrollFields(self.root, capture_mouse_position=Mock())
            fields.direction_var.set("Left")
            self.assertEqual(fields.build_action("x")["direction"], "left")
            fields.frame.destroy()

    def test_keymap_kind_labels_and_rows(self):
        fake_panel = SimpleNamespace(
            _app=SimpleNamespace(),
            format_keymap_display_name=lambda item: item.get("id", ""),
        )
        with patch("keyseq.presentation.controllers.keymap_panel.keymap_add_flow._kind_row_labels",
                   return_value={"new": "Create", "load": "Load", "paste": "Paste"}), \
             patch("keyseq.presentation.controllers.keymap_panel.keymap_add_flow.tr",
                   side_effect=lambda key: "new" if key == "keymap_panel.add.existing" else key):
            flow = KeymapAddFlow(fake_panel)
            rows = flow._make_rows("new", [{"id": "old", "label": ""}], [{"id": "km1", "label": ""}])
            self.assertEqual([row[0] for row in rows], ["new", "Create"])

    def test_empty_selection_summary_does_not_depend_on_display_label(self):
        controller = TriggerPanelController.__new__(TriggerPanelController)
        controller._app = SimpleNamespace(
            _find_trigger_by_key=Mock(return_value=None), _indices={},
        )
        controller.selected_trigger_is_effective = lambda: True
        self.assertEqual(controller.get_next_action_summary(""), "（なし）")
