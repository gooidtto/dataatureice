"""Second-stage UI action fixes that depend on the canonical Store instance."""
import tkinter as tk
from tkinter import ttk, messagebox
import phone_search
from search_core import search_rows

# model_code is an authoritative 19-field fact and is also the user's
# network-model identifier. Expose it in every data-facing UI built from COLS.
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
    history = self.s.history(rows)
    w = tk.Toplevel(self.root); w.title("历史价格对比"); w.geometry("1650x760"); w.minsize(1100,600)
    cols=("date","model","condition","price","unit")
    tree=ttk.Treeview(w,columns=cols,show="headings")
    for c,h,wd in (("date","日期",120),("model","型号",320),("condition","价格条件",300),("price","价格",100),("unit","单位",100)):
        tree.heading(c,text=h);tree.column(c,width=wd,anchor="w")
    for r in history: tree.insert("","end",values=(r.get("data_date",""),r.get("model",""),r.get("condition",""),r.get("price",""),r.get("unit","")))
    tree.pack(fill="both",expand=True,padx=12,pady=12);ttk.Button(w,text="关闭",command=w.destroy).pack(pady=(0,8));w.bind("<Escape>",lambda _e:w.destroy());w.transient(self.root);w.focus_set()


def show_favorites(self):
    rows=self.fav.dedupe();w=tk.Toplevel(self.root);w.title("⭐ 我的收藏");w.geometry("1500x760");w.minsize(1050,560)
    ttk.Label(w,text=f"收藏内容 · {len(rows)} 条 · 按型号分组，日期倒序",font=("微软雅黑",12,"bold")).pack(anchor="w",padx=12,pady=10)
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


def install_fix(App):
    phone_search.Store.search = _semantic_search
    App.compare=compare
    App.show_favorites=show_favorites
