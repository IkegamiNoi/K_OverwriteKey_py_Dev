import tkinter as tk
root=tk.Tk(); root.geometry('200x80+60+60')
a=tk.Toplevel(root); a.transient(root)
b=tk.Toplevel(root); b.transient(a)
root.update(); b.grab_set(); root.update()
print("normal: a.viewable",a.winfo_viewable(),"b.viewable",b.winfo_viewable(),"grab",root.grab_current())
root.iconify(); root.update()
print("iconic: a.viewable",a.winfo_viewable(),"b.viewable",b.winfo_viewable(),"grab",root.grab_current())
b.destroy(); root.update()
print("after destroy holder while iconic: grab",root.grab_current())
root.deiconify(); root.update()
print("deiconify: a.viewable",a.winfo_viewable(),"grab",root.grab_current())
# grab_set on withdrawn window?
c=tk.Toplevel(root); c.withdraw(); root.update()
try:
    c.grab_set(); print("grab_set on withdrawn: OK ->",root.grab_current(),"c.viewable",c.winfo_viewable())
except tk.TclError as e:
    print("grab_set on withdrawn: TclError",e)
root.destroy()
