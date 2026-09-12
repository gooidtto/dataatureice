"""Windows release bootstrap with unified dynamic result presentation."""
import os
import re
import tkinter as tk
from tkinter import ttk
import phone_search
from app_actions import install as install_app_actions
from app_actions_fix import install_fix as install_app_action_fixes
from search_display import build_display_columns, normalize_search_results
from value_order import sort_rows

phone_search.CAT["手机配件"] = "手机配件"
_EMPTY_HINT = "输入品牌 / 系列 / 型号开始查询\n\n数据来自已验证的图片事实价格库"
_original_ui = phone_search.App.ui
_original_tree_click = getattr(phone_search.App, "on_tree_click", None)
_real_toplevel = phone_search.tk.Toplevel


def _canonical_store_load(self):
    self.rows = []; self.snapshots = {}; self.manifest = []; self.errors = []
    db = os.path.join(self.d, 'database'); loaded_dates = set()
    def load_paths(date, paths):
        data = []; seen = set()
        for p in paths:
            try: rows = phone_search.read_csv(p)
            except Exception as e: self.errors.append(f'{date}: {e}'); continue
            for raw in rows:
                r = {k: phone_search.clean(raw.get(k, '')) for k in phone_search.FIELDS}; r['category'] = phone_search.CAT.get(r['category'], r['category'])
                if r['data_date'] != date: self.errors.append(f'{date}: data_date不一致')
                if r['category'] not in phone_search.CAT.values(): self.errors.append(f'{date}: 非标准分类 {r["category"]}')
                if not phone_search.valid(r): continue
                rid = r['record_id']
                if rid in seen: self.errors.append(f'{date}: 重复 record_id {rid}'); continue
                seen.add(rid); data.append(r)
        self.snapshots[date] = data; self.rows.extend(data)
    if os.path.isdir(db):
        for date in sorted(os.listdir(db)):
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date): continue
            folder = os.path.join(db, date)
            if not os.path.isdir(folder): continue
            paths = [os.path.join(folder, n) for n in sorted(os.listdir(folder)) if n.lower().endswith('.csv') and os.path.isfile(os.path.join(folder, n))]
            if paths: load_paths(date, paths); loaded_dates.add(date)
    sd = os.path.join(self.d, 'snapshots')
    if os.path.isdir(sd):
        for date in sorted(os.listdir(sd)):
            if date in loaded_dates or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date): continue
            folder = os.path.join(sd, date)
            if not os.path.isdir(folder): continue
            paths = [os.path.join(folder, n) for n in sorted(os.listdir(folder)) if n.lower().endswith('.csv')]
            if paths: load_paths(date, paths)
    mp = os.path.join(self.d, 'source_image_manifest.csv')
    if os.path.isfile(mp):
        try: self.manifest = phone_search.read_csv(mp)
        except Exception as e: self.errors.append(f'来源清单: {e}')


def _clear_result_views(self):
    for tree in getattr(self, '_result_trees', []):
        try: tree.destroy()
        except tk.TclError: pass
    self._result_trees = []
    self._result_tree_map = {}
    self._result_order = []
    if hasattr(self, '_results_inner'):
        try: self._results_inner.update_idletasks(); self._results_canvas.configure(scrollregion=self._results_canvas.bbox('all'))
        except tk.TclError: pass


def clear_search(self):
    if getattr(self, '_search_after_id', None):
        try: self.root.after_cancel(self._search_after_id)
        except tk.TclError: pass
        self._search_after_id = None
    self.q.set(''); self.hide_suggestions(); self.rows = []; self.map = {}; self._matrix_map = {}; self._display_columns = (); self.tree.delete(*self.tree.get_children()); _clear_result_views(self); self.target.config(text='输入品牌 / 系列 / 型号开始查询')
    if hasattr(self, 'empty_hint'): self.empty_hint.place(relx=0.5, rely=0.5, anchor='center')
    self.status.config(text='请输入品牌、系列、型号或别名'); self.entry.focus_set()


# One solid color per real-world model group. Different dates of the same
# model stay in the same visual group; a blank row separates the periods.
_MODEL_PALETTE = (
    '#EEB5B5', '#EED1B5', '#EEEEB5', '#D1EEB5',
    '#B5EEB5', '#B5EED1', '#B5EEEE', '#B5D1EE',
    '#B5B5EE', '#D1B5EE', '#EEB5EE', '#EEB5D1',
)


def _row_tag(model_index, period_index):
    return f'model_{model_index}_period_{period_index}', _MODEL_PALETTE[model_index % len(_MODEL_PALETTE)]


def _fit_main_width(self, column_sets):
    """Fit the main window to the widest independent result block."""
    try:
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        widest = 0
        for columns in column_sets or ():
            widest = max(widest, sum(max(70, int(width)) for _, _, width in columns) + 110)
        desired = widest + 44
        width = min(max(1050, desired), max(1050, screen_w - 24))
        current_h = max(self.root.winfo_height(), 720)
        x = max(12, (screen_w - width) // 2)
        self.root.geometry(f'{width}x{current_h}+{x}+12')
    except tk.TclError:
        pass


def _configure_result_tree(tree, columns, iid, display, favorite):
    fields = [c[0] for c in columns] + ['favorite']
    tree.configure(columns=fields, show='headings', height=1, selectmode='browse')
    for field, title, width in columns:
        tree.heading(field, text=title)
        tree.column(field, width=width, minwidth=max(60, min(width, 90)), anchor='center' if field == 'data_date' else 'w', stretch=False)
    tree.heading('favorite', text='收藏')
    tree.column('favorite', width=110, minwidth=90, anchor='center', stretch=False)
    values = [display.get(field, '') for field, _title, _width in columns]
    tree.insert('', 'end', iid=iid, values=values + ['★ 已收藏' if favorite else '☆ 一键收藏'], tags=(_row_tag(display['_model_index'], display['_period_index'])[0],))
    tree.tag_configure(_row_tag(display['_model_index'], display['_period_index'])[0], background=_MODEL_PALETTE[display['_model_index'] % len(_MODEL_PALETTE)])
    requested_chars = max(20, (sum(max(70, int(width)) for _, _, width in columns) + 110) // 8)
    tree.configure(width=requested_chars)


def _sync_result_selection(self):
    selected = set(self.tree.selection())
    for tree in getattr(self, '_result_trees', []):
        for iid in tree.get_children():
            if iid in selected: tree.selection_set(iid)
            else: tree.selection_remove(iid)


def _select_result_iid(self, iid, ctrl=False, shift=False):
    if iid not in self._result_tree_map: return
    old_anchor = getattr(self, '_search_selection_anchor', None)
    if shift and old_anchor in self._result_order:
        a = self._result_order.index(old_anchor); b = self._result_order.index(iid)
        chosen = self._result_order[min(a,b):max(a,b)+1]
        self.tree.selection_set(chosen)
    elif ctrl:
        if iid in self.tree.selection(): self.tree.selection_remove(iid)
        else: self.tree.selection_add(iid)
        self._search_selection_anchor = iid
    else:
        self.tree.selection_set(iid)
        self._search_selection_anchor = iid
    _sync_result_selection(self)


def _result_click(self, event):
    tree = event.widget
    iid = tree.identify_row(event.y)
    if not iid or iid not in self._result_tree_map: return 'break'
    self._active_result_tree = tree
    self._active_result_iid = iid
    column = tree.identify_column(event.x)
    favorite_column = f'#{len(getattr(self._result_tree_map[iid], "_columns", ())) + 1}' if False else None
    columns = self._result_tree_map[iid].get('_columns', ())
    favorite_column = f'#{len(columns) + 1}'
    ctrl = bool(event.state & 0x0004); shift = bool(event.state & 0x0001)
    if column == favorite_column:
        _select_result_iid(self, iid, ctrl=ctrl, shift=shift)
        _toggle_matrix_favorite(self, iid, self._matrix_map.get(iid) or {})
        return 'break'
    _select_result_iid(self, iid, ctrl=ctrl, shift=shift)
    return 'break'


def _result_double_click(self, event):
    tree = event.widget; iid = tree.identify_row(event.y)
    if not iid or iid not in self._result_tree_map: return 'break'
    self._active_result_tree = tree; self._active_result_iid = iid
    self.detail(event)
    return 'break'


def _result_context_menu(self, event):
    tree = event.widget; iid = tree.identify_row(event.y)
    if not iid or iid not in self._result_tree_map: return 'break'
    _select_result_iid(self, iid, ctrl=False, shift=False)
    self._active_result_tree = tree; self._active_result_iid = iid
    menu = tk.Menu(self.root, tearoff=False)
    menu.add_command(label='查看详细信息', command=self.detail)
    menu.add_command(label='添加收藏', command=lambda: self.addToFavorites(self._matrix_map[iid].get('_rows', [])))
    menu.add_command(label='复制选中', command=self.copy)
    menu.add_command(label='历史价格对比', command=self.compare)
    menu.tk_popup(event.x_root, event.y_root)
    return 'break'


def _render_search_matrix(self, result):
    display_rows = normalize_search_results(sort_rows(result))
    self.rows = result; self.map = {}; self._matrix_map = {}; self._display_columns = ()
    self.tree.delete(*self.tree.get_children()); _clear_result_views(self)
    self._result_tree_map = {}; self._result_order = []; self._search_selection_anchor = None
    block_columns = []
    for display_index, display in enumerate(display_rows):
        if display.get('_separator'):
            height = 18 if display.get('_separator') == 'period' else 28
            spacer = tk.Frame(self._results_inner, height=height, bg='#ffffff')
            spacer.pack(fill='x'); spacer.pack_propagate(False)
            continue
        raw_rows = display.get('_rows', []); columns = display.get('_columns') or build_display_columns(raw_rows)
        block_columns.append(columns)
        iid = f'result_{display_index}'
        frame = ttk.Frame(self._results_inner, padding=(0, 0, 0, 2))
        frame.pack(fill='x', pady=(0, 2))
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns] + ['favorite'], show='headings', height=1, selectmode='browse')
        _configure_result_tree(tree, columns, iid, display, bool(raw_rows) and all(self.fav.has(r) for r in raw_rows))
        tree.pack(fill='x', expand=False)
        tree.bind('<Button-1>', lambda e, self=self: _result_click(self, e), add='+')
        tree.bind('<Double-1>', lambda e, self=self: _result_double_click(self, e), add='+')
        tree.bind('<Button-3>', lambda e, self=self: _result_context_menu(self, e), add='+')
        self._result_trees.append(tree); self._result_tree_map[iid] = display; self._result_order.append(iid)
        representative = raw_rows[0] if raw_rows else {}
        self.map[iid] = representative; self._matrix_map[iid] = display
        self.tree.insert('', 'end', iid=iid, values=(display.get('data_date', ''),))
    _fit_main_width(self, block_columns)
    try:
        self._results_inner.update_idletasks(); self._results_canvas.configure(scrollregion=self._results_canvas.bbox('all'))
    except tk.TclError: pass
    self._display_columns = tuple(block_columns[0]) if len(block_columns) == 1 else ()
    return display_rows


def _results_mousewheel(self, event):
    try:
        self._results_canvas.yview_scroll(-1 * int(event.delta / 120), 'units')
    except (tk.TclError, ZeroDivisionError): pass


def ui(self):
    _original_ui(self)
    host = self.tree.master
    self.tree.grid_remove()
    for child in host.winfo_children():
        if isinstance(child, ttk.Scrollbar): child.grid_remove()
    self._results_canvas = tk.Canvas(host, highlightthickness=0, borderwidth=0, bg='#ffffff')
    self._results_inner = tk.Frame(self._results_canvas, bg='#ffffff', borderwidth=0, highlightthickness=0)
    self._results_window = self._results_canvas.create_window((0, 0), window=self._results_inner, anchor='nw')
    self._results_y = ttk.Scrollbar(host, orient='vertical', command=self._results_canvas.yview)
    self._results_x = ttk.Scrollbar(host, orient='horizontal', command=self._results_canvas.xview)
    self._results_canvas.configure(yscrollcommand=self._results_y.set, xscrollcommand=self._results_x.set)
    self._results_canvas.grid(row=0, column=0, sticky='nsew'); self._results_y.grid(row=0, column=1, sticky='ns'); self._results_x.grid(row=1, column=0, sticky='ew')
    host.grid_rowconfigure(0, weight=1); host.grid_columnconfigure(0, weight=1)
    self._results_inner.bind('<Configure>', lambda _e: self._results_canvas.configure(scrollregion=self._results_canvas.bbox('all')))
    self._results_canvas.bind('<Configure>', lambda e: self._results_canvas.itemconfigure(self._results_window, width=max(e.width, self._results_inner.winfo_reqwidth())))
    self._result_trees = []; self._result_tree_map = {}; self._result_order = []
    self.empty_hint = tk.Label(host, text=_EMPTY_HINT, font=('微软雅黑', 15), justify='center', fg='#666666', bg='#ffffff', padx=28, pady=22)
    self.empty_hint.place(relx=0.5, rely=0.5, anchor='center'); self._matrix_map = {}; self._display_columns = (); self._search_after_id = None
    self.q.trace_add('write', lambda *_: _schedule_search(self))
    self.root.bind_all('<MouseWheel>', lambda e, self=self: _results_mousewheel(self, e), add='+')
    self.root.bind('<Control-a>', lambda _e: (self.tree.selection_set(self._result_order), _sync_result_selection(self), 'break')[-1], add='+')
    self.root.bind('<Control-A>', lambda _e: (self.tree.selection_set(self._result_order), _sync_result_selection(self), 'break')[-1], add='+')


def _schedule_search(self):
    """Run a search two seconds after typing stops."""
    if getattr(self, '_search_after_id', None):
        try: self.root.after_cancel(self._search_after_id)
        except tk.TclError: pass
    q = phone_search.clean(self.q.get())
    if not q:
        self._search_after_id = None
        return
    self._search_after_id = self.root.after(2000, lambda: _debounced_search(self))


def _debounced_search(self):
    self._search_after_id = None
    if phone_search.clean(self.q.get()): self.search()


def search(self, record_history=True):
    q = phone_search.clean(self.q.get())
    if not q:
        self.hide_suggestions(); self.rows = []; self.map = {}; self._matrix_map = {}; self._display_columns = (); self.tree.delete(*self.tree.get_children()); _clear_result_views(self); self.target.config(text='输入品牌 / 系列 / 型号开始查询')
        if hasattr(self, 'empty_hint'): self.empty_hint.place(relx=0.5, rely=0.5, anchor='center')
        self.status.config(text='请输入品牌、系列、型号或别名'); return []
    if getattr(self, '_search_after_id', None):
        try: self.root.after_cancel(self._search_after_id)
        except tk.TclError: pass
        self._search_after_id = None
    if record_history: self.h.add(q)
    result = self.s.search(q, self.cat.get()); _render_search_matrix(self, result)
    count = sum(1 for payload in self._matrix_map.values() if payload); self.target.config(text=f'搜索结果：{q} · {count} 个结果块'); self.status.config(text=f'找到 {count} 个结果块')
    if hasattr(self, 'empty_hint'):
        if count: self.empty_hint.place_forget()
        else: self.empty_hint.place(relx=0.5, rely=0.5, anchor='center')
    self.refresh_suggestions(); return result


def load(self):
    self.s.load(); self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}')
    q = phone_search.clean(self.q.get())
    if q: self.search(False)
    else:
        self.rows = []; self.map = {}; self._matrix_map = {}; self._display_columns = (); self.tree.delete(*self.tree.get_children()); _clear_result_views(self); self.target.config(text='输入品牌、系列、型号或别名开始查询')
        if hasattr(self, 'empty_hint'): self.empty_hint.place(relx=0.5, rely=0.5, anchor='center')
        self.status.config(text='数据已就绪，请输入查询条件')
    self.root.after_idle(self.entry.focus_set); self.root.after_idle(self.show_suggestions)


def _toggle_matrix_favorite(self, iid, payload):
    rows = payload.get('_rows', [])
    if not rows: return
    selected_all = all(self.fav.has(r) for r in rows)
    if selected_all:
        for row in rows: self.fav.remove([row])
    else: self.fav.add(rows)
    _render_search_matrix(self, self.rows)


def favorite_groups(self):
    return normalize_search_results(sort_rows(self.fav.dedupe()))


def _standardize_window(w):
    try:
        if not w.winfo_exists() or bool(w.overrideredirect()): return
        title = phone_search.clean(w.title()); specs = (("搜索历史",560,620,420,420),("我的收藏",1500,760,1050,560),("记录详情",1500,680,1000,500),("历史价格对比",1650,760,1100,600),("来源图片结构",1100,620,800,480)); width,height,min_w,min_h=900,600,640,420
        for marker,sw,sh,smw,smh in specs:
            if marker in title: width,height,min_w,min_h=sw,sh,smw,smh; break
        parent=w.master if getattr(w,'master',None) is not None else w.winfo_toplevel(); parent.update_idletasks(); pw,ph=parent.winfo_width(),parent.winfo_height(); px,py=parent.winfo_rootx(),parent.winfo_rooty(); w.minsize(min_w,min_h); x=max(12,px+(pw-width)//2); y=max(12,py+12); w.geometry(f'{width}x{height}+{x}+{y}'); w.transient(parent.winfo_toplevel()); w.bind('<Escape>',lambda _e:w.destroy(),add='+'); w.protocol('WM_DELETE_WINDOW',w.destroy); w.focus_set()
    except tk.TclError: pass


def standardized_toplevel(*args, **kwargs):
    w = _real_toplevel(*args, **kwargs); w.after_idle(lambda: _standardize_window(w)); return w

install_app_actions(phone_search.App); install_app_action_fixes(phone_search.App)
phone_search.Store.load = _canonical_store_load
phone_search.App.ui = ui; phone_search.App.search = search; phone_search.App.render = _render_search_matrix; phone_search.App.load = load; phone_search.App.clear_search = clear_search; phone_search.App.on_tree_click = _result_click; phone_search.App.favorite_groups = favorite_groups; phone_search.tk.Toplevel = standardized_toplevel

def main():
    root = tk.Tk(); phone_search.App(root); root.mainloop()
if __name__ == '__main__': main()
