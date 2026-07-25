from __future__ import annotations

from keyseq.presentation.controllers.config_io.io_dialogs import IoDialogs
from keyseq.presentation.controllers.config_io.keymap_file_io import KeymapFileIo
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.sequence_file_io import SequenceFileIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.controllers.config_io.trigger_set_file_io import TriggerSetFileIo


class ConfigIoController:
    """構成セット・個別JSON（keymap / trigger_set / sequence）の保存・読込フロー。"""

    def __init__(self, app) -> None:
        self._app = app
        self._keymap_set_io = KeymapSetIo(app)
        self._startup_io = StartupIo(app)
        self._io_dialogs = IoDialogs(app)
        self._keymap_io = KeymapFileIo(app)
        self._trigger_set_io = TriggerSetFileIo(app)
        self._sequence_io = SequenceFileIo(app)

    # Temporary migration-era wrappers; scheduled for removal in task_05.
    def confirm_save_if_dirty(self, action_name: str) -> bool:
        return self._keymap_set_io.confirm_save_if_dirty(action_name)

    def new_config(self):
        self._keymap_set_io.new_config()

    def save_keymap_set(self, *, show_success_dialog: bool = True) -> bool:
        return self._keymap_set_io.save_keymap_set(show_success_dialog=show_success_dialog)

    def save_as(self, *, show_success_dialog: bool = True) -> bool:
        return self._keymap_set_io.save_as(show_success_dialog=show_success_dialog)

    def save_keymap_set_to(self, path: str, *, flash_message: str, show_success_dialog: bool) -> bool:
        return self._keymap_set_io.save_keymap_set_to(
            path,
            flash_message=flash_message,
            show_success_dialog=show_success_dialog,
        )

    def load_keymap_set_from(self):
        self._keymap_set_io.load_keymap_set_from()

    def import_config(self):
        self._keymap_set_io.import_config()

    def export_config(self):
        self._keymap_set_io.export_config()

    def restore_default(self):
        self._keymap_set_io.restore_default()

    def set_startup_keymap_set(self):
        self._keymap_set_io.set_startup_keymap_set()

    def apply_loaded_data_to_ui(self):
        self._keymap_set_io.apply_loaded_data_to_ui()

    def choose_split_base_dir_for_keymap_set(self, save_path: str) -> str:
        return self._keymap_set_io.choose_split_base_dir_for_keymap_set(save_path)

    def load_startup_and_config(self):
        self._startup_io.load_startup_and_config()

    def write_startup(self, data: dict[str, any]):
        self._startup_io.write_startup(data)

    def choose_save_path_with_collision(self, *, title: str, suggested_path: str) -> str:
        return self._io_dialogs.choose_save_path_with_collision(title=title, suggested_path=suggested_path)

    def ask_link_label_to_filename(self, *, title: str, path: str) -> bool:
        return self._io_dialogs.ask_link_label_to_filename(title=title, path=path)

    # Temporary migration-era wrappers; scheduled for removal in task_05.
    def selected_keymap_for_io(self) -> "tuple[int, dict] | tuple[None, None]":
        return self._keymap_io.selected_keymap_for_io()

    def save_selected_keymap(self) -> bool:
        return self._keymap_io.save_selected_keymap()

    def save_selected_keymap_as(self) -> bool:
        return self._keymap_io.save_selected_keymap_as()

    def save_keymap_to_path(self, index: int, keymap: dict, path: str) -> bool:
        return self._keymap_io.save_keymap_to_path(index, keymap, path)

    def load_keymap_file(self) -> None:
        self._keymap_io.load_keymap_file()

    def save_trigger_set_file(self) -> bool:
        return self._trigger_set_io.save_trigger_set_file()

    def save_trigger_set_file_as(self) -> bool:
        return self._trigger_set_io.save_trigger_set_file_as()

    def save_trigger_set_to_path(self, path: str) -> bool:
        return self._trigger_set_io.save_trigger_set_to_path(path)

    def load_trigger_set_file(self) -> None:
        self._trigger_set_io.load_trigger_set_file()

    def save_selected_sequence(self) -> bool:
        return self._sequence_io.save_selected_sequence()

    def save_selected_sequence_as(self) -> bool:
        return self._sequence_io.save_selected_sequence_as()

    def save_sequence_to_path(self, trigger: dict, path: str) -> bool:
        return self._sequence_io.save_sequence_to_path(trigger, path)

    def load_sequence_file(self) -> None:
        self._sequence_io.load_sequence_file()
