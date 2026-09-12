"""Second-stage UI action fixes that depend on the canonical Store instance."""
import tkinter as tk
from tkinter import ttk, messagebox
import phone_search
from search_core import search_rows
from value_order import sort_rows

# model_code is an authoritative 19-field fact and also the user's network-model
# identifier. Keep this legacy/detail definition available to auxiliary views.
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
    if not rows:
        return messagebox.showinfo("历史价格对比", "请先选择或查询记录", parent=self.root)
    history = sort_rows(self.s.history(rows))
    w = tk.Toplevel(self.root); w.title("历史价格对比"); w.geometry("1650x760"); w.minsize(1100,600)
    cols=("date","model","condition","price","unit")
    tree=ttk.Treeview(w,columns=cols,show="headings")
    for c,h,wd in (("date","日期",120),("model","型号",320),("condition","价格条件",300),("price","价格",100),("unit","单位",100)):
        tree.heading(c,text=h);tree.column(c,width=wd,anchor="w")
    for r in history: tree.insert("","end",values=(r.get("data_date",""),r.get("model",""),r.get("condition",""),r.get("price",""),r.get("unit","")))
    tree.pack(fill="both",expand=True,padx=12,pady=12);ttk.Button(w,text="关闭",command=w.destroy).pack(pady=(0,8));w.bind("<Escape>",lambda _e:w.destroy());w.transient(self.root);w.focus_set()


def show_favorites(self):
    rows=self.fav.dedupe();w=tk.Toplevel(self.root);w.title("⭐ 我的收藏");w.geometry("1500x760");w.minsize(1050,560)
    ttk.Label(w,text=f"收藏内容 · {len(rows)} 条 · 按现实商品价值排序",font=("微软雅黑",12,"bold")).pack(anchor="w",padx=12,pady=10)
    f=ttk.Frame(w,padding=(12,0,12,10));f.pack(fill="both",expand=True);cols=[c[0] for c in phone_search.COLS];tree=ttk.Treeview(f,columns=cols,show="headings",selectmode="extended")
    for c,h,width in phone_search.COLS:tree.heading(c,text=h);tree.column(c,width=width,anchor="w")
    y=ttk.Scrollbar(f,orient="vertical",command=tree.yview);x=ttk.Scrollbar(f,orient="horizontal",command=tree.xview);tree.configure(yscrollcommand=y.set,xscrollcommand=x.set);tree.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew");f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1)
    groups=self.favorite_groups()
    for gi,(_,blocks) in enumerate(groups):
        for bi,block in enumerate(blocks):
            for r in block:tree.insert("","end",values=[r.get(c,"") for c in cols])
            if bi<len(blocks)-1:tree.insert("","end",values=[""]*len(cols))
        if gi<len(groups)-1:tree.insert("","end",values=[""]*len(cols));tree.insert("","end",values=[""]*len(cols))
    bar=ttk.Frame(w,padding=8);bar.pack(fill="x")
    def remove_selected():
        targets=[]
        for iid in tree.selection():
            vals=tree.item(iid,"values")
            if not vals:continue
            for r in self.fav.dedupe():
                if all(str(r.get(c,""))==str(vals[j]) for j,(c,_,_) in enumerate(phone_search.COLS)):targets.append(r);break
        if targets:self.fav.remove(targets);w.destroy();self.show_favorites()
    ttk.Button(bar,text="移除选中",command=remove_selected).pack(side="left",padx=4);ttk.Button(bar,text="关闭",command=w.destroy).pack(side="right",padx=4);w.bind("<Escape>",lambda _e:w.destroy());w.transient(self.root);w.focus_set()


# Detail records use the same canonical value ordering. Date/price are only
# displayed facts and never determine which real-world condition comes first.
def legacy_detail_rows(payload):
    """Return original raw price rows in canonical real-world value order."""
    rows=list((payload or {}).get("_rows", []))
    return sort_rows(rows)


LEGACY_DETAIL_COLS = (
    ("data_date", "数据日期", 105),
    ("category", "品类", 70),
    ("brand", "品牌", 100),
    ("series", "系列", 150),
    ("model", "市场型号", 260),
    ("model_code", "网络型号", 145),
    ("condition", "成色等级标准项", 190),
    ("price", "价格", 85),
    ("unit", "单位", 85),
    ("source_image", "来源图片", 145),
    ("note", "备注", 220),
)


def detail(self, event=None):
    """Show the original flat price records behind a matrix row in value order."""
    iid=self.tree.identify_row(event.y) if event is not None else (self.tree.selection()[0] if self.tree.selection() else "")
    payload=getattr(self, "_matrix_map", {}).get(iid) if iid else None
    if not payload:
        row=self.map.get(iid) if iid and hasattr(self, "map") else None
        if not row:return
        payload={"_rows":[row]}
    rows=legacy_detail_rows(payload)
    w=tk.Toplevel(self.root); w.title("记录详情 · 原始价格明细"); w.geometry("1500x620"); w.minsize(1000,480)
    ttk.Label(w,text="原始价格明细（按现实商品价值排序）",font=("微软雅黑",12,"bold")).pack(anchor="w",padx=12,pady=10)
    f=ttk.Frame(w,padding=(12,0,12,8));f.pack(fill="both",expand=True)
    cols=[c[0] for c in LEGACY_DETAIL_COLS]
    tree=ttk.Treeview(f,columns=cols,show="headings",selectmode="extended")
    for c,h,width in LEGACY_DETAIL_COLS:tree.heading(c,text=h);tree.column(c,width=width,anchor="w")
    y=ttk.Scrollbar(f,orient="vertical",command=tree.yview);x=ttk.Scrollbar(f,orient="horizontal",command=tree.xview)
    tree.configure(yscrollcommand=y.set,xscrollcommand=x.set);tree.grid(row=0,column=0,sticky="nsew");y.grid(row=0,column=1,sticky="ns");x.grid(row=1,column=0,sticky="ew");f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1)
    for r in rows:tree.insert("","end",values=[r.get(c,"") for c,_,_ in LEGACY_DETAIL_COLS])
    bar=ttk.Frame(w,padding=8);bar.pack(fill="x")
    ttk.Button(bar,text="关闭",command=w.destroy).pack(side="right",padx=4)
    ttk.Button(bar,text="查看完整19字段",command=lambda:self._show_full_raw_record(rows,w)).pack(side="right",padx=4)
    w.bind("<Escape>",lambda _e:w.destroy());w.transient(self.root);w.focus_set()


def _show_full_raw_record(self, rows, parent=None):
    rows=sort_rows(rows)
    w=tk.Toplevel(self.root);w.title("完整事实记录 · 19字段");w.geometry("900x640");w.minsize(700,480)
    text=tk.Text(w,wrap="none",font=("微软雅黑",10));text.pack(fill="both",expand=True,padx=12,pady=12)
    for idx,r in enumerate(rows,1):
        text.insert("end",f"===== 原始记录 {idx} =====\n")
        for field in phone_search.FIELDS:text.insert("end",f"{field}: {r.get(field,'')}\n")
        text.insert("end","\n")
    text.configure(state="disabled")
    ttk.Button(w,text="关闭",command=w.destroy).pack(pady=(0,8));w.bind("<Escape>",lambda _e:w.destroy());w.transient(parent or self.root);w.focus_set()


def install_fix(App):
    phone_search.Store.search = _semantic_search
    App.compare=compare
    App.show_favorites=show_favorites
    App.detail=detail
    App._show_full_raw_record=_show_full_raw_record
