"""【一時ファイル・phase 83 の目視が終わったら削除する】案 E の最小構成: ヘルプを、いちばん手前のダイアログの子へ作り直して付け替える。

実行: リポジトリの .venv の python で `python instructions/phase/83_help_input_during_modal/spike/help_follow_spike.py`
操作: ROOT の「Help」でヘルプを開く → 「Open dialog」でダイアログを開く → ダイアログの「Open child」で入れ子 →
各ダイアログの「Close」で閉じる。ヘルプの絞り込み欄・本文のスクロール・チェックの状態・位置が付け替えで保たれるか、
付け替えの瞬間にちらつくかを見る。Mac では前面の間だけ grab をヘルプへ移す（案 D と同じ）。
"""
import sys
import time
import tkinter as tk

LOG = sys.argv[1] if len(sys.argv) > 1 else None
MAC = sys.platform == "darwin"
T0 = time.monotonic()


def log(*a: object) -> None:
    line = f"{time.monotonic() - T0:8.3f} " + " ".join(map(str, a))
    print(line, flush=True)
    if LOG:
        with open(LOG, "a") as f:
            f.write(line + "\n")


root = tk.Tk()
root.title("ROOT_APP")
root.geometry("320x160+40+60")
tk.Entry(root).pack(pady=6)
modals: list[tk.Toplevel] = []  # 開いた順のダイアログ（いちばん手前 = 末尾）
help_win: "Help | None" = None


def top_owner() -> tk.Misc:
    return modals[-1] if modals else root


class Help(tk.Toplevel):
    def __init__(self, master: tk.Misc, state: dict | None) -> None:
        super().__init__(master)
        self.withdraw()
        self.title("HELP")
        self.filter_var = tk.StringVar()
        self.check_var = tk.BooleanVar()
        tk.Entry(self, textvariable=self.filter_var).pack(fill="x", padx=6, pady=4)
        tk.Checkbutton(self, text="section open", variable=self.check_var).pack(anchor="w")
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.text = tk.Text(frame, height=10, width=40)
        bar = tk.Scrollbar(frame, command=self.text.yview)
        self.text.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.text.insert("end", "\n".join(f"line {i}" for i in range(1, 201)))
        self.protocol("WM_DELETE_WINDOW", close_help)
        if MAC:
            self.bind("<Activate>", self._activate, add="+")
            self.bind("<Deactivate>", self._deactivate, add="+")
        if state:
            self.geometry(state["geometry"])
            self.filter_var.set(state["filter"])
            self.check_var.set(state["check"])
            self.update_idletasks()
            self.text.yview_moveto(state["yview"])
        else:
            self.geometry("360x300+420+60")

    def snapshot(self) -> dict:
        return {"geometry": self.geometry(), "filter": self.filter_var.get(),
                "check": self.check_var.get(), "yview": self.text.yview()[0]}

    def _activate(self, e: tk.Event) -> None:
        if e.widget is self and modals and self.grab_current() is self.master:
            self.grab_set()
            log("grab -> HELP")

    def _deactivate(self, e: tk.Event) -> None:
        if e.widget is self and self.grab_current() is self and self.master.winfo_exists():
            self.master.grab_set()
            log("grab back ->", self.master.title())


def open_help() -> None:
    global help_win
    if help_win is None:
        help_win = Help(top_owner(), None)
        help_win.deiconify()


def close_help() -> None:
    global help_win
    if help_win is not None:
        w, help_win = help_win, None
        w.destroy()


def follow(owner: tk.Misc, refocus: tk.Misc) -> None:
    """ヘルプを owner の子へ作り直す（新しい窓を先に出し、古い窓を後で消す）。"""
    global help_win
    if help_win is None or help_win.master is owner:
        return
    old = help_win
    t = time.monotonic()
    new = Help(owner, old.snapshot())
    new.deiconify()
    new.update_idletasks()
    old.destroy()
    help_win = new
    refocus.lift()
    refocus.focus_force()
    log(f"follow -> {getattr(owner, 'title', lambda: 'root')()} in {1000 * (time.monotonic() - t):.1f} ms",
        "state", new.snapshot())


def open_dialog(parent: tk.Misc) -> None:
    n = len(modals) + 1
    d = tk.Toplevel(parent)
    d.title(f"DIALOG_{n}")
    d.geometry(f"300x150+{40 + 30 * n}+{260 + 30 * n}")
    d.transient(parent)
    tk.Entry(d).pack(pady=6)
    tk.Button(d, text="Open child", command=lambda: open_dialog(d)).pack()
    tk.Button(d, text="Close", command=lambda: close_dialog(d)).pack()
    d.protocol("WM_DELETE_WINDOW", lambda: close_dialog(d))
    modals.append(d)
    d.grab_set()
    d.focus_set()
    log("open", d.title())
    follow(d, d)


def close_dialog(d: tk.Toplevel) -> None:
    modals.remove(d)
    owner = top_owner()
    follow(owner, owner)  # 先に付け替える（d を消すと子のヘルプも消えるため）
    d.destroy()
    if modals:
        modals[-1].grab_set()
    owner.lift()  # 窓を消したあとで手前の窓へ前面を戻す（消す前だと OS がヘルプを前面にする）
    owner.focus_force()
    log("close ->", getattr(owner, "title", lambda: "root")())


tk.Button(root, text="Help", command=open_help).pack()
tk.Button(root, text="Open dialog", command=lambda: open_dialog(root)).pack()
root.after(900000, root.destroy)
root.mainloop()
