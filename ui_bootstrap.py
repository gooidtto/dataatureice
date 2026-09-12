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


def clear_search(self):
    self.q.set(''); self.hide_suggestions(); self.rows = []; self.map = {}; self._matrix_map = {}; self._display_columns = (); self.tree.delete(*self.tree.get_children()); self.target.config(text='输入品牌 / 系列 / 型号开始查询')
    if hasattr(self, 'empty_hint'): self.empty_hint.place(relx=0.5, rely=0.5, anchor='center')
    self.status.config(text='请输入品牌、系列、型号或别名'); self.entry.focus_set()


# A small palette is assigned per real model. Periods within one model use
# distinct shades so the model remains visually grouped while dates remain distinct.
_MODEL_PALETTE = (
    ('#E8F1FF', '#D5E6FF', '#C1DAFF', '#A9CCFF'),
    ('#EAF7EA', '#D5F0D5', '#BFE6BF', '#A7DBA7'),
    ('#FFF3E0', '#FFE4BD', '#FFD69A', '#FFC875'),
    ('#F3EAFB', '#E7D5F5', '#D9C0EE', '#C9A7E5'),
    ('#E7F7F7', '#CFECEC', '#B5E1E1', '#99D5D5'),
    ('#FFF0F3', '#FFDDE5', '#FFC9D6', '#FFB4C8'),
    ('#F4F4E7', '#E8E8CD', '#DCDCBA', '#CFCF9F'),
    ('#ECECF8', '#DCDCF0', '#CBCBE7', '#B9B9DE'),
)


def _row_tag(model_index, period_index):
    palette = _MODEL_PALETTE[model_index % len(_MODEL_PALETTE)]
    return f'model_{model_index}_period_{period_index}', palette[period_index % len(palette)]


def _configure_dynamic_columns(self, columns):
    tree_columns = [c[0] for c in columns] + ['favorite']
    self.tree.configure(columns=tree_columns)
    for field, title, width in columns:
        self.tree.heading(field, text=title)
        self.tree.column(field, width=width, minwidth=max(60, min(width, 90)), anchor='center' if field == 'data_date' else 'w', stretch=False)
    self.tree.heading('favorite', text='收藏')
    self.tree.column('favorite', width=110, minwidth=90, anchor='center', stretch=False)
    self._display_columns = tuple(columns)


def _render_search_matrix(self, result):
    display_rows = normalize_search_results(sort_rows(result))
    columns = build_display_columns(result)
    self.rows = result; self.map = {}; self._matrix_map = {}; self._display_columns = columns
    self.tree.delete(*self.tree.get_children()); _configure_dynamic_columns(self, columns)
    for display in display_rows:
        if display.get('_separator'):
            iid = self.tree.insert('', 'end', values=[''] * (len(columns) + 1), tags=('model_separator',))
            self.map[iid] = None; self._matrix_map[iid] = None
            continue
        raw_rows = display.get('_rows', []); representative = raw_rows[0] if raw_rows else {}
        iid = self.tree.insert('', 'end', values=[display.get(c, '') for c, _, _ in columns] + ['★ 已收藏' if raw_rows and all(self.fav.has(r) for r in raw_rows) else '☆ 一键收藏'], tags=(_row_tag(display['_model_index'], display['_period_index'])[0],))
        self.map[iid] = representative; self._matrix_map[iid] = display
    try:
        self.tree.tag_configure('model_separator', height=18)
        for model_index in range(len(_MODEL_PALETTE)):
            for period_index in range(4):
                tag, bg = _row_tag(model_index, period_index); self.tree.tag_configure(tag, background=bg)
    except tk.TclError:
        pass
    return display_rows


def ui(self):
    _original_ui(self)
    for widget in self.root.winfo_children():
        if isinstance(widget, ttk.Frame):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Combobox):
                    values = list(child.cget('values'))
                    if '手机配件' not in values: child.configure(values=values + ['手机配件'])
                    break
    self.empty_hint = tk.Label(self.tree.master, text=_EMPTY_HINT, font=('微软雅黑', 15), justify='center', fg='#666666', bg='#ffffff', padx=28, pady=22)
    self.empty_hint.place(relx=0.5, rely=0.5, anchor='center'); self._matrix_map = {}; self._display_columns = ()


def search(self, record_history=True):
    q = phone_search.clean(self.q.get())
    if not q:
        self.hide_suggestions(); self.rows = []; self.map = {}; self._matrix_map = {}; self._display_columns = (); self.tree.delete(*self.tree.get_children()); self.target.config(text='输入品牌 / 系列 / 型号开始查询')
        if hasattr(self, 'empty_hint'): self.empty_hint.place(relx=0.5, rely=0.5, anchor='center')
        self.status.config(text='请输入品牌、系列、型号或别名'); return []
    if record_history: self.h.add(q)
    result = self.s.search(q, self.cat.get()); _render_search_matrix(self, result)
    count = sum(1 for payload in self._matrix_map.values() if payload); self.target.config(text=f'搜索结果：{q} · {count} 个结果块'); self.status.config(text=f'找到 {count} 个结果块')
    if hasattr(self, 'empty_hint'):
        if self._matrix_map: self.empty_hint.place_forget()
        else: self.empty_hint.place(relx=0.5, rely=0.5, anchor='center')
    self.refresh_suggestions(); return result


def load(self):
    self.s.load(); self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}')
    q = phone_search.clean(self.q.get())
    if q: self.search(False)
    else:
        self.rows = []; self.map = {}; self._matrix_map = {}; self._display_columns = (); self.tree.delete(*self.tree.get_children()); self.target.config(text='输入品牌 / 系列 / 型号开始查询')
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


def on_tree_click(self, event):
    region = self.tree.identify('region', event.x, event.y); column = self.tree.identify_column(event.x); iid = self.tree.identify_row(event.y); favorite_column = f'#{len(getattr(self, "_display_columns", ())) + 1}'
    payload = self._matrix_map.get(iid) if iid else None
    if region == 'cell' and column == favorite_column and payload:
        self.tree.selection_set(iid); _toggle_matrix_favorite(self, iid, payload); return 'break'
    if callable(_original_tree_click): return _original_tree_click(self, event)
    return None


def favorite_groups(self):
    # Favorites use exactly the same source-of-truth grouping as search results.
    return normalize_search_results(sort_rows(self.fav.dedupe()))


def _standardize_window(w):
    try:
        if not w.winfo_exists() or bool(w.overrideredirect()): return
        title = phone_search.clean(w.title()); specs = (("搜索历史",560,620,420,420),("我的收藏",1500,760,1050,560),("记录详情",1500,680,1000,500),("历史价格对比",1650,760,1100,600),("来源图片结构",1100,620,800,480)); width,height,min_w,min_h=900,600,640,420
        for marker,sw,sh,smw,smh in specs:
            if marker in title: width,height,min_w,min_h=sw,sh,smw,smh; break
        parent=w.master if getattr(w,'master',None) is not None else w.winfo_toplevel(); parent.update_idletasks(); pw,ph=parent.winfo_width(),parent.winfo_height(); px,py=parent.winfo_rootx(),parent.winfo_rooty(); w.minsize(min_w,min_h); w.geometry(f'{width}x{height}+{max(0,px+(pw-width)//2)}+{max(0,py+(ph-height)//2)}'); w.transient(parent.winfo_toplevel()); w.bind('<Escape>',lambda _e:w.destroy(),add='+'); w.protocol('WM_DELETE_WINDOW',w.destroy); w.focus_set()
    except tk.TclError: pass


def standardized_toplevel(*args, **kwargs):
    w = _real_toplevel(*args, **kwargs); w.after_idle(lambda: _standardize_window(w)); return w

install_app_actions(phone_search.App); install_app_action_fixes(phone_search.App)
phone_search.Store.load = _canonical_store_load
phone_search.App.ui = ui; phone_search.App.search = search; phone_search.App.render = _render_search_matrix; phone_search.App.load = load; phone_search.App.clear_search = clear_search; phone_search.App.on_tree_click = on_tree_click; phone_search.App.favorite_groups = favorite_groups; phone_search.tk.Toplevel = standardized_toplevel

def main():
    root = tk.Tk(); phone_search.App(root); root.mainloop()
if __name__ == '__main__': main()
