import tkinter as tk


def build_menu_bar(app):
    menubar = tk.Menu(app)

    file_menu = tk.Menu(menubar, tearoff=False)
    file_menu.add_command(label="新規作成", command=app.keymap_set_io.new_config, accelerator="Ctrl+N")
    file_menu.add_separator()
    file_menu.add_command(label="保存", command=app.keymap_set_io.save_keymap_set, accelerator="Ctrl+S")
    file_menu.add_command(label="別名で保存…", command=app.keymap_set_io.save_as, accelerator="Ctrl+Shift+S")
    file_menu.add_command(label="読込（構成セット）…", command=app.keymap_set_io.load_keymap_set_from, accelerator="Ctrl+O")
    file_menu.add_separator()
    file_menu.add_command(label="Import...", command=app.keymap_set_io.import_config)
    file_menu.add_command(label="Export...", command=app.keymap_set_io.export_config)
    file_menu.add_separator()
    file_menu.add_command(label="起動時に読む構成セットを指定…", command=app.keymap_set_io.set_startup_keymap_set)
    file_menu.add_command(label="例を復元", command=app.keymap_set_io.restore_default)
    file_menu.add_separator()
    file_menu.add_command(label="終了", command=app.on_close)
    menubar.add_cascade(label="ファイル", menu=file_menu)

    settings_menu = tk.Menu(menubar, tearoff=False)
    settings_menu.add_command(label="プリセット編集…", command=app.open_preset_manager, accelerator="Ctrl+Alt+P")
    settings_menu.add_command(label="キーボードUIを開く", command=app.layout.open_keyboard_window)
    settings_menu.add_separator()
    settings_menu.add_command(label="外部レイアウトを追加…", command=app.layout.add_external_keyboard_layout)
    settings_menu.add_command(label="レイアウトを削除…", command=app.layout.delete_keyboard_layout)
    settings_menu.add_separator()
    settings_menu.add_checkbutton(
        label="物理キー名を表示",
        variable=app.ui_vars.keyboard_show_physical_key_labels_var,
        command=app.layout.toggle_keyboard_show_physical_key_labels,
    )
    settings_menu.add_separator()

    font_menu = tk.Menu(settings_menu, tearoff=False)
    for delta in (-3, -2, -1, 0, 1, 2, 3):
        label = "標準 (0)" if delta == 0 else f"{delta:+d}"
        font_menu.add_radiobutton(
            label=label,
            value=delta,
            variable=app.ui_vars.ui_font_delta_var,
            command=lambda d=delta: app.set_ui_font_delta(d),
        )
    settings_menu.add_cascade(label="フォントサイズ", menu=font_menu)

    menubar.add_cascade(label="設定", menu=settings_menu)

    app.config(menu=menubar)
    app.menubar = menubar


def bind_menu_shortcuts(app):
    app.bind("<Control-n>", app._on_shortcut_new, add="+")
    app.bind("<Control-N>", app._on_shortcut_new, add="+")
    app.bind("<Control-s>", app._on_shortcut_save, add="+")
    app.bind("<Control-S>", app._on_shortcut_save, add="+")
    app.bind("<Control-o>", app._on_shortcut_load, add="+")
    app.bind("<Control-O>", app._on_shortcut_load, add="+")
    app.bind("<Control-Shift-s>", app._on_shortcut_save_as, add="+")
    app.bind("<Control-Shift-S>", app._on_shortcut_save_as, add="+")
    app.bind("<Control-Alt-p>", app._on_shortcut_open_preset_manager, add="+")
    app.bind("<Control-Alt-P>", app._on_shortcut_open_preset_manager, add="+")
