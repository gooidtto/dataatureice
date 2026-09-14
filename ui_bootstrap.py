"""Tk UI bootstrap for the stable SearchApp result/favorites surface."""
from __future__ import annotations

import tkinter as tk
from queue import Empty
from tkinter import ttk

import phone_search
from app_actions import install as install_app_actions
from search_display import build_result_blocks, group_model_dates


_MODEL_PALETTE = ("#eef7ff", "#f5efff", "#eefaf2", "#fff7e8", "#f3f3f3")
_UI_QUEUE = __import__("queue").Queue()


def _new_window(self, title, geometry=None, minsize=None):
    w = tk.Toplevel(self.root)
    w.title(title)
    if geometry:
        w.geometry(geometry)
    if minsize:
        w.minsize(*minsize)
    try:
        w.transient(self.root)
        w.lift()
        w.focus_force()
    except tk.TclError:
        pass
    return w


class SearchApp(phone_search.App):
    _new_window = _new_window

    def ui(self):
        phone_search.App.ui(self)
        self.tree.grid_remove()
        host = self.tree.master
        self._results_canvas = tk.Canvas(host, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(host, orient="vertical", command=self._results_canvas.yview)
        self._results_canvas.configure(yscrollcommand=scrollbar.set)
        self._results_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        host.grid_rowconfigure(0, weight=1)
        host.grid_columnconfigure(0, weight=1)
        self._results_inner = tk.Frame(self._results_canvas, bd=0, highlightthickness=0)
        self._results_window = self._results_canvas.create_window((0, 0), window=self._results_inner, anchor="nw")
        self._results_inner.bind("<Configure>", lambda _e: self._results_canvas.configure(scrollregion=self._results_canvas.bbox("all")))
        self._results_canvas.bind("<Configure>", self._resize_results_inner)
        self.empty_hint = ttk.Label(host, text="输入品牌、系列、型号开始查询", font=("微软雅黑", 12))
        self._result_views = []
        self._result_trees = []
        self._result_tree_map = {}
        self._result_order = []
        self._matrix_map = {}
        self._display_columns = ()

    def _resize_results_inner(self, event):
        try:
            self._results_canvas.itemconfigure(self._results_window, width=event.width)
        except tk.TclError:
            pass

    def _new_window(self, title, geometry=None, minsize=None):
        return _new_window(self, title, geometry, minsize)

    def _result_double_click(self, iid):
        payload = self._matrix_map.get(iid) or {}
        rows = list(payload.get("_rows") or [])
        if rows:
            self.detail_rows(rows)
        return "break"


def _clear_result_views(self):
    for frame in getattr(self, "_result_views", []):
        try:
            frame.destroy()
        except tk.TclError:
            pass
    self._result_views = []
    self._result_trees = []
    self._result_tree_map = {}
    self._result_order = []


def _row_tag(model_index, period_index):
    return f"m{model_index}d{period_index}"


def _configure_result_tree(tree, columns, iid, display, favorite):
    fields = [c[0] for c in columns] + ["favorite"]
    tree.configure(columns=fields, show="headings", height=1, selectmode="none")
    for field, title, width in columns:
        tree.heading(field, text=title)
        is_quote = field.startswith("condition_")
        tree.column(field, width=width, minwidth=max(60, min(width, 90)), anchor="center" if field == "data_date" or is_quote else "w", stretch=False)
    tree.heading("favorite", text="收藏")
    tree.column("favorite", width=110, minwidth=90, anchor="center", stretch=False)
    values = [display.get(field, "") for field, _, _ in columns]
    tag = _row_tag(display["_model_index"], display["_period_index"])
    tree.insert("", "end", iid=iid, values=values + ["★ 已收藏" if favorite else "☆ 一键收藏"], tags=(tag,))
    tree.tag_configure(tag, background=_MODEL_PALETTE[display["_model_index"] % len(_MODEL_PALETTE)])


def _render_search_matrix(self, result):
    _clear_result_views(self)
    self.map = {}
    self._matrix_map = {}
    self._display_columns = ()
    # SearchService order is authoritative. Rendering only groups contiguous runs.
    blocks = build_result_blocks(list(result or []))
    parent = getattr(self, "_results_inner", None)
    if parent is None:
        self.rows = list(result or [])
        return
    previous_model = None
    for block in blocks:
        model_index = block["_model_index"]
        period_index = block["_period_index"]
        if previous_model is not None and model_index != previous_model:
            for _ in range(2):
                spacer = tk.Frame(parent, height=8)
                spacer.pack(fill="x")
                self._result_views.append(spacer)
        elif period_index > 0:
            spacer = tk.Frame(parent, height=4)
            spacer.pack(fill="x")
            self._result_views.append(spacer)
        columns = tuple(block.get("_columns") or ())
        if columns:
            self._display_columns = columns
        iid = f"result-{len(self._matrix_map)}"
        rows = list(block.get("_rows") or [])
        favorite_keys = {self.fav.identity(r) for r in self.fav.dedupe()}
        favorite = any(self.fav.identity(r) in favorite_keys for r in rows)
        frame = tk.Frame(parent, bd=0, highlightthickness=0)
        tree = ttk.Treeview(frame, columns=(), show="headings", height=1, selectmode="none")
        _configure_result_tree(tree, columns, iid, block, favorite)
        # Search is display-only: no selection, drag, context menu, or inline favorite action.
        tree.bind("<Double-1>", lambda _event, iid=iid: self._result_double_click(iid))
        tree.pack(fill="x", expand=True)
        frame.pack(fill="x", expand=True, pady=(0, 2))
        self._result_views.append(frame)
        self._result_trees.append(tree)
        self._result_tree_map[iid] = tree
        self._result_order.append(iid)
        self._matrix_map[iid] = block
        first = rows[0] if rows else {}
        hidden_values = [first.get(c, "") for c in phone_search.COLS] + ["★ 已收藏" if favorite else "☆ 一键收藏"]
        try:
            self.tree.insert("", "end", iid=iid, values=hidden_values)
        except tk.TclError:
            pass
        if rows:
            self.map[iid] = rows[0]
            for row in rows:
                rid = phone_search.rid(row)
                if rid:
                    self.map[rid] = row
        previous_model = model_index
    try:
        self._results_canvas.configure(scrollregion=self._results_canvas.bbox("all"))
    except (AttributeError, tk.TclError):
        pass
    try:
        if self._matrix_map:
            self.empty_hint.place_forget()
        else:
            self.empty_hint.place(relx=0.5, rely=0.5, anchor="center")
    except tk.TclError:
        pass


def favorite_groups(self):
    """Return favorite groups in stored order; grouping never re-sorts records."""
    return group_model_dates(self.fav.dedupe())


def _poll_async_results(self):
    try:
        while True:
            query_id, q, record_history, future = _UI_QUEUE.get_nowait()
            _apply_async_result(self, query_id, q, record_history, future)
    except Empty:
        pass
    try:
        self.root.after(25, lambda: _poll_async_results(self))
    except tk.TclError:
        pass


def _apply_async_result(self, query_id, q, record_history, future):
    if query_id != getattr(self, "_search_query_id", 0):
        return
    try:
        result = future.result()
    except Exception as exc:
        self.status.config(text=f"搜索失败：{type(exc).__name__}: {exc}")
        return
    self.rows = list(result or [])
    if record_history:
        self.h.add(q)
    self.render(self.rows)
    count = len(getattr(self, "_matrix_map", {}) or {})
    self.target.config(text=f"搜索结果：{q} · {count} 个结果块")
    self.status.config(text=f"找到 {count} 个结果块")


def _queue_async_result(query_id, q, record_history, future):
    _UI_QUEUE.put((query_id, q, record_history, future))


def _debounced_search(self):
    try:
        self.root.after_cancel(self._search_after_id)
    except Exception:
        pass
    self._search_after_id = self.root.after(180, lambda: self.search(False))


def clear_search(self):
    try:
        self.root.after_cancel(self._search_after_id)
    except Exception:
        pass
    try:
        self.root.after_cancel(self._sync_search_after_id)
    except Exception:
        pass
    self._search_query_id = getattr(self, "_search_query_id", 0) + 1
    self.q.set("")
    self.hide_suggestions()
    self.rows = []
    self.map = {}
    self._matrix_map = {}
    self._display_columns = ()
    try:
        self.tree.delete(*self.tree.get_children())
    except tk.TclError:
        pass
    _clear_result_views(self)
    self.target.config(text="输入品牌、系列、型号开始查询")
    try:
        self.empty_hint.place(relx=0.5, rely=0.5, anchor="center")
    except tk.TclError:
        pass
    self.status.config(text="请输入品牌、系列、型号或别名")
    self.entry.focus_set()


install_app_actions(SearchApp)
SearchApp.render = _render_search_matrix
SearchApp.favorite_groups = favorite_groups
SearchApp.clear_search = clear_search
SearchApp._poll_async_results = _poll_async_results
SearchApp._apply_async_result = _apply_async_result
SearchApp._queue_async_result = _queue_async_result
SearchApp._debounced_search = _debounced_search


if __name__ == "__main__":
    root = tk.Tk()
    app = SearchApp(root)
    root.mainloop()
