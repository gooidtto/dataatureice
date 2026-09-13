"""Complete optional UI actions used by phone_search.App."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox


def _new_window(self, title, geometry=None, minsize=None):
    factory = getattr(self, "_window_factory", None)
    if not callable(factory):
        raise RuntimeError("SearchApp must provide _new_window()")
    w = factory(title=title, geometry=geometry, minsize=minsize)
    try:
        w.withdraw()
        self.root.after_idle(lambda: _show_window(w))
    except tk.TclError:
        pass
    return w


def _show_window(w):
    try:
        if w.winfo_exists():
            w.update_idletasks()
            w.deiconify()
            w.lift()
    except tk.TclError:
        pass


def addToFavorites(self, rows):
    rows = list(rows or [])
    if not rows:
        return messagebox.showinfo("收藏", "请先选择要收藏的记录", parent=self.root)
    added, duplicate = self.fav.add(rows)
    if added and duplicate:
        messagebox.showinfo("收藏", f"已收藏 {len(added)} 条，{len(duplicate)} 条已经收藏", parent=self.root)
    elif added:
        messagebox.showinfo("收藏", f"已收藏 {len(added)} 条", parent=self.root)
    else:
        messagebox.showinfo("收藏", "已经收藏", parent=self.root)
    return added, duplicate


def add_favorite(self):
    """Compatibility handler for the main-window one-click favorite button."""
    rows = self.selected() or self.rows
    return self.addToFavorites(rows)


def _install_window_lifecycle(App):
    original_init = App.__init__
    base_factory = getattr(App, "_new_window", None)
    if not callable(base_factory):
        raise RuntimeError("SearchApp must provide _new_window() before lifecycle installation")

    def _init(self, root, *args, **kwargs):
        root.withdraw()
        try:
            original_init(self, root, *args, **kwargs)
            root.update_idletasks()
            root.deiconify()
            root.update_idletasks()
        except Exception:
            try:
                root.deiconify()
            except tk.TclError:
                pass
            raise

    App.__init__ = _init
    App._window_factory = base_factory
    App._new_window = _new_window


def open_dir(self):
    path = os.path.abspath(self.d)
    os.makedirs(path, exist_ok=True)
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as exc:
        messagebox.showerror("数据目录", f"无法打开数据目录：{exc}", parent=self.root)


def sources(self):
    w = _new_window(self, "来源图片结构", "1100x620", (800, 480))
    cols = ("date", "image", "path", "include", "note")
    tree = ttk.Treeview(w, columns=cols, show="headings")
    headings = {"date":"日期", "image":"来源图片", "path":"来源路径", "include":"纳入", "note":"备注"}
    widths = {"date":110, "image":220, "path":420, "include":80, "note":220}
    for c in cols:
        tree.heading(c, text=headings[c])
        tree.column(c, width=widths[c], anchor="w")
    y = ttk.Scrollbar(w, orient="vertical", command=tree.yview)
    x = ttk.Scrollbar(w, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
    tree.grid(row=0,column=0,sticky="nsew")
    y.grid(row=0,column=1,sticky="ns")
    x.grid(row=1,column=0,sticky="ew")
    w.grid_rowconfigure(0,weight=1)
    w.grid_columnconfigure(0,weight=1)
    for r in getattr(self.s, "manifest", []):
        tree.insert("", "end", values=(r.get("data_date",""), r.get("source_image",""), r.get("source_path",""), r.get("include",""), r.get("note", "")))
    ttk.Button(w, text="关闭", command=w.destroy).grid(row=2,column=0,pady=8)
    w.bind("<Escape>", lambda _e: w.destroy())


def show_favorites(self):
    rows = self.fav.dedupe()
    w = _new_window(self, "⭐ 我的收藏", "1500x760", (1050, 560))
    ttk.Label(w, text=f"收藏内容 · {len(rows)} 条 · 按型号分组，日期倒序", font=("微软雅黑",12,"bold")).pack(anchor="w", padx=12, pady=10)
    f=ttk.Frame(w,padding=(12,0,12,10)); f.pack(fill="both",expand=True)
    cols=[c[0] for c in __import__("phone_search").COLS]
    tree=ttk.Treeview(f,columns=cols,show="headings",selectmode="extended")
    for c,h,width in __import__("phone_search").COLS:
        tree.heading(c,text=h)
        tree.column(c,width=width,anchor="w")
    y=ttk.Scrollbar(f,orient="vertical",command=tree.yview)
    x=ttk.Scrollbar(f,orient="horizontal",command=tree.xview)
    tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
    tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")
    f.grid_rowconfigure(0,weight=1); f.grid_columnconfigure(0,weight=1)
    mapping={}
    index=0
    groups=self.favorite_groups()
    for gi,(_,blocks) in enumerate(groups):
        for bi,block in enumerate(blocks):
            for r in block:
                iid=f"r{index}"; index+=1
                tree.insert("","end",iid=iid,values=[r.get(c,"") for c in cols]); mapping[iid]=r
            if bi<len(blocks)-1:
                iid=f"g{index}"; index+=1
                tree.insert("","end",iid=iid,values=[""]*len(cols)); mapping[iid]=None
        if gi<len(groups)-1:
            for _ in range(2):
                iid=f"g{index}"; index+=1
                tree.insert("","end",iid=iid,values=[""]*len(cols)); mapping[iid]=None

    def selected_rows():
        return [mapping[iid] for iid in tree.selection() if mapping.get(iid)]

    def all_rows():
        return [r for r in mapping.values() if r]

    bar=ttk.Frame(w,padding=(12,0,12,10)); bar.pack(fill="x")
    ttk.Button(bar,text="查看详情",command=lambda:self.detail_rows(selected_rows() or all_rows())).pack(side="left",padx=4)
    ttk.Button(bar,text="移除收藏",command=lambda:self._remove_favorite_rows(w,selected_rows())).pack(side="left",padx=4)
    ttk.Button(bar,text="复制",command=lambda:self.copy_popup(selected_rows() or all_rows())).pack(side="left",padx=4)
    ttk.Button(bar,text="导出CSV",command=lambda:self.export_popup(selected_rows() or all_rows(),False)).pack(side="left",padx=4)
    ttk.Button(bar,text="导出Excel",command=lambda:self.export_popup(selected_rows() or all_rows(),True)).pack(side="left",padx=4)
    ttk.Button(bar,text="关闭",command=w.destroy).pack(side="right",padx=4)
    tree.bind("<Double-1>",lambda _e:self.detail_rows(selected_rows()))
    tree.bind("<Button-3>",lambda e:self._favorite_popup_menu(e,tree,mapping,w))
    w.bind("<Escape>",lambda _e:w.destroy())


def _remove_favorite_rows(self, window, rows):
    if not rows:
        return messagebox.showinfo("我的收藏","请先选择要移除的收藏",parent=window)
    self.fav.remove(rows)
    window.destroy()
    self.show_favorites()
    self.status.config(text=f"已移除收藏 {len(rows)} 条")


def _favorite_popup_menu(self, event, tree, mapping, window):
    iid=tree.identify_row(event.y)
    row=mapping.get(iid) if iid else None
    if not row:
        return
    tree.selection_set(iid)
    menu=tk.Menu(tree,tearoff=False)
    menu.add_command(label="查看详情",command=lambda:self.detail_rows([row]))
    menu.add_command(label="移除收藏",command=lambda:self._remove_favorite_rows(window,[row]))
    menu.add_command(label="复制",command=lambda:self.copy_popup([row]))
    menu.tk_popup(event.x_root,event.y_root)


def stats(self):
    rows = self.selected() or self.rows
    if not rows:
        return messagebox.showinfo("条件统计","没有可统计的结果",parent=self.root)
    from collections import Counter
    by_date=Counter(r.get("data_date","") for r in rows)
    by_cond=Counter(r.get("condition","") for r in rows)
    text=[f"价格记录：{len(rows)} 条", f"型号目标：{len({__import__('phone_search').rid(r) for r in rows})} 个", "", "按日期："]
    text += [f"  {d}: {n} 条" for d,n in sorted(by_date.items(),reverse=True)]
    text += ["", "按价格条件："] + [f"  {c}: {n} 条" for c,n in by_cond.most_common()]
    messagebox.showinfo("条件统计","\n".join(text),parent=self.root)


def quote(self):
    rows=self.selected() or self.rows
    if not rows:
        return messagebox.showinfo("批量报价","请先选择或查询价格记录",parent=self.root)
    prices=[__import__('phone_search').num(r.get('price','')) for r in rows]
    prices=[p for p in prices if p is not None]
    if not prices:
        return messagebox.showinfo("批量报价","选中记录没有可计算的数字价格",parent=self.root)
    messagebox.showinfo("批量报价",f"记录：{len(rows)} 条\n最低：{min(prices):g}\n最高：{max(prices):g}\n平均：{sum(prices)/len(prices):.2f}",parent=self.root)


def show_compare(self, rows, targets=None):
    """Render comparison without constructing a Toplevel directly."""
    rows = list(rows or [])
    targets = list(targets or rows)
    if not rows:
        return
    history = self.s.history(targets)
    w = _new_window(self, "历史价格对比 · 同型号跨日期", "1650x760", (1100, 600))
    cols = ("date", "model", "condition", "price", "unit")
    frame = ttk.Frame(w, padding=12)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="extended")
    for c,h,wd in (("date","日期",120),("model","型号",320),("condition","价格条件",300),("price","价格",100),("unit","单位",100)):
        tree.heading(c,text=h); tree.column(c,width=wd,anchor="w")
    previous_date = None
    for r in history:
        date = r.get("data_date","")
        if previous_date is not None and date != previous_date:
            tree.insert("","end",values=("","","","",""))
            tree.insert("","end",values=("","","","",""))
        tree.insert("","end",values=(date,r.get("model",""),r.get("condition",""),r.get("price",""),r.get("unit","")))
        previous_date = date
    y=ttk.Scrollbar(frame,orient="vertical",command=tree.yview)
    x=ttk.Scrollbar(frame,orient="horizontal",command=tree.xview)
    tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
    tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")
    frame.grid_rowconfigure(0,weight=1); frame.grid_columnconfigure(0,weight=1)
    buttons=ttk.Frame(w); buttons.pack(pady=(0,8))
    copy_fn=getattr(self,"copy_popup",None)
    export_fn=getattr(self,"export_popup",None)
    if callable(copy_fn):
        ttk.Button(buttons,text="复制",command=lambda:copy_fn(history)).pack(side="left",padx=4)
    if callable(export_fn):
        ttk.Button(buttons,text="导出CSV",command=lambda:export_fn(history,False)).pack(side="left",padx=4)
        ttk.Button(buttons,text="导出Excel",command=lambda:export_fn(history,True)).pack(side="left",padx=4)
    ttk.Button(buttons,text="关闭",command=w.destroy).pack(side="left",padx=4)
    w.bind("<Escape>",lambda _e:w.destroy())


def detail_rows(self, rs):
    """Show raw fields for the first selected result using the window factory."""
    rows = list(rs or [])
    if not rows:
        return
    row = rows[0]
    w = _new_window(self, "记录详情", "760x560", (600, 420))
    text=tk.Text(w,wrap="none",font=("微软雅黑",10))
    text.pack(fill="both",expand=True,padx=12,pady=12)
    for field in __import__('phone_search').FIELDS:
        text.insert("end",f"{field}: {row.get(field,'')}\n")
    text.configure(state="disabled")
    ttk.Button(w,text="关闭",command=w.destroy).pack(pady=(0,8))
    w.bind("<Escape>",lambda _e:w.destroy())


def compare(self):
    rows=self.selected() or self.rows
    if not rows:
        return messagebox.showinfo("历史价格对比","请先选择或查询记录",parent=self.root)
    return show_compare(self, rows, rows)


def detail(self,event=None):
    iid=self.tree.identify_row(event.y) if event is not None else (self.tree.selection()[0] if self.tree.selection() else "")
    row=self.map.get(iid) if iid else None
    if not row:
        return
    return detail_rows(self,[row])


def menu(self,event):
    iid=self.tree.identify_row(event.y); row=self.map.get(iid) if iid else None
    if not row:
        return
    self.tree.selection_set(iid)
    m=tk.Menu(self.root,tearoff=False)
    m.add_command(label="添加收藏",command=lambda:self.addToFavorites([row]))
    m.add_command(label="复制选中",command=self.copy)
    m.add_command(label="查看详情",command=self.detail)
    m.tk_popup(event.x_root,event.y_root)


def install(App):
    actions={
        "open_dir":open_dir,
        "sources":sources,
        "show_favorites":show_favorites,
        "stats":stats,
        "quote":quote,
        "compare":compare,
        "show_compare":show_compare,
        "detail":detail,
        "detail_rows":detail_rows,
        "menu":menu,
        "addToFavorites":addToFavorites,
        "add_favorite":add_favorite,
        "_remove_favorite_rows":_remove_favorite_rows,
        "_favorite_popup_menu":_favorite_popup_menu,
    }
    for name,fn in actions.items():
        setattr(App,name,fn)
    _install_window_lifecycle(App)
