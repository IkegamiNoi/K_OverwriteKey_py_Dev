"""First-launch choices with a local language preview."""

import tkinter as tk
from tkinter import ttk

from keyseq.presentation.help.help_content import load_help_content
from keyseq.presentation.help.help_window import HelpWindow
from keyseq.presentation.modal import grab_modal
from keyseq.shared.i18n import available_languages, tr_in

from .welcome_result import WelcomeResult, estimate_layout_id


class WelcomeWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc, *, language: str, reopen: bool = False) -> None:
        super().__init__(master)
        self.reopen = reopen
        self.language = language
        self._languages = available_languages()
        self._layouts = (("us_tkl", "US TKL"), ("jis", "JIS"))
        self._layout_touched = False
        self.layout_var = tk.StringVar(self, value=estimate_layout_id(language))
        self.start_var = tk.StringVar(self, value="sample")
        self.result = WelcomeResult(language, self.layout_var.get(), "sample")
        self._help_window: HelpWindow | None = None
        self._body: ttk.Frame | None = None
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self.bind("<Escape>", self._finish)
        self._build_content()
        if reopen:
            grab_modal(self, self.master, focus=self.start_button)
        else:
            # The root is withdrawn during first launch.
            grab_modal(self, focus=self.start_button)

    def _text(self, key: str) -> str:
        return tr_in(self.language, f"welcome.{key}")

    def _build_content(self) -> None:
        if self._body is not None:
            self._body.destroy()
        self.title(self._text("title"))
        self._body = ttk.Frame(self, padding=16)
        self._body.pack(fill="both", expand=True)
        if not self.reopen:
            language_row = ttk.Frame(self._body)
            language_row.pack(fill="x")
            ttk.Label(language_row, text="Language").pack(side="left", padx=(0, 12))
            self.language_combo = ttk.Combobox(
                language_row, state="readonly", values=[name for _, name in self._languages],
            )
            self.language_combo.current([code for code, _ in self._languages].index(self.language))
            self.language_combo.pack(side="left")
            self.language_combo.bind("<<ComboboxSelected>>", self._change_language)
        if self.reopen:
            self._build_usage()
            self._build_sample_settings()
        else:
            self._build_layout()
            self._build_usage()
            self._build_start()
        self._build_buttons()
        self._fit_and_center()

    def _section(self, key: str) -> ttk.LabelFrame:
        section = ttk.LabelFrame(self._body, text=self._text(key), padding=10)
        section.pack(fill="x", pady=(12, 0))
        return section

    def _build_layout(self) -> None:
        self.layout_section = self._section("layout")
        self.layout_combo = ttk.Combobox(
            self.layout_section, state="readonly", values=[name for _, name in self._layouts],
        )
        self.layout_combo.current([layout_id for layout_id, _ in self._layouts].index(
            self.layout_var.get(),
        ))
        self.layout_combo.pack(side="left")
        self.layout_combo.bind("<<ComboboxSelected>>", self._touch_layout)

    def _build_sample_settings(self) -> None:
        self.sample_settings_section = self._section("sample_settings")
        self.sample_description = ttk.Label(
            self.sample_settings_section, text=self._text("sample_description"),
            wraplength=520, justify="left",
        )
        self.sample_description.pack(anchor="w")
        self.restore_sample_button = ttk.Button(
            self.sample_settings_section,
            text=tr_in(self.language, "menu.file.restore_sample"), command=self._restore_sample,
        )
        self.restore_sample_button.pack(anchor="w", pady=(8, 0))

    def _restore_sample(self) -> None:
        try:
            self.master.keymap_set_io.restore_default(parent=self)
        finally:
            # Keep the original grab_modal destroy handler and its previous holder.
            if self.winfo_exists() and self.winfo_viewable():
                holder = self.grab_current()
                if holder is None or holder is self:
                    self.grab_set()
                    self.restore_sample_button.focus_set()

    def _build_usage(self) -> None:
        self.usage_section = self._section("usage")
        self.usage_labels = []
        for key in ("usage.trigger", "usage.sequence", "usage.hook"):
            label = ttk.Label(
                self.usage_section, text=self._text(key), wraplength=520, justify="left",
            )
            label.pack(anchor="w", pady=2)
            self.usage_labels.append(label)

    def _build_start(self) -> None:
        self.start_section = self._section("start")
        self.start_choices: dict[str, ttk.Radiobutton] = {}
        for choice in ("sample", "empty"):
            button = ttk.Radiobutton(
                self.start_section, text=self._text(f"start.{choice}"),
                value=choice, variable=self.start_var,
            )
            button.pack(anchor="w", pady=2)
            self.start_choices[choice] = button
        self.sample_description = ttk.Label(
            self.start_section, text=self._text("sample_description"),
            wraplength=520, justify="left",
        )
        self.sample_description.pack(anchor="w", pady=(8, 0))

    def _build_buttons(self) -> None:
        buttons = ttk.Frame(self._body)
        buttons.pack(fill="x", pady=(16, 0))
        self.help_button = ttk.Button(
            buttons, text=self._text("open_help"), command=self._open_help,
        )
        self.help_button.pack(side="left")
        self.start_button = ttk.Button(
            buttons, text=self._text("close" if self.reopen else "begin"), command=self._finish,
        )
        self.start_button.pack(side="right")

    def _fit_and_center(self) -> None:
        self.update_idletasks()
        width = max(560, self.winfo_reqwidth())
        height = self.winfo_reqheight()
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _change_language(self, _event: tk.Event) -> None:
        self.language = self._languages[self.language_combo.current()][0]
        if not self._layout_touched:
            self.layout_var.set(estimate_layout_id(self.language))
        self._build_content()
        self.language_combo.focus_set()

    def _touch_layout(self, _event: tk.Event) -> None:
        self.layout_var.set(self._layouts[self.layout_combo.current()][0])
        self._layout_touched = True

    def _open_help(self) -> None:
        if self.reopen:
            self.master.help.open_for_dialog(self, "guide", "")
            return
        if self._help_window is None or not self._help_window.winfo_exists():
            self._help_window = HelpWindow(
                self, load_help_content(), suspend_hook=lambda: None, resume_hook=lambda: None,
            )
        else:
            self._help_window.deiconify()
            self._help_window.lift()
            self._help_window.focus_set()
        self._help_window.select_tab("guide")

    def _finish(self, _event: tk.Event | None = None) -> str:
        self.result = WelcomeResult(self.language, self.layout_var.get(), self.start_var.get())
        self.destroy()
        return "break"
