import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.config_service import ConfigService
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.config_paths import ConfigPaths
from keyseq.presentation.controllers.layout_controller import LayoutController


class LayoutControllerRegistrationTest(unittest.TestCase):
    def test_registration_stores_config_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_root = os.path.join(tmp, "config")
            layout_path = str(Path(config_root) / "user" / "keylayout" / "jis.json")
            paths = ConfigPaths(
                base_dir=tmp,
                config_root=config_root,
                user_root=os.path.join(tmp, "user"),
                config_service=ConfigService(JsonRepository()),
            )
            app = SimpleNamespace(
                data={"external_keyboard_layouts": []},
                base_dir=tmp,
                paths=paths,
                _set_flash_message=Mock(),
            )
            controller = LayoutController.__new__(LayoutController)
            controller._app = app
            controller.keyboard_layouts_dir = ""
            controller._keyboard_layout_entries = {}
            controller.reload_keyboard_layouts = Mock()
            controller.persist_keyboard_layout_selection = Mock()

            with patch(
                "keyseq.presentation.controllers.layout_controller.filedialog.askopenfilename",
                return_value=layout_path,
            ), patch(
                "keyseq.presentation.controllers.layout_controller.load_layout_from_json",
                return_value=SimpleNamespace(layout_id="jis"),
            ):
                controller.add_external_keyboard_layout()

            self.assertEqual(
                app.data["external_keyboard_layouts"],
                [{"path": "user/keylayout/jis.json"}],
            )
            controller.reload_keyboard_layouts.assert_called_once_with()
            controller.persist_keyboard_layout_selection.assert_called_once_with()

    def test_registration_stores_outside_config_path_as_absolute_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_root = os.path.join(tmp, "config")
            layout_path = os.path.join(tmp, "outside", "jis.json")
            paths = ConfigPaths(
                base_dir=tmp,
                config_root=config_root,
                user_root=os.path.join(tmp, "user"),
                config_service=ConfigService(JsonRepository()),
            )
            app = SimpleNamespace(
                data={"external_keyboard_layouts": []},
                base_dir=tmp,
                paths=paths,
                _set_flash_message=Mock(),
            )
            controller = LayoutController.__new__(LayoutController)
            controller._app = app
            controller.keyboard_layouts_dir = ""
            controller._keyboard_layout_entries = {}
            controller.reload_keyboard_layouts = Mock()
            controller.persist_keyboard_layout_selection = Mock()

            with patch(
                "keyseq.presentation.controllers.layout_controller.filedialog.askopenfilename",
                return_value=layout_path,
            ), patch(
                "keyseq.presentation.controllers.layout_controller.load_layout_from_json",
                return_value=SimpleNamespace(layout_id="jis"),
            ):
                controller.add_external_keyboard_layout()

            self.assertEqual(
                app.data["external_keyboard_layouts"],
                [{"path": os.path.abspath(layout_path).replace("\\", "/")}],
            )
            controller.reload_keyboard_layouts.assert_called_once_with()
            controller.persist_keyboard_layout_selection.assert_called_once_with()


class LayoutControllerRefreshListsTest(unittest.TestCase):
    def _controller(self):
        panel = SimpleNamespace(refresh_triggers=Mock(), refresh_actions=Mock())
        app = SimpleNamespace(
            data={"keyboard_layout": "default", "external_keyboard_layouts": []},
            trigger_panel=panel,
            ui_vars=SimpleNamespace(keyboard_layout_var=Mock()),
            paths=SimpleNamespace(config_root=""),
            _set_flash_message=Mock(),
        )
        controller = LayoutController.__new__(LayoutController)
        controller._app = app
        controller.keyboard_layout_id = "default"
        controller._keyboard_layout_entries = {
            "default": SimpleNamespace(
                source="builtin",
                path=None,
                layout=SimpleNamespace(display_name="Default"),
            ),
            "external": SimpleNamespace(
                source="external",
                path="external.json",
                layout=SimpleNamespace(display_name="External"),
            ),
        }
        controller._keyboard_layout_display_to_id = {"Default": "default"}
        controller._keyboard_layout_id_to_display = {"default": "Default"}
        controller._layout_combos = []
        controller.refresh_keyboard_window = Mock()
        controller._refresh_active_layout = Mock()
        controller.reload_keyboard_layouts = Mock()
        controller.persist_keyboard_layout_selection = Mock(return_value=True)
        return controller

    def _assert_refreshed_once(self, panel):
        panel.refresh_triggers.assert_called_once_with()
        panel.refresh_actions.assert_called_once_with()

    def test_set_selection_refreshes_before_failed_persist(self):
        controller = self._controller()
        controller.persist_keyboard_layout_selection.return_value = False

        result = controller.set_keyboard_layout_selection("external", persist=True)

        self.assertFalse(result)
        self._assert_refreshed_once(controller._app.trigger_panel)

    def test_set_selection_refreshes_without_persist(self):
        controller = self._controller()

        result = controller.set_keyboard_layout_selection("default")

        self.assertTrue(result)
        controller.persist_keyboard_layout_selection.assert_not_called()
        self._assert_refreshed_once(controller._app.trigger_panel)

    def test_set_selection_refreshes_after_successful_persist(self):
        controller = self._controller()

        result = controller.set_keyboard_layout_selection("default", persist=True)

        self.assertTrue(result)
        controller.persist_keyboard_layout_selection.assert_called_once_with()
        self._assert_refreshed_once(controller._app.trigger_panel)

    def test_dropdown_selection_refreshes_after_reload(self):
        controller = self._controller()
        controller._app.ui_vars.keyboard_layout_var.get = Mock(return_value="Default")

        controller.on_keyboard_layout_selected()

        controller.reload_keyboard_layouts.assert_called_once_with()
        self._assert_refreshed_once(controller._app.trigger_panel)

    def test_external_layout_addition_refreshes_after_reload(self):
        controller = self._controller()
        controller.keyboard_layouts_dir = ""
        controller._app.base_dir = "."
        controller._keyboard_layout_entries = {"default": controller._keyboard_layout_entries["default"]}
        controller._app.paths.to_config_relative_or_absolute = Mock(return_value="external.json")

        with patch(
            "keyseq.presentation.controllers.layout_controller.filedialog.askopenfilename",
            return_value="external.json",
        ), patch(
            "keyseq.presentation.controllers.layout_controller.load_layout_from_json",
            return_value=SimpleNamespace(layout_id="new_external"),
        ):
            controller.add_external_keyboard_layout()

        controller.reload_keyboard_layouts.assert_called_once_with()
        self._assert_refreshed_once(controller._app.trigger_panel)

    def test_external_layout_deletion_refreshes_after_reload(self):
        controller = self._controller()
        dialog = SimpleNamespace(result="external", wait_window=Mock())

        with patch(
            "keyseq.presentation.controllers.layout_controller.LayoutDeleteDialog",
            return_value=dialog,
        ), patch(
            "keyseq.presentation.controllers.layout_controller.messagebox.askyesno",
            return_value=True,
        ):
            controller.delete_keyboard_layout()

        controller.reload_keyboard_layouts.assert_called_once_with()
        self._assert_refreshed_once(controller._app.trigger_panel)

    def test_deleting_selected_layout_refreshes_when_persist_fails(self):
        controller = self._controller()
        controller.keyboard_layout_id = "external"
        controller._app.data["external_keyboard_layouts"] = [{"path": "external.json"}]
        controller.persist_keyboard_layout_selection.return_value = False
        dialog = SimpleNamespace(result="external", wait_window=Mock())

        with patch(
            "keyseq.presentation.controllers.layout_controller.LayoutDeleteDialog",
            return_value=dialog,
        ), patch(
            "keyseq.presentation.controllers.layout_controller.messagebox.askyesno",
            return_value=True,
        ):
            controller.delete_keyboard_layout()

        controller.persist_keyboard_layout_selection.assert_called_once_with()
        controller.reload_keyboard_layouts.assert_not_called()
        self._assert_refreshed_once(controller._app.trigger_panel)

    def test_reload_and_control_sync_do_not_refresh_lists(self):
        reload_controller = self._controller()
        reload_controller._app.held_inputs = None
        reload_controller._keyboard_layout_entries = {}
        sync_spy = Mock()
        reload_controller.sync_keyboard_layout_controls = sync_spy
        reload_spy = Mock(
            wraps=LayoutController.reload_keyboard_layouts.__get__(
                reload_controller, LayoutController
            )
        )
        reload_controller.reload_keyboard_layouts = reload_spy

        with patch(
            "keyseq.presentation.controllers.layout_controller.collect_keyboard_layouts",
            return_value={},
        ):
            reload_controller.reload_keyboard_layouts()

        reload_spy.assert_called_once_with()
        sync_spy.assert_called_once_with()
        reload_controller._app.trigger_panel.refresh_triggers.assert_not_called()
        reload_controller._app.trigger_panel.refresh_actions.assert_not_called()

        sync_controller = self._controller()
        rebuild_spy = Mock()
        sync_controller.rebuild_keyboard_layout_display_maps = rebuild_spy
        sync_controller.sync_keyboard_layout_controls()

        rebuild_spy.assert_called_once_with()
        sync_controller._app.trigger_panel.refresh_triggers.assert_not_called()
        sync_controller._app.trigger_panel.refresh_actions.assert_not_called()


if __name__ == "__main__":
    unittest.main()
