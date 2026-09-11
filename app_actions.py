"""Complete optional UI actions used by phone_search.App."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox


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
    w = tk.Toplevel(self.root)
    w.title("来源图片结构")
    w.geometry("1100x620")
    w.minsize(800, 480)
    cols = ("date", "image", "path", "include", "note")
    tree = ttk.Treeview(w, columns=cols, show="headings")
    headings = {"date":"日期", "image":"来源图片", "path":"来源路径", "include":"纳入", "note":"备注"}
    widths = {"date":110, "image":220, "path":420, "include":80, "note":220}
    for c in cols:
        tree.heading(c, text=headings[c]); tree.column(c, width=widths[c], anchor="w")
    y = ttk.Scrollbar(w, orient="vertical", command=tree.yview)
    x = ttk.Scrollbar(w, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
    tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")
    w.grid_rowconfigure(0,weight=1); w.grid_columnconfigure(0,weight=1)
    for r in getattr(self.s, "manifest", []):
        tree.insert("", "end", values=(r.get("data_date",""), r.get("source_image",""), r.get("source_path",""), r.get("include",""), r.get("note", "")))
    ttk.Button(w, text="关闭", command=w.destroy).grid(row=2,column=0,pady=8)
    w.bind("<Escape>", lambda _e: w.destroy())
    w.transient(self.root); w.focus_set()


def show_favorites(self):
    rows = self.fav.dedupe()
    w = tk.Toplevel(self.root)
    w.title("⭐ 我的收藏")
    w.geometry("1500x760")
    w.minsize(1050,560)
    ttk.Label(w, text=f"收藏内容 · {len(rows)} 条 · 按型号分组，日期倒序", font=("微软雅黑",12,"bold")).pack(anchor="w", padx=12, pady=10)
    f=ttk.Frame(w,padding=(12,0,12,10)); f.pack(fill="both",expand=True)
    cols=[c[0] for c in __import__("phone_search").COLS]
    tree=ttk.Treeview(f,columns=cols,show="headings")
    for c,h,width in __import__("phone_search").COLS:
        tree.heading(c,text=h); tree.column(c,width=width,anchor="w")
    y=ttk.Scrollbar(f,orient="vertical",command=tree.yview); x=ttk.Scrollbar(f,orient="horizontal",command=tree.xview)
    tree.configure(yscrollcommand=y.set,xscrollcommand=x.set); tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")
    f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1)
    for gi, (model_key, blocks) in enumerate(self.favorite_groups()):
        for bi, block in enumerate(blocks):
            for r in block:
                tree.insert("", "end", values=[r.get(c,"") for c in cols])
            if bi < len(blocks)-1:
                tree.insert("", "end", values=[""]*len(cols))
        if gi < len(self.favorite_groups())-1:
            tree.insert("", "end", values=[""]*len(cols)); tree.insert("", "end", values=[""]*len(cols))
    ttk.Button(w,text="关闭",command=w.destroy).pack(pady=8)
    w.bind("<Escape>",lambda _e:w.destroy());w.transient(self.root);w.focus_set()


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
    if not rows:return messagebox.showinfo("批量报价","请先选择或查询价格记录",parent=self.root)
    prices=[__import__('phone_search').num(r.get('price','')) for r in rows]
    prices=[p for p in prices if p is not None]
    if not prices:return messagebox.showinfo("批量报价","选中记录没有可计算的数字价格",parent=self.root)
    messagebox.showinfo("批量报价",f"记录：{len(rows)} 条\n最低：{min(prices):g}\n最高：{max(prices):g}\n平均：{sum(prices)/len(prices):.2f}",parent=self.root)


def compare(self):
    rows=self.selected() or self.rows
    if not rows:return messagebox.showinfo("历史价格对比","请先选择或查询记录",parent=self.root)
    w=tk.Toplevel(self.root);w.title("历史价格对比");w.geometry("1650x760");w.minsize(1100,600)
    cols=("date","model","condition","price","unit")
    tree=ttk.Treeview(w,columns=cols,show="headings")
    for c,h,wd in (("date","日期",120),("model","型号",320),("condition","价格条件",300),("price","价格",100),("unit","单位",100)):
        tree.heading(c,text=h);tree.column(c,width=wd,anchor="w")
    for r in __import__('phone_search').Store(self.d).history(rows):
        tree.insert("", "end", values=(r.get("data_date",""),r.get("model",""),r.get("condition",""),r.get("price",""),r.get("unit","")))
    tree.pack(fill="both",expand=True,padx=12,pady=12)
    ttk.Button(w,text="关闭",command=w.destroy).pack(pady=(0,8));w.bind("<Escape>",lambda _e:w.destroy());w.transient(self.root);w.focus_set()


def detail(self,event=None):
    iid=self.tree.identify_row(event.y) if event is not None else (self.tree.selection()[0] if self.tree.selection() else "")
    row=self.map.get(iid) if iid else None
    if not row:return
    w=tk.Toplevel(self.root);w.title("记录详情");w.geometry("760x560");w.minsize(600,420)
    text=tk.Text(w,wrap="none",font=("微软雅黑",10));text.pack(fill="both",expand=True,padx=12,pady=12)
    for f in __import__('phone_search').FIELDS:text.insert("end",f"{f}: {row.get(f,'')}\n")
    text.configure(state="disabled");ttk.Button(w,text="关闭",command=w.destroy).pack(pady=(0,8));w.bind("<Escape>",lambda _e:w.destroy());w.transient(self.root);w.focus_set()


def menu(self,event):
    iid=self.tree.identify_row(event.y); row=self.map.get(iid) if iid else None
    if not row:return
    self.tree.selection_set(iid)
    m=tk.Menu(self.root,tearoff=False)
    m.add_command(label="添加收藏",command=lambda:self.addToFavorites([row]))
    m.add_command(label="复制选中",command=self.copy)
    m.add_command(label="查看详情",command=self.detail)
    m.tk_popup(event.x_root,event.y_root)


def install(App):
    actions={"open_dir":open_dir,"sources":sources,"show_favorites":show_favorites,"stats":stats,"quote":quote,"compare":compare,"detail":detail,"menu":menu}
    for name,fn in actions.items():
        if not hasattr(App,name): setattr(App,name,fn)
