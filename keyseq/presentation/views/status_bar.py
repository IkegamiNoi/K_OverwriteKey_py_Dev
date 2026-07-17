from tkinter import ttk


def build_status_area(app, parent):
    # フック/トリガー状態表示（1行または2行）
    runtime_status_frame = ttk.LabelFrame(parent, text="ステータス", padding=(10, 6))
    runtime_status_frame.pack(side="top", fill="x", padx=12, pady=(0, 4))
    ttk.Label(runtime_status_frame, textvariable=app.ui_vars.status_var, anchor="w", justify="left").pack(fill="x")
    # 共通ステータスバー（左: ファイル状態 / 中央: 一時メッセージ）
    status_bar = ttk.Frame(parent, style="Statusbar.TFrame")
    status_bar.pack(side="bottom", fill="x")
    status_bar.grid_columnconfigure(0, weight=1)
    status_bar.grid_columnconfigure(1, weight=1)
    status_bar.grid_columnconfigure(2, weight=1)
    ttk.Label(
        status_bar,
        textvariable=app.ui_vars.file_status_var,
        style="Statusbar.TLabel",
        anchor="w",
        justify="left",
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(
        status_bar,
        textvariable=app.ui_vars.flash_message_var,
        style="Statusbar.TLabel",
        anchor="center",
        justify="center",
    ).grid(row=0, column=1, sticky="ew")
    ttk.Label(status_bar, text="", style="Statusbar.TLabel", anchor="e").grid(row=0, column=2, sticky="e")

    app._update_file_status()
