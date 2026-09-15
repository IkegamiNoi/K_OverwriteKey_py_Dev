"""idea_19 診断 v2: Win+D / タスクバー復元で Tk に何が届くかを観測し、対策候補を A/B する。

    python diag_win_d2.py events   # そのまま観測（対策なし）
    python diag_win_d2.py fix      # root の <Unmap> で grab を外し、<Map> で戻す

操作はどちらも同じ: 窓が出たら ①Win+D ②タスクバーのアイコンで戻す ③10 秒待って Ctrl+C
（fix で戻れた場合は、戻った後に grab が再取得されているか = 背面の root を操作できないかも見る）。
ログは本ファイルと同じフォルダの diag_win_d2_<mode>.log。
"""
import os
import sys
import tkinter as tk
from datetime import datetime

MODE = (sys.argv[1] if len(sys.argv) > 1 else "events").lower()
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"diag_win_d2_{MODE}.log")
WATCHED = ("<Map>", "<Unmap>", "<Visibility>", "<FocusIn>", "<FocusOut>", "<Activate>", "<Deactivate>")


def main():
    log = open(LOG, "w", encoding="utf-8")

    def write(line):
        log.write(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} {line}\n")
        log.flush()

    root = tk.Tk()
    root.title("diag2 root (App 相当)")
    root.geometry("380x120+80+80")
    tk.Label(root, text=f"mode={MODE}\nWin+D → タスクバーから復元を試す",
             justify="left").pack(padx=12, pady=12)

    child = tk.Toplevel(root); child.title("diag2 child")
    child.transient(root); child.geometry("380x100+140+240")

    grand = tk.Toplevel(root); grand.title("diag2 grandchild (grab)")
    grand.transient(child); grand.geometry("380x100+200+400")

    root.update()
    grand.grab_set()
    wins = [("root", root), ("child", child), ("grand", grand)]

    def states():
        parts = []
        for name, w in wins:
            try:
                parts.append(f"{name}=[{w.wm_state()},v={int(bool(w.winfo_viewable()))}]")
            except tk.TclError:
                parts.append(f"{name}=[ERR]")
        try:
            parts.append(f"grab={root.grab_current()}")
        except tk.TclError:
            parts.append("grab=ERR")
        return " ".join(parts)

    for name, w in wins:
        for seq in WATCHED:
            def handler(event, name=name, seq=seq, w=w):
                if event.widget is w:
                    write(f"EVENT {name}{seq} | {states()}")
            w.bind(seq, handler, "+")

    if MODE == "fix":
        state = {"released": False}

        def on_root_unmap(event):
            if event.widget is not root or state["released"]:
                return
            holder = root.grab_current()
            if holder is not None:
                state["released"] = True
                state["holder"] = holder
                holder.grab_release()
                write(f"FIX grab_release on root <Unmap> (holder={holder}) | {states()}")

        def on_root_map(event):
            if event.widget is not root or not state["released"]:
                return
            state["released"] = False
            holder = state.get("holder")
            try:
                if holder is not None and holder.winfo_exists():
                    holder.deiconify()
                    root.update_idletasks()
                    holder.grab_set()
                    write(f"FIX grab_set on root <Map> (holder={holder}) | {states()}")
            except tk.TclError as e:
                write(f"FIX failed: {e}")

        root.bind("<Unmap>", on_root_unmap, "+")
        root.bind("<Map>", on_root_map, "+")

    write(f"# mode={MODE} transient: child->{child.wm_transient()} grand->{grand.wm_transient()}")
    write(f"START {states()}")

    prev = {"line": states()}

    def tick():
        now = states()
        if now != prev["line"]:
            write(f"STATE {now}")
            prev["line"] = now
        root.after(300, tick)

    tick()
    try:
        root.mainloop()
    finally:
        write(f"END {states()}")
        log.close()


main()
