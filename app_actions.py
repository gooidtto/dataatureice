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
            _install_search_behavior(self)
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


def _reliable_search(self, record_history=True):
    q = __import__('phone_search').clean(self.q.get())
    if not q:
        return []
    for attr in ("_search_after_id", "_sync_search_after_id"):
        pending = getattr(self, attr, None)
        if pending:
            try:
                self.root.after_cancel(pending)
            except tk.TclError:
                pass
            setattr(self, attr, None)
    self._search_query_id = getattr(self, "_search_query_id", 0) + 1
    self.status.config(text="正在搜索…")
    try:
        result = self.s.search(q, self.cat.get())
        self.rows = list(result or [])
        if record_history:
            self.h.add(q)
        renderer = getattr(self, "render", None)
        if not callable(renderer):
            raise RuntimeError("SearchApp result renderer is unavailable")
        renderer(self.rows)
        count = len(getattr(self, "_matrix_map", {}) or {})
        self.target.config(text=f"搜索结果：{q} · {count} 个结果块")
        self.status.config(text=f"找到 {count} 个结果块")
        if hasattr(self, "empty_hint"):
            if count:
                self.empty_hint.place_forget()
            else:
                self.empty_hint.place(relx=0.5, rely=0.5, anchor="center")
        _refresh_suggestions(self)
        return self.rows
    except Exception as exc:
        self.status.config(text=f"搜索失败：{type(exc).__name__}: {exc}")
        return []


def _install_search_behavior(self):
    """Typing only updates suggestions; Search button or Enter performs the query."""
    q = getattr(self, "q", None)
    if q is None:
        return
    try:
        for mode, callback in q.trace_info():
            if mode == "write":
                q.trace_remove(mode, callback)
    except (AttributeError, tk.TclError):
        pass

    def on_change(*_args):
        _refresh_suggestions(self)

    q.trace_add("write", on_change)
    self._sync_search_after_id = None


def _suggestion_window(self):
    popup = getattr(self, "suggest_popup", None)
    try:
        if popup is not None and popup.winfo_exists():
            return popup
    except tk.TclError:
        pass
    try:
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.transient(self.root)
        popup.configure(bg="#d9d9d9")
        popup.attributes("-topmost", False)
        self.suggest_popup = popup
        return popup
    except tk.TclError:
        self.suggest_popup = None
        return None


def _refresh_suggestions(self):
    """Render the unified search-history/suggestion layer directly below the search box."""
    if not hasattr(self, "entry") or not hasattr(self, "h"):
        return
    items = self.h.suggestions(__import__('phone_search').clean(self.q.get()), 5)
    if not items:
        _hide_suggestions(self)
        return
    popup = _suggestion_window(self)
    if popup is None:
        return
    try:
        for child in popup.winfo_children():
            child.destroy()
        outer = tk.Frame(popup, bg="#d9d9d9", bd=0, highlightthickness=0)
        outer.pack(fill="both", expand=True)
        header = tk.Label(outer, text="搜索历史 / 建议", anchor="w", bg="#f5f5f5", fg="#555555", font=("微软雅黑", 9), padx=10, pady=5)
        header.pack(fill="x")
        body = tk.Frame(outer, bg="white", bd=1, relief="solid")
        body.pack(fill="both", expand=True)
        for item in items:
            button = tk.Label(body, text=item, anchor="w", bg="white", fg="#222222", font=("微软雅黑", 11), padx=10, pady=7, cursor="hand2")
            button.pack(fill="x")
            button.bind("<Button-1>", lambda _e, value=item: _use_suggestion(self, value))
            button.bind("<Enter>", lambda _e, widget=button: widget.configure(bg="#f0f0f0"))
            button.bind("<Leave>", lambda _e, widget=button: widget.configure(bg="white"))
        popup.update_idletasks()
        width = max(420, self.entry.winfo_width())
        height = 34 + len(items) * 39 + 2
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.lift()
    except tk.TclError:
        _hide_suggestions(self)


def _show_suggestions(self):
    _refresh_suggestions(self)


def _use_suggestion(self, value):
    self.q.set(value)
    _hide_suggestions(self)
    self.search()


def _hide_suggestions(self):
    popup = getattr(self, "suggest_popup", None)
    if popup is not None:
        try:
            popup.destroy()
        except tk.TclError:
            pass
    self.suggest_popup = None


def _dismiss_suggestions(self, event=None):
    if event is None or getattr(self, "suggest_popup", None) is None:
        return
    try:
        ex, ey = event.x_root, event.y_root
        px, py = self.entry.winfo_rootx(), self.entry.winfo_rooty()
        if px <= ex <= px + self.entry.winfo_width() and py <= ey <= py + self.entry.winfo_height():
            _refresh_suggestions(self)
            return
        popup = self.suggest_popup
        x1, y1 = popup.winfo_rootx(), popup.winfo_rooty()
        x2, y2 = x1 + popup.winfo_width(), y1 + popup.winfo_height()
        if x1 <= ex <= x2 and y1 <= ey <= y2:
            return
    except tk.TclError:
        pass
    _hide_suggestions(self)


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
    tree.grid(row=0, column=0, sticky="nsew")
    y.grid(row=0, column=1, sticky="ns")
    x.grid(row=1, column=0, sticky="ew")
    w.grid_rowconfigure(0, weight=1)
    w.grid_columnconfigure(0, weight=1)
    for r in getattr(self.s, "manifest", []):
        tree.insert("", "end", values=(r.get("data_date", ""), r.get("source_image", ""), r.get("source_path", ""), r.get("include", ""), r.get("note", "")))
    ttk.Button(w, text="关闭", command=w.destroy).grid(row=2, column=0, pady=8)
    w.bind("<Escape>", lambda _e: w.destroy())


def show_favorites(self):
    from favorites_view import show_favorites_matrix
    return show_favorites_matrix(self)


def _remove_favorite_rows(self, window, rows):
    if not rows:
        return messagebox.showinfo("我的收藏", "请先选择要移除的收藏", parent=window)
    self.fav.remove(rows)
    window.destroy()
    self.show_favorites()
    self.status.config(text=f"已移除收藏 {len(rows)} 条")


def _favorite_popup_menu(self, event, tree, mapping, window):
    iid = tree.identify_row(event.y)
    row = mapping.get(iid) if iid else None
    if not row:
        return
    tree.selection_set(iid)
    menu = tk.Menu(tree, tearoff=False)
    menu.add_command(label="查看详情", command=lambda: self.detail_rows([row]))
    menu.add_command(label="移除收藏", command=lambda: self._remove_favorite_rows(window, [row]))
    menu.add_command(label="复制", command=lambda: self.copy_popup([row]))
    menu.tk_popup(event.x_root, event.y_root)


def stats(self):
    rows = self.selected() or self.rows
    if not rows:
        return messagebox.showinfo("条件统计", "没有可统计的结果", parent=self.root)
    from collections import Counter
    by_date = Counter(r.get("data_date", "") for r in rows)
    by_cond = Counter(r.get("condition", "") for r in rows)
    text = [f"价格记录：{len(rows)} 条", f"型号目标：{len({__import__('phone_search').rid(r) for r in rows})} 个", "", "按日期："]
    text += [f"  {d}: {n} 条" for d, n in sorted(by_date.items(), reverse=True)]
    text += ["", "按价格条件："] + [f"  {c}: {n} 条" for c, n in by_cond.most_common()]
    messagebox.showinfo("条件统计", "\n".join(text), parent=self.root)


def quote(self):
    rows = self.selected() or self.rows
    if not rows:
        return messagebox.showinfo("批量报价", "请先选择或查询价格记录", parent=self.root)
    prices = [__import__('phone_search').num(r.get('price', '')) for r in rows]
    prices = [p for p in prices if p is not None]
    if not prices:
        return messagebox.showinfo("批量报价", "选中记录没有可计算的数字价格", parent=self.root)
    messagebox.showinfo("批量报价", f"记录：{len(rows)} 条\n最低：{min(prices):g}\n最高：{max(prices):g}\n平均：{sum(prices)/len(prices):.2f}", parent=self.root)


def show_compare(self, rows, targets=None):
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
    for c, h, wd in (("date", "日期", 120), ("model", "型号", 320), ("condition", "价格条件", 300), ("price", "价格", 100), ("unit", "单位", 100)):
        tree.heading(c, text=h)
        tree.column(c, width=wd, anchor="w")
    previous_date = None
    for r in history:
        date = r.get("data_date", "")
        if previous_date is not None and date != previous_date:
            tree.insert("", "end", values=("", "", "", "", ""))
            tree.insert("", "end", values=("", "", "", "", ""))
        tree.insert("", "end", values=(date, r.get("model", ""), r.get("condition", ""), r.get("price", ""), r.get("unit", "")))
        previous_date = date
    y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
    tree.grid(row=0, column=0, sticky="nsew")
    y.grid(row=0, column=1, sticky="ns")
    x.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    buttons = ttk.Frame(w)
    buttons.pack(pady=(0, 8))
    copy_fn = getattr(self, "copy_popup", None)
    export_fn = getattr(self, "export_popup", None)
    if callable(copy_fn):
        ttk.Button(buttons, text="复制", command=lambda: copy_fn(history)).pack(side="left", padx=4)
    if callable(export_fn):
        ttk.Button(buttons, text="导出CSV", command=lambda: export_fn(history, False)).pack(side="left", padx=4)
        ttk.Button(buttons, text="导出Excel", command=lambda: export_fn(history, True)).pack(side="left", padx=4)
    ttk.Button(buttons, text="关闭", command=w.destroy).pack(side="left", padx=4)
    w.bind("<Escape>", lambda _e: w.destroy())


def detail_rows(self, rs):
    rows = list(rs or [])
    if not rows:
        return
    row = rows[0]
    w = _new_window(self, "记录详情", "760x560", (600, 420))
    text = tk.Text(w, wrap="none", font=("微软雅黑", 10))
    text.pack(fill="both", expand=True, padx=12, pady=12)
    for field in __import__('phone_search').FIELDS:
        text.insert("end", f"{field}: {row.get(field, '')}\n")
    text.configure(state="disabled")
    ttk.Button(w, text="关闭", command=w.destroy).pack(pady=(0, 8))
    w.bind("<Escape>", lambda _e: w.destroy())


def compare(self):
    rows = self.selected() or self.rows
    if not rows:
        return messagebox.showinfo("历史价格对比", "请先选择或查询记录", parent=self.root)
    return show_compare(self, rows, rows)


def detail(self, event=None):
    iid = self.tree.identify_row(event.y) if event is not None else (self.tree.selection()[0] if self.tree.selection() else "")
    row = self.map.get(iid) if iid else None
    if not row:
        return
    return detail_rows(self, [row])


def menu(self, event):
    iid = self.tree.identify_row(event.y)
    row = self.map.get(iid) if iid else None
    if not row:
        return
    self.tree.selection_set(iid)
    m = tk.Menu(self.root, tearoff=False)
    m.add_command(label="添加收藏", command=lambda: self.addToFavorites([row]))
    m.add_command(label="复制选中", command=self.copy)
    m.add_command(label="查看详情", command=self.detail)
    m.tk_popup(event.x_root, event.y_root)


def install(App):
    actions = {
        "open_dir": open_dir,
        "sources": sources,
        "show_favorites": show_favorites,
        "stats": stats,
        "quote": quote,
        "compare": compare,
        "show_compare": show_compare,
        "detail": detail,
        "detail_rows": detail_rows,
        "menu": menu,
        "addToFavorites": addToFavorites,
        "add_favorite": add_favorite,
        "_remove_favorite_rows": _remove_favorite_rows,
        "_favorite_popup_menu": _favorite_popup_menu,
        "show_suggestions": _show_suggestions,
        "refresh_suggestions": _refresh_suggestions,
        "hide_suggestions": _hide_suggestions,
        "dismiss_suggestions": _dismiss_suggestions,
    }
    for name, fn in actions.items():
        setattr(App, name, fn)
    App.search = _reliable_search
    _install_window_lifecycle(App)
