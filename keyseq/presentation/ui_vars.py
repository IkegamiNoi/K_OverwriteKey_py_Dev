import tkinter as tk

from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS
from keyseq.presentation.keyboard_layouts import DEFAULT_LAYOUT_ID


class UiVars:
    """View / controller 間で共有する Tk 変数のホルダー。"""

    def __init__(self, master, ui_font_delta_pt: int) -> None:
        self.always_on_top_var = tk.BooleanVar(master=master, value=False)
        self.stop_key_var = tk.StringVar(master=master, value=str(master.data.get("hook_stop_key", "")))
        self.toggle_key_var = tk.StringVar(master=master, value=str(master.data.get("hook_toggle_key", "")))
        self.status_var = tk.StringVar(master=master, value="")
        self.file_status_var = tk.StringVar(master=master, value="")
        self.flash_message_var = tk.StringVar(master=master, value="")
        self.ui_font_delta_var = tk.IntVar(master=master, value=int(ui_font_delta_pt))
        self.suppress_var = tk.BooleanVar(master=master, value=True)
        self.run_to_end_var = tk.BooleanVar(master=master, value=False)
        self.run_to_end_delay_var = tk.StringVar(master=master, value=str(DEFAULT_RUN_TO_END_DELAY_MS))
        self.keyboard_layout_var = tk.StringVar(
            master=master,
            value=str(master.data.get("keyboard_layout", DEFAULT_LAYOUT_ID)),
        )
        self.keyboard_show_physical_key_labels_var = tk.BooleanVar(
            master=master,
            value=bool(master.data.get("keyboard_show_physical_key_labels", False)),
        )
