import tkinter as tk
from keyseq.shared.i18n import available_languages, tr
from keyseq.presentation.welcome.first_launch import open_welcome_again
from keyseq.presentation.tk_platform import accelerator_text, primary_modifier


def build_menu_bar(app):
    menubar = tk.Menu(app)

    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label=tr("menu.file.new"), command=app.keymap_set_io.new_config, accelerator=accelerator_text(app, "Ctrl+N"))
    file_menu.add_separator()
    file_menu.add_command(label=tr("menu.file.save"), command=app.keymap_set_io.save_keymap_set, accelerator=accelerator_text(app, "Ctrl+S"))
    file_menu.add_command(label=tr("menu.file.save_as"), command=app.keymap_set_io.save_as, accelerator=accelerator_text(app, "Ctrl+Shift+S"))
    file_menu.add_command(label=tr("menu.file.load_keymap_set"), command=app.keymap_set_io.load_keymap_set_from, accelerator=accelerator_text(app, "Ctrl+O"))
    file_menu.add_command(label=tr("menu.file.load_history"), command=app.keymap_set_history_io.open_history_dialog)
    file_menu.add_separator()
    file_menu.add_command(label="Import...", command=app.keymap_set_io.import_config)
    file_menu.add_command(label="Export...", command=app.keymap_set_io.export_config)
    file_menu.add_separator()
    file_menu.add_command(label=tr("menu.file.set_startup_keymap_set"), command=app.keymap_set_io.set_startup_keymap_set)
    file_menu.add_command(label=tr("menu.file.restore_sample"), command=app.keymap_set_io.restore_default)
    file_menu.add_separator()
    file_menu.add_command(label=tr("common.exit"), command=app.on_close)
    menubar.add_cascade(label=tr("menu.file.title"), menu=file_menu)

    settings_menu = tk.Menu(menubar, tearoff=False)
    settings_menu.add_command(label=tr("menu.settings.preset_edit"), command=app.open_preset_manager, accelerator=accelerator_text(app, "Ctrl+Alt+P"))
    settings_menu.add_command(label=tr("menu.settings.reference_cleanup"), command=app.reference_cleanup_io.run_cleanup)
    settings_menu.add_command(label=tr("menu.settings.orphan_sweep"), command=app.orphan_sweep_io.run_sweep)
    settings_menu.add_command(label=tr("menu.settings.quarantine_manage"), command=app.quarantine_manage_io.manage_quarantine)
    settings_menu.add_command(label=tr("menu.settings.keyboard_ui"), command=app.layout.open_keyboard_window)
    settings_menu.add_separator()
    settings_menu.add_command(label=tr("menu.settings.add_external_layout"), command=app.layout.add_external_keyboard_layout)
    settings_menu.add_command(label=tr("menu.settings.delete_layout"), command=app.layout.delete_keyboard_layout)
    settings_menu.add_separator()
    settings_menu.add_checkbutton(
        label=tr("menu.settings.show_physical_key_names"),
        variable=app.ui_vars.keyboard_show_physical_key_labels_var,
        command=app.layout.toggle_keyboard_show_physical_key_labels,
    )
    settings_menu.add_separator()

    font_menu = tk.Menu(settings_menu, tearoff=False)
    for delta in (-3, -2, -1, 0, 1, 2, 3):
        label = tr("menu.settings.font_size.standard") if delta == 0 else f"{delta:+d}"
        font_menu.add_radiobutton(
            label=label,
            value=delta,
            variable=app.ui_vars.ui_font_delta_var,
            command=lambda d=delta: app.set_ui_font_delta(d),
        )
    settings_menu.add_cascade(label=tr("menu.settings.font_size"), menu=font_menu)

    language_menu = tk.Menu(settings_menu, tearoff=False)
    for code, name in available_languages():
        language_menu.add_radiobutton(
            label=name,
            value=code,
            variable=app.ui_vars.ui_language_var,
            command=lambda c=code: app.set_ui_language(c),
        )
    settings_menu.add_cascade(label=tr("menu.settings.language"), menu=language_menu)

    menubar.add_cascade(label=tr("menu.settings.title"), menu=settings_menu)

    help_menu = tk.Menu(menubar, tearoff=False)
    help_menu.add_command(label=tr("menu.help.guide"), command=lambda: app.help.open("guide"))
    help_menu.add_command(label=tr("menu.help.faq"), command=lambda: app.help.open("faq"))
    help_menu.add_command(
        label=tr("menu.help.show_welcome"), command=lambda: open_welcome_again(app),
    )
    help_menu.add_separator()
    help_menu.add_command(
        label=tr("menu.help.version"),
        command=lambda: _open_version_dialog(app),
    )
    help_menu.add_command(label=tr("menu.help.license"), command=lambda: app.license.open())
    menubar.add_cascade(label=tr("menu.help.title"), menu=help_menu)

    app.config(menu=menubar)
    app.menubar = menubar


def _open_version_dialog(app: tk.Misc) -> None:
    from keyseq.presentation.help.version_dialog import open_version_dialog

    open_version_dialog(app)


def bind_menu_shortcuts(app):
    modifier = primary_modifier(app)
    app.bind(f"<{modifier}-n>", app._on_shortcut_new, add="+")
    app.bind(f"<{modifier}-N>", app._on_shortcut_new, add="+")
    app.bind(f"<{modifier}-s>", app._on_shortcut_save, add="+")
    app.bind(f"<{modifier}-S>", app._on_shortcut_save, add="+")
    app.bind(f"<{modifier}-o>", app._on_shortcut_load, add="+")
    app.bind(f"<{modifier}-O>", app._on_shortcut_load, add="+")
    app.bind(f"<{modifier}-Shift-s>", app._on_shortcut_save_as, add="+")
    app.bind(f"<{modifier}-Shift-S>", app._on_shortcut_save_as, add="+")
    app.bind(f"<{modifier}-Alt-p>", app._on_shortcut_open_preset_manager, add="+")
    app.bind(f"<{modifier}-Alt-P>", app._on_shortcut_open_preset_manager, add="+")
