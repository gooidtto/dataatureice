"""UI startup/child-window standard for the Windows release build."""
import tkinter as tk
from tkinter import ttk
import phone_search
from favorite_toggle import toggle_favorite

phone_search.CAT["手机配件"] = "手机配件"
_EMPTY_HINT = "输入品牌 / 系列 / 型号开始查询\n\n数据来自已验证的图片事实价格库"
_original_ui = phone_search.App.ui
_original_load = phone_search.App.load
_original_tree_click = phone_search.App.on_tree_click
_real_toplevel = phone_search.tk.Toplevel

def ui(self):
    _original_ui(self)
    for widget in self.root.winfo_children():
        if isinstance(widget, ttk.Frame):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Combobox):
                    values=list(child.cget("values"))
                    if "手机配件" not in values: child.configure(values=values+["手机配件"])
                    break
    self.empty_hint=tk.Label(self.tree.master,text=_EMPTY_HINT,font=("微软雅黑",15),justify="center",fg="#666666",bg="#ffffff",padx=28,pady=22)
    self.empty_hint.place(relx=0.5,rely=0.5,anchor="center")

def search(self, record_history=True):
    q=phone_search.clean(self.q.get())
    if not q:
        self.hide_suggestions(); self.rows=[]; self.map={}; self.tree.delete(*self.tree.get_children())
        self.target.config(text="输入品牌 / 系列 / 型号开始查询")
        if hasattr(self,"empty_hint"): self.empty_hint.place(relx=0.5,rely=0.5,anchor="center")
        self.status.config(text="请输入品牌、系列、型号或别名")
        return []
    if record_history: self.h.add(q)
    result=self.s.search(q,self.cat.get())
    self.rows=result; self.map={}
    self.tree.delete(*self.tree.get_children())
    for i,r in enumerate(result):
        iid=str(i); self.map[iid]=r
        values=[r.get(c,'') for c,_,_ in phone_search.COLS]+["★ 已收藏" if self.fav.has(r) else "☆ 一键收藏"]
        self.tree.insert('', 'end', iid=iid, values=values)
    self.target.config(text=f"搜索结果：{q} · {len(result)} 条")
    self.status.config(text=f"找到 {len(result)} 条")
    if hasattr(self,"empty_hint"):
        if result: self.empty_hint.place_forget()
        else: self.empty_hint.place(relx=0.5,rely=0.5,anchor="center")
    self.refresh_suggestions()
    return result

def load(self):
    _original_load(self)
    self.meta.config(text=f"最新：{self.s.latest or '无'} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}")
    if phone_search.clean(self.q.get()):
        if hasattr(self,"empty_hint"): self.empty_hint.place_forget()
    else:
        self.rows=[]; self.map={}; self.tree.delete(*self.tree.get_children()); self.target.config(text="输入品牌 / 系列 / 型号开始查询")
        if hasattr(self,"empty_hint"): self.empty_hint.place(relx=0.5,rely=0.5,anchor="center")
        self.status.config(text="数据已就绪，请输入查询条件")
    self.root.after_idle(self.entry.focus_set); self.root.after_idle(self.show_suggestions)

def on_tree_click(self,event):
    region=self.tree.identify("region",event.x,event.y); column=self.tree.identify_column(event.x); iid=self.tree.identify_row(event.y)
    favorite_column=f"#{len(phone_search.COLS)+1}"; row=self.map.get(iid) if iid else None
    if region=="cell" and column==favorite_column and row:
        self.tree.selection_set(iid); toggle_favorite(self,row); return "break"
    return _original_tree_click(self,event)

def favorite_groups(self):
    groups={}
    for r in self.fav.dedupe(): groups.setdefault(phone_search.key(r.get("model","")),[]).append(r)
    ordered=[]
    for model_key,rows in groups.items():
        dates=sorted({r.get("data_date","") for r in rows},reverse=True)
        blocks=[[r for r in rows if r.get("data_date","")==d] for d in dates]
        ordered.append((model_key,dates[0] if dates else "",blocks))
    ordered.sort(key=lambda x:(x[1],x[0]),reverse=True)
    return [(k,b) for k,_,b in ordered]

def _standardize_window(w):
    try:
        if not w.winfo_exists() or bool(w.overrideredirect()): return
        title=phone_search.clean(w.title())
        specs=(("搜索历史",560,620,420,420),("我的收藏",1500,760,1050,560),("记录详情",760,560,600,420),("历史价格对比",1650,760,1100,600),("来源图片结构",1100,620,800,480))
        width,height,min_w,min_h=900,600,640,420
        for marker,sw,sh,smw,smh in specs:
            if marker in title: width,height,min_w,min_h=sw,sh,smw,smh; break
        parent=w.master if getattr(w,"master",None) is not None else w.winfo_toplevel(); parent.update_idletasks()
        pw,ph=parent.winfo_width(),parent.winfo_height(); px,py=parent.winfo_rootx(),parent.winfo_rooty()
        w.minsize(min_w,min_h); w.geometry(f"{width}x{height}+{max(0,px+(pw-width)//2)}+{max(0,py+(ph-height)//2)}")
        w.transient(parent.winfo_toplevel()); w.bind("<Escape>",lambda _e:w.destroy(),add="+"); w.protocol("WM_DELETE_WINDOW",w.destroy); w.focus_set()
    except tk.TclError: pass

def standardized_toplevel(*args,**kwargs):
    w=_real_toplevel(*args,**kwargs); w.after_idle(lambda:_standardize_window(w)); return w

phone_search.App.ui=ui
phone_search.App.search=search
phone_search.App.load=load
phone_search.App.on_tree_click=on_tree_click
phone_search.App.favorite_groups=favorite_groups
phone_search.tk.Toplevel=standardized_toplevel

def main():
    root=tk.Tk(); phone_search.App(root); root.mainloop()

if __name__=="__main__": main()
