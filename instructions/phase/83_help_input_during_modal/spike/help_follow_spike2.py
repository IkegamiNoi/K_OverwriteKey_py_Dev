"""【一時ファイル・phase 83 task_07 で削除する】暫定 63 の手順どおりの付け替え（task_03 の実測用）。

実行: リポジトリの .venv の python で `python instructions/phase/83_help_input_during_modal/spike/help_follow_spike2.py [ログのパス]`
操作: ROOT の「Help」でヘルプを開く → 「Open dialog」→ ダイアログの「Open child」→ 各ダイアログの「Close」。
暫定 63 との対応: 閉じるときはダイアログを先に破棄し、ヘルプは親と一緒に消える（§3.5）→ after_idle で持ち主の子として
控えから作り直す。開くときは新しい窓を先に出してから古い窓を消す（§3.4）。新しいヘルプは持ち主のすぐ下（§3.6）。
フォーカスには触らない。ヘルプに初期フォーカスを入れない。
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
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


root = tk.Tk()
root.title("ROOT_APP")
root.geometry("320x160+40+60")
tk.Entry(root).pack(pady=6)
modals: list[tk.Toplevel] = []


def name(w: tk.Misc | None) -> str:
    if w is None:
        return "None"
    try:
        return w.winfo_toplevel().title() + ":" + w.winfo_class()
    except tk.TclError:
        return str(w)


class Controller:
    def __init__(self) -> None:
        self.window: "Help | None" = None
        self.state: dict | None = None
        self.orphaned = False
        self.orphaned_at = 0.0
        self.restoring = False  # 状態を戻している間は控えを上書きしない

    # 控え（変わるたびに取る）
    def remember(self, **kw: object) -> None:
        if self.state is not None and not self.restoring:
            self.state.update(kw)

    def open(self) -> None:
        if self.window is None and not self.orphaned:
            self.state = {"geometry": "360x300+420+60", "filter": "", "check": False, "yview": 0.0}
            self.window = Help(owner(), self, self.state)
            self.window.deiconify()

    def user_close(self) -> None:
        if self.window is not None:
            w, self.window = self.window, None
            w.reason = "user"
            self.state = None
            w.destroy()

    def on_window_destroyed(self, w: "Help") -> None:
        if w.reason is None and w is self.window:
            self.window = None
            self.orphaned = True
            self.orphaned_at = time.monotonic()
            log("help destroyed with its parent -> pending re-create")

    def front_changed(self) -> None:
        root.after_idle(self.reconcile)

    def reconcile(self) -> None:
        target = owner()
        if self.orphaned:
            self.orphaned = False
            new = self._build(target)
            gap = 1000 * (time.monotonic() - self.orphaned_at)
            log(f"re-created under {target.title()} gap={gap:.0f} ms", "focus", name(root.focus_get()))
            return
        if self.window is None or self.window.master is target:
            return
        old = self.window
        t = time.monotonic()
        self._build(target)
        old.reason = "replace"
        old.destroy()
        log(f"moved under {target.title()} in {1000 * (time.monotonic() - t):.0f} ms", "focus", name(root.focus_get()))

    def _build(self, target: tk.Misc) -> "Help":
        self.restoring = True
        try:
            new = Help(target, self, self.state)
            new.deiconify()
            new.wait_visibility()  # 表示されてからでないと lower が効かない（task_03 の実測）
            if target is not root:
                new.lower(target)
            # 案 X: OS が新しいヘルプを前面の窓にするので、持ち主が覚えている入力先へ戻す
            restore = getattr(target, "last_input", None)
            if restore is not None and restore.winfo_exists():
                restore.focus_force()
                log("focus restored to", name(restore))
            new.update_idletasks()
            new.text.yview_moveto(self.state["yview"])
            new.update_idletasks()
        finally:
            self.restoring = False
        self.window = new
        root.after(300, lambda: log("stacking after 300ms", root.tk.eval("wm stackorder .")))
        return new


class Help(tk.Toplevel):
    def __init__(self, master: tk.Misc, ctl: Controller, state: dict) -> None:
        super().__init__(master)
        self.withdraw()
        self.reason: str | None = None
        self.ctl = ctl
        self.title("HELP")
        self.geometry(state["geometry"])
        self.filter_var = tk.StringVar(self, value=state["filter"])
        self.check_var = tk.BooleanVar(self, value=state["check"])
        tk.Entry(self, textvariable=self.filter_var).pack(fill="x", padx=6, pady=4)
        tk.Checkbutton(self, text="section open", variable=self.check_var).pack(anchor="w")
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.text = tk.Text(frame, height=10, width=40)
        bar = tk.Scrollbar(frame, command=self.text.yview)

        def on_scroll(first: str, last: str) -> None:
            bar.set(first, last)
            ctl.remember(yview=float(first))

        self.text.configure(yscrollcommand=on_scroll)
        bar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.text.insert("end", "\n".join(f"line {i}" for i in range(1, 201)))
        self.filter_var.trace_add("write", lambda *_: ctl.remember(filter=self.filter_var.get()))
        self.check_var.trace_add("write", lambda *_: ctl.remember(check=self.check_var.get()))
        self.bind("<Configure>", self._configure, add="+")
        self.bind("<Destroy>", self._destroyed, add="+")
        self.protocol("WM_DELETE_WINDOW", ctl.user_close)
        if MAC:
            self.bind("<Activate>", self._activate, add="+")
            self.bind("<Deactivate>", self._deactivate, add="+")

    def _configure(self, e: tk.Event) -> None:
        if e.widget is self and self.winfo_ismapped():
            self.ctl.remember(geometry=self.geometry())

    def _destroyed(self, e: tk.Event) -> None:
        if e.widget is self:
            self.ctl.on_window_destroyed(self)

    def _activate(self, e: tk.Event) -> None:
        if e.widget is self and self.master is not root and self.grab_current() is self.master:
            self.grab_set()

    def _deactivate(self, e: tk.Event) -> None:
        if e.widget is self and self.grab_current() is self:
            try:
                if self.master.winfo_exists():
                    self.master.grab_set()
            except tk.TclError:
                pass


ctl = Controller()


def track_input(e: tk.Event) -> None:
    # 案 X: ダイアログごとに最後に入力していた部品を覚える（窓自身へのフォーカスは数えない）
    w = e.widget
    if not isinstance(w, tk.Misc) or isinstance(w, tk.Toplevel):
        return
    top = w.winfo_toplevel()
    if top in modals:
        top.last_input = w


root.bind_all("<FocusIn>", track_input, add="+")


def owner() -> tk.Misc:
    for w in reversed(modals):
        if w.winfo_exists():
            return w
    return root


def open_dialog(parent: tk.Misc) -> None:
    n = len(modals) + 1
    d = tk.Toplevel(parent)
    d.title(f"DIALOG_{n}")
    d.geometry(f"300x150+{380 + 30 * n}+{120 + 30 * n}")  # ヘルプと重なる位置
    d.transient(parent)
    entry = tk.Entry(d)
    entry.pack(pady=6)
    tk.Button(d, text="Open child", command=lambda: open_dialog(d)).pack()
    tk.Button(d, text="Close", command=d.destroy).pack()
    d.protocol("WM_DELETE_WINDOW", d.destroy)
    previous = root.grab_current()
    modals.append(d)
    d.grab_set()
    entry.focus_set()  # grab_modal の初期の入力先に当たる
    d.last_input = entry  # 案 X: 開いた直後の入力先 = 初期の入力先

    def restore(e: tk.Event) -> None:  # modal.py の restore_grab に当たる
        if e.widget is not d:
            return
        modals.remove(d)
        try:
            if previous is not None and previous.winfo_exists():
                previous.grab_set()
        except tk.TclError:
            pass
        log("closed", d.title())
        ctl.front_changed()

    d.bind("<Destroy>", restore, add="+")
    log("opened", d.title())
    ctl.front_changed()


tk.Button(root, text="Help", command=ctl.open).pack()
tk.Button(root, text="Open dialog", command=lambda: open_dialog(root)).pack()
root.after(900000, root.destroy)
root.mainloop()
