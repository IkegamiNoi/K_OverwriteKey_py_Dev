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


if __name__ == "__main__":
    unittest.main()
