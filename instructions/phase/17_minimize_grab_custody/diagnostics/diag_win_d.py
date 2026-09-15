"""idea_19 診断: 子が grab を持つ状態で Win+D したときの各窓の状態を記録する。

使い方（worktree ルートで実行）:
    ../../../.venv/Scripts/python.exe <このファイル> [nested|flat]

  nested = phase 16 後の形（grandchild.transient(child)）※既定
  flat   = phase 16 前の形（grandchild.transient(root)）

操作: 3 つの窓が出たら ①Win+D ②タスクバーのアイコンでアプリへ戻そうとする
      ③戻れても戻れなくても 10 秒ほど待ってからログを見る（復元できない場合は
      コンソールで Ctrl+C。ログは終了時まで 500ms ごとに追記される）。
"""
import os
import sys
import tkinter as tk
from datetime import datetime

MODE = (sys.argv[1] if len(sys.argv) > 1 else "nested").lower()
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag_win_d.log")


def snapshot(root, wins):
    parts = []
    for name, w in wins:
        try:
            parts.append(f"{name}=[{w.wm_state()},viewable={int(bool(w.winfo_viewable()))}]")
        except tk.TclError as e:
            parts.append(f"{name}=[ERR {e}]")
    try:
        holder = root.grab_current()
    except tk.TclError:
        holder = "ERR"
    parts.append(f"grab={holder}")
    return " ".join(parts)


def main():
    root = tk.Tk()
    root.title("diag root (App 相当)")
    root.geometry("360x120+80+80")
    tk.Label(root, text=f"mode={MODE}\nWin+D → タスクバーから復元を試す",
             justify="left").pack(padx=12, pady=12)

    child = tk.Toplevel(root)          # プリセット編集 相当
    child.title("diag child")
    child.transient(root)
    child.geometry("360x100+140+240")

    grand = tk.Toplevel(root)          # 上書き確認 / プリセット追加 相当（master は root = 役割 1）
    grand.title("diag grandchild (grab)")
    grand.transient(child if MODE == "nested" else root)
    grand.geometry("360x100+200+400")

    root.update()
    grand.grab_set()
    wins = [("root", root), ("child", child), ("grand", grand)]

    log = open(LOG, "w", encoding="utf-8")
    log.write(f"# mode={MODE} start={datetime.now().isoformat(timespec='seconds')}\n")
    log.write(f"# transient: child->{child.wm_transient()} grand->{grand.wm_transient()}\n")
    log.flush()

    def tick():
        log.write(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} {snapshot(root, wins)}\n")
        log.flush()
        root.after(500, tick)

    tick()
    try:
        root.mainloop()
    finally:
        log.close()


main()
