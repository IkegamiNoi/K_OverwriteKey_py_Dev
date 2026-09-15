import tkinter as tk
root = tk.Tk(); root.geometry('200x80+60+60')
a = tk.Toplevel(root); a.transient(root); a.geometry('200x80+120+160')   # transient あり
b = tk.Toplevel(root)                                                     # transient なし（master は root）
b.geometry('200x80+180+260')
root.update()
print("transient: a=%r b=%r" % (a.wm_transient(), b.wm_transient()))
print("normal   : a=%s/v%d b=%s/v%d" % (a.wm_state(), a.winfo_viewable(), b.wm_state(), b.winfo_viewable()))
root.iconify(); root.update()
print("iconic   : a=%s/v%d b=%s/v%d" % (a.wm_state(), a.winfo_viewable(), b.wm_state(), b.winfo_viewable()))
# phase 16 §1-④ の形: 呼び出し元を破棄して transient が外れた子
root.deiconify(); root.update()
c = tk.Toplevel(root); c.transient(a); c.geometry('200x80+240+360'); root.update()
a.destroy(); root.update()
print("after caller destroy: c.transient=%r c=%s/v%d" % (c.wm_transient(), c.wm_state(), c.winfo_viewable()))
c.grab_set(); root.update()
root.iconify(); root.update()
print("iconic(orphan c)    : c=%s/v%d grab=%s" % (c.wm_state(), c.winfo_viewable(), root.grab_current()))
root.destroy()
