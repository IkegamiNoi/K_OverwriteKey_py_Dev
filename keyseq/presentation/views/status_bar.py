from tkinter import ttk

from keyseq.presentation.hover_tooltip import bind_hover_tooltip


def _bind_status_tooltip(label, display_var, full_var) -> None:
    def is_truncated() -> bool:
        width = label.winfo_width()
        return width > 1 and label.winfo_reqwidth() > width

    tooltip = bind_hover_tooltip(label, full_var.get, is_truncated)
    pending = None

    def refresh() -> None:
        nonlocal pending
        pending = None
        tooltip.refresh()

    def request_refresh(*_args) -> None:
        nonlocal pending
        # 変数の書き込み後、Label の文言と要求幅が更新されてから判定する。
        if pending is None:
            pending = label.after_idle(refresh)

    traces = [(var, var.trace_add("write", request_refresh)) for var in (display_var, full_var)]

    def cleanup(_event) -> None:
        nonlocal pending
        for var, trace in traces:
            var.trace_remove("write", trace)
        if pending is not None:
            label.after_cancel(pending)
            pending = None

    label.bind("<Configure>", request_refresh, add="+")
    label.bind("<Destroy>", cleanup, add="+")


def build_status_area(app, parent):
    # フック/トリガー状態表示（1行または2行）
    runtime_status_frame = ttk.LabelFrame(parent, text="ステータス", padding=(10, 6))
    runtime_status_frame.pack(
        side="bottom", fill="x", padx=12, pady=(0, 4), before=app.outer,
    )
    runtime_label = ttk.Label(runtime_status_frame, textvariable=app.ui_vars.status_var, anchor="w", justify="left")
    runtime_label.pack(fill="x")
    # 共通ステータスバー（左: ファイル状態 / 中央: 一時メッセージ）
    status_bar = ttk.Frame(parent, style="Statusbar.TFrame")
    # 先に pack した側が下端に来るため、ステータス欄より前へ入れて最下段にする。
    status_bar.pack(side="bottom", fill="x", before=runtime_status_frame)
    status_bar.grid_columnconfigure(0, weight=1)
    status_bar.grid_columnconfigure(1, weight=1)
    status_bar.grid_columnconfigure(2, weight=1)
    file_label = ttk.Label(
        status_bar,
        textvariable=app.ui_vars.file_status_var,
        style="Statusbar.TLabel",
        anchor="w",
        justify="left",
    )
    file_label.grid(row=0, column=0, sticky="w")
    flash_label = ttk.Label(
        status_bar,
        textvariable=app.ui_vars.flash_message_var,
        style="Statusbar.TLabel",
        anchor="center",
        justify="center",
    )
    flash_label.grid(row=0, column=1, sticky="ew")
    ttk.Label(status_bar, text="", style="Statusbar.TLabel", anchor="e").grid(row=0, column=2, sticky="e")

    _bind_status_tooltip(runtime_label, app.ui_vars.status_var, app.ui_vars.status_full_var)
    _bind_status_tooltip(file_label, app.ui_vars.file_status_var, app.ui_vars.file_status_full_var)
    _bind_status_tooltip(flash_label, app.ui_vars.flash_message_var, app.ui_vars.flash_message_full_var)
    app._update_file_status()
