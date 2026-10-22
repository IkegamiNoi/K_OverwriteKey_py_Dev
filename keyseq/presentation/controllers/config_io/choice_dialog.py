"""ボタンに操作名を書いた選択肢で確認するモーダルダイアログ（暫定 51 §3.5）。

はい / いいえ に本文で意味を割り当てる確認の代わりに使う。
呼び出し側はモジュール経由で `choice_dialog.ask_choice(...)` を呼ぶ（テストで差し替えるため）。
"""
import tkinter as tk
from tkinter import ttk

from keyseq.presentation.modal import grab_modal


def ask_choice(
    app,
    *,
    title: str,
    message: str,
    choices: list[tuple[str, str]],
    default: str,
    cancel: str,
) -> str:
    """押したボタンの id を返す。× / Esc は `cancel` の id を返す。

    `choices` は `(選択肢 id, ボタンの文字)` の並び（見た目の左 → 右）。
    開いたときの入力先は `default` のボタン。開いている間はフックを止め、破棄で自動解除する。
    """
    parent = _grab_holder(app)
    result = {"choice": cancel}
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.resizable(False, False)
    frame = ttk.Frame(dialog, padding=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=message, justify="left", wraplength=560).pack(fill="both", expand=True)
    buttons_frame = ttk.Frame(frame)
    buttons_frame.pack(anchor="e", pady=(12, 0))

    def choose(choice: str) -> None:
        result["choice"] = choice
        dialog.destroy()

    buttons: dict[str, ttk.Button] = {}
    for index, (choice_id, text) in enumerate(choices):
        button = ttk.Button(buttons_frame, text=text, command=lambda c=choice_id: choose(c))
        button.pack(side="left", padx=(0 if index == 0 else 8, 0))
        buttons[choice_id] = button

    def invoke_focused(_event) -> None:
        # Enter はフォーカス中のボタンを押す（初期は既定ボタン。Tab の移動は ttk の既定）。
        try:
            focused = dialog.focus_get()
        except (tk.TclError, KeyError):
            return
        if isinstance(focused, ttk.Button):
            focused.invoke()

    dialog.bind("<Return>", invoke_focused)
    dialog.bind("<Escape>", lambda _event: choose(cancel))
    dialog.protocol("WM_DELETE_WINDOW", lambda: choose(cancel))
    default_button = buttons[default]
    app.hook.suspend_hook_for_dialog(dialog)
    grab_modal(dialog, parent, focus=default_button)
    dialog.wait_window()
    return result["choice"]


def _grab_holder(app) -> tk.Misc:
    """grab を持つウィンドウ（入れ子で開く経路の親）を返す。無ければ App。"""
    try:
        holder = app.grab_current()
    except (tk.TclError, KeyError):
        # 終了中や tkinter 管理外の保持者は解決できないため、App を親にする。
        return app
    return app if holder is None else holder
