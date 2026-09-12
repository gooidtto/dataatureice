"""Unified UI actions sharing the search result data model."""
import tkinter as tk
from tkinter import ttk, messagebox
import unicodedata
import phone_search
from search_core import search_rows
from search_display import build_display_columns, normalize_search_results, column_width
from value_order import sort_rows

# model_code is an authoritative fact and the network-model identifier.
DISPLAY_COLS = [
    ("data_date", "数据日期", 105),
    ("category", "分类", 70),
    ("subtype", "子类型", 75),
    ("brand", "品牌", 110),
    ("series", "系列", 110),
    ("model", "型号", 250),
    ("model_code", "网络型号", 150),
    ("condition", "价格条件", 175),
    ("price", "价格", 85),
    ("unit", "单位", 85),
    ("note", "备注", 260),
    ("source_image", "来源图片", 150),
]
phone_search.COLS = DISPLAY_COLS


def _semantic_search(self, q='', cat='全部'):
    return search_rows(self.rows, q, cat)


def compare(self):
    rows = self.selected() or self.rows
    if not rows: return messagebox.showinfo("历史价格对比", "请先选择或查询记录", parent=self.root)
    history = sort_rows(self.s.history(rows))
    w = tk.Toplevel(self.root); w.title("历史价格对比"); w.geometry("1650x760"); w.minsize(1100,600)
    cols=("date","model","condition","price","unit"); tree=ttk.Treeview(w,columns=cols,show="headings")
    for c,h,wd in (("date","日期",120),("model","型号",320),("condition","价格条件",300),("price","价格",100),("unit","单位",100)):
        tree.heading(c,text=h); tree.column(c,width=wd,anchor="w")
    for r in history: tree.insert("","end",values=(r.get("data_date",""),r.get("model",""),r.get("condition",""),r.get("price",""),r.get("unit","")))
    tree.pack(fill="both",expand=True,padx=12,pady=12); ttk.Button(w,text="关闭",command=w.destroy).pack(pady=(0,8)); w.bind("<Escape>",lambda _e:w.destroy()); w.transient(self.root); w.focus_set()


def _palette_tag(tree, model_index, period_index):
    palettes=(('#E8F1FF','#D5E6FF','#C1DAFF','#A9CCFF'),('#EAF7EA','#D5F0D5','#BFE6BF','#A7DBA7'),('#FFF3E0','#FFE4BD','#FFD69A','#FFC875'),('#F3EAFB','#E7D5F5','#D9C0EE','#C9A7E5'),('#E7F7F7','#CFECEC','#B5E1E1','#99D5D5'),('#FFF0F3','#FFDDE5','#FFC9D6','#FFB4C8'))
    colors=palettes[model_index%len(palettes)]; tag=f'model_{model_index}_period_{period_index}'; tree.tag_configure(tag,background=colors[period_index%len(colors)]); return tag


def _insert_result_blocks(tree, rows, favorite=False):
    displays=normalize_search_results(sort_rows(rows)); columns=build_display_columns(rows); fields=[c[0] for c in columns]
    tree.configure(columns=fields); 
    for field,title,width in columns: tree.heading(field,text=title); tree.column(field,width=width,anchor='center' if field=='data_date' else 'w',stretch=False)
    for display in displays:
        if display.get('_separator'):
            tree.insert('', 'end', values=['']*len(columns), tags=('model_separator',)); continue
        raw=display.get('_rows',[]); values=[display.get(field,'') for field in fields]
        tree.insert('', 'end', values=values, tags=(_palette_tag(tree,display['_model_index'],display['_period_index']),))
    tree.tag_configure('model_separator',height=18)
    return displays, columns


def show_favorites(self):
    rows=self.fav.dedupe(); w=tk.Toplevel(self.root); w.title("⭐ 我的收藏"); w.geometry("1500x760"); w.minsize(1050,560)
    ttk.Label(w,text=f"收藏内容 · {len(rows)} 条 · 与搜索结果统一分组/排序",font=("微软雅黑",12,"bold")).pack(anchor="w",padx=12,pady=10)
    f=ttk.Frame(w,padding=(12,0,12,10)); f.pack(fill="both",expand=True)
    tree=ttk.Treeview(f,columns=("placeholder",),show="headings",selectmode="extended")
    y=ttk.Scrollbar(f,orient="vertical",command=tree.yview); x=ttk.Scrollbar(f,orient="horizontal",command=tree.xview); tree.configure(yscrollcommand=y.set,xscrollcommand=x.set); tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew"); f.grid_rowconfigure(0,weight=1); f.grid_columnconfigure(0,weight=1)
    displays,columns=_insert_result_blocks(tree,rows,True)
    bar=ttk.Frame(w,padding=8); bar.pack(fill="x")
    def remove_selected():
        targets=[]
        for iid in tree.selection():
            payload=displays[int(tree.index(iid))] if tree.index(iid)<len(displays) else None
            if payload and not payload.get('_separator'): targets.extend(payload.get('_rows',[]))
        if targets:
            self.fav.remove(targets); w.destroy(); self.show_favorites()
    ttk.Button(bar,text="移除选中",command=remove_selected).pack(side="left",padx=4); ttk.Button(bar,text="关闭",command=w.destroy).pack(side="right",padx=4); w.bind("<Escape>",lambda _e:w.destroy()); w.transient(self.root); w.focus_set()


def legacy_detail_rows(payload):
    """Return every original source row in canonical real-world value order."""
    return sort_rows(list((payload or {}).get('_rows', [])))


def _detail_columns(rows):
    labels=(('data_date','数据日期'),('category','品类'),('subtype','子类型'),('brand','品牌'),('series','系列'),('model','市场型号'),('model_code','网络型号'),('condition','原始价格条件'),('price','价格'),('unit','单位'),('note','备注'),('origin','来源'),('source_image','来源图片'),('source_path','来源路径'),('verified','已验证'),('confidence','置信度'),('verification','验证说明'),('record_id','记录ID'),('alias','别名'))
    return tuple((field,title,column_width(title,[r.get(field,'') for r in rows],80,360)) for field,title in labels)


def detail(self,event=None):
    iid=self.tree.identify_row(event.y) if event is not None else (self.tree.selection()[0] if self.tree.selection() else "")
    payload=getattr(self,'_matrix_map',{}).get(iid) if iid else None
    if not payload:
        row=self.map.get(iid) if iid and hasattr(self,'map') else None
        if not row:return
        payload={'_rows':[row]}
    rows=legacy_detail_rows(payload); columns=_detail_columns(rows)
    w=tk.Toplevel(self.root); w.title("记录详情 · 全部原始事实"); w.geometry("1650x700"); w.minsize(1100,520)
    ttk.Label(w,text="全部原始事实记录（不合并、不丢失；按现实商品价值排序）",font=("微软雅黑",12,"bold")).pack(anchor="w",padx=12,pady=10)
    f=ttk.Frame(w,padding=(12,0,12,8)); f.pack(fill="both",expand=True); fields=[c[0] for c in columns]
    tree=ttk.Treeview(f,columns=fields,show="headings",selectmode="extended")
    for field,title,width in columns: tree.heading(field,text=title); tree.column(field,width=width,anchor="w",stretch=False)
    y=ttk.Scrollbar(f,orient="vertical",command=tree.yview); x=ttk.Scrollbar(f,orient="horizontal",command=tree.xview); tree.configure(yscrollcommand=y.set,xscrollcommand=x.set); tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew"); f.grid_rowconfigure(0,weight=1); f.grid_columnconfigure(0,weight=1)
    for r in rows: tree.insert('', 'end', values=[r.get(field,'') for field in fields])
    bar=ttk.Frame(w,padding=8); bar.pack(fill='x'); ttk.Button(bar,text='关闭',command=w.destroy).pack(side='right',padx=4); ttk.Button(bar,text='查看完整19字段',command=lambda:self._show_full_raw_record(rows,w)).pack(side='right',padx=4); w.bind('<Escape>',lambda _e:w.destroy()); w.transient(self.root); w.focus_set()


def _show_full_raw_record(self, rows, parent=None):
    rows=sort_rows(rows); w=tk.Toplevel(self.root); w.title("完整事实记录 · 19字段"); w.geometry("1000x680"); w.minsize(760,500)
    text=tk.Text(w,wrap='none',font=('微软雅黑',10)); text.pack(fill='both',expand=True,padx=12,pady=12)
    for idx,r in enumerate(rows,1):
        text.insert('end',f'===== 原始记录 {idx} =====\n')
        for field in phone_search.FIELDS:text.insert('end',f'{field}: {r.get(field,"")}\n')
        text.insert('end','\n')
    text.configure(state='disabled'); ttk.Button(w,text='关闭',command=w.destroy).pack(pady=(0,8)); w.bind('<Escape>',lambda _e:w.destroy()); w.transient(parent or self.root); w.focus_set()


def install_fix(App):
    phone_search.Store.search=_semantic_search; App.compare=compare; App.show_favorites=show_favorites; App.detail=detail; App._show_full_raw_record=_show_full_raw_record
