"""Tk lifecycle/bootstrap bridge for the stable SearchApp UI."""
from __future__ import annotations

import tkinter as tk
from queue import Empty

import phone_search
from app_actions import install as install_app_actions
from search_display import normalize_search_results, sort_rows


class SearchApp(phone_search.App):
    def _new_window(self,title,geometry=None,minsize=None):
        w=tk.Toplevel(self.root); w.title(title)
        if geometry: w.geometry(geometry)
        if minsize: w.minsize(*minsize)
        try: w.transient(self.root); w.lift(); w.focus_force()
        except tk.TclError: pass
        return w


def _clear_result_views(self):
    for frame in getattr(self,"_result_views",[]):
        try: frame.destroy()
        except tk.TclError: pass
    self._result_views=[]; self._result_trees=[]; self._result_tree_map={}; self._result_order=[]


def _row_tag(model_index,period_index): return (f"m{model_index}d{period_index}",)
_MODEL_PALETTE=("#eef7ff","#f5efff","#eefaf2","#fff7e8","#f3f3f3")


def _configure_result_tree(tree,columns,iid,display,favorite):
    fields=[c[0] for c in columns]+["favorite"]; tree.configure(columns=fields,show="headings",height=1,selectmode="browse")
    for field,title,width in columns: tree.heading(field,text=title); tree.column(field,width=width,minwidth=max(60,min(width,90)),anchor="center" if field=="data_date" else "w",stretch=False)
    tree.heading("favorite",text="收藏"); tree.column("favorite",width=110,minwidth=90,anchor="center",stretch=False)
    values=[display.get(field,"") for field,_,_ in columns]; tag=_row_tag(display["_model_index"],display["_period_index"])[0]
    tree.insert("","end",iid=iid,values=values+["★ 已收藏" if favorite else "☆ 一键收藏"],tags=(tag,)); tree.tag_configure(tag,background=_MODEL_PALETTE[display["_model_index"]%len(_MODEL_PALETTE)])


def _sync_result_selection(self):
    selected=set(self.tree.selection())
    for iid,tree in getattr(self,"_result_tree_map",{}).items():
        try: tree.selection_set(iid) if iid in selected else tree.selection_remove(iid)
        except tk.TclError: pass


def _select_result_iid(self,iid):
    try: self.tree.selection_set(iid); self.tree.focus(iid)
    except tk.TclError: pass
    _sync_result_selection(self)


def _result_click(self,event,iid):
    tree=self._result_tree_map.get(iid)
    if tree is None: return
    _select_result_iid(self,iid)
    if tree.identify_column(event.x)==f"#{len(self._matrix_map[iid].get('_columns',()))+1}": _toggle_matrix_favorite(self,iid,self._matrix_map[iid])


def _result_context_menu(self,event,iid):
    tree=self._result_tree_map.get(iid); payload=self._matrix_map.get(iid) if iid else None
    if tree is None or payload is None: return
    _select_result_iid(self,iid); menu=tk.Menu(tree,tearoff=False); menu.add_command(label="收藏当前结果",command=lambda:self.addToFavorites(payload.get("_rows",[]))); menu.add_command(label="查看详情",command=lambda:self.detail_rows(payload.get("_rows",[]))); menu.tk_popup(event.x_root,event.y_root)


def _toggle_matrix_favorite(self,iid,payload):
    rows=list(payload.get("_rows") or [])
    if not rows: return
    keys={self.fav.identity(r) for r in rows}; existing={self.fav.identity(r) for r in self.fav.dedupe()}
    if keys and keys.issubset(existing): self.fav.remove(rows); self.status.config(text="已取消收藏")
    else: self.addToFavorites(rows)
    _render_search_matrix(self,self.rows)


def _render_search_matrix(self,result):
    _clear_result_views(self); self.map={}; self._matrix_map={}; self._display_columns=(); display_rows=normalize_search_results(sort_rows(result)); parent=getattr(self,"_results_inner",None)
    if parent is None: self.rows=list(result or []); return
    for item in display_rows:
        if item.get("_separator"):
            self._result_order.append(None if item.get("_separator")=="model" else ""); continue
        columns=tuple(item.get("_columns") or ()); self._display_columns=columns or self._display_columns; iid=f"result-{len(self._matrix_map)}"; rows=list(item.get("_rows") or []); favorite_keys={self.fav.identity(r) for r in self.fav.dedupe()}; favorite=any(self.fav.identity(r) in favorite_keys for r in rows)
        tree_frame=tk.Frame(parent,bd=0,highlightthickness=0); tree=phone_search.ttk.Treeview(tree_frame,columns=(),show="headings",height=1,selectmode="browse"); _configure_result_tree(tree,columns,iid,item,favorite)
        tree.bind("<Button-1>",lambda event,iid=iid:_result_click(self,event,iid)); tree.bind("<Button-3>",lambda event,iid=iid:_result_context_menu(self,event,iid)); tree.bind("<Double-1>",lambda _e,iid=iid:( _select_result_iid(self,iid), self.detail(), "break")[-1]); tree.bind("<<TreeviewSelect>>",lambda _event:_sync_result_selection(self)); tree.pack(fill="x",expand=True); tree_frame.pack(fill="x",expand=True,pady=(0,2)); self._result_views.append(tree_frame); self._result_trees.append(tree); self._result_tree_map[iid]=tree; self._result_order.append(iid); self._matrix_map[iid]=item
        for row in rows:
            rid=phone_search.rid(row)
            if rid:self.map[rid]=row
    try:self._results_canvas.configure(scrollregion=self._results_canvas.bbox("all"))
    except (AttributeError,tk.TclError): pass
    if getattr(self,"_matrix_map",{}):
        try:self.empty_hint.place_forget()
        except tk.TclError: pass
    else:
        try:self.empty_hint.place(relx=.5,rely=.5,anchor="center")
        except tk.TclError: pass


def favorite_groups(self):
    rows=sort_rows(self.fav.dedupe()); grouped={}
    for row in rows:
        key=tuple(phone_search.clean(row.get(field,"")) for field in ("category","brand","series","model","model_code")); grouped.setdefault(key,{}).setdefault(phone_search.clean(row.get("data_date","")),[]).append(row)
    result=[]; model_index=0
    for key,dates in grouped.items():
        period_index=0
        for _date,group in sorted(dates.items(),reverse=True):
            r=sort_rows(group)[0].copy(); r["identity"]=" ".join(x for x in key if x); r["_rows"]=sort_rows(group); r["_model_index"]=model_index; r["_period_index"]=period_index; result.append(r); period_index+=1
        model_index+=1
        if model_index<len(grouped): result.append({"_separator":"model"})
    return result


def _new_window(self,title,geometry=None,minsize=None): return self.__class__._new_window(self,title,geometry,minsize)

_UI_QUEUE=__import__("queue").Queue()

def _poll_async_results(self):
    try:
        while True:
            query_id,q,record_history,future=_UI_QUEUE.get_nowait(); _apply_async_result(self,query_id,q,record_history,future)
    except Empty: pass
    try:self.root.after(25,lambda:_poll_async_results(self))
    except tk.TclError: pass

def _apply_async_result(self,query_id,q,record_history,future):
    if query_id!=getattr(self,"_search_query_id",0): return
    try: result=future.result()
    except Exception as exc: self.status.config(text=f"搜索失败：{type(exc).__name__}: {exc}"); return
    self.rows=list(result or []); self.h.add(q) if record_history else None; self.render(self.rows); count=len(getattr(self,"_matrix_map",{}) or {}); self.target.config(text=f"搜索结果：{q} · {count} 个结果块"); self.status.config(text=f"找到 {count} 个结果块")

def _queue_async_result(query_id,q,record_history,future): _UI_QUEUE.put((query_id,q,record_history,future))

def _debounced_search(self):
    try:self.root.after_cancel(self._search_after_id)
    except Exception: pass
    self._search_after_id=self.root.after(180,lambda:self.search(False))

def clear_search(self):
    try:self.root.after_cancel(self._search_after_id)
    except Exception: pass
    try:self.root.after_cancel(self._sync_search_after_id)
    except Exception: pass
    self._search_query_id=getattr(self,"_search_query_id",0)+1; self.q.set(""); self.hide_suggestions(); self.rows=[]; self.map={}; self._matrix_map={}; self._display_columns=(); self.tree.delete(*self.tree.get_children()); _clear_result_views(self); self.target.config(text="输入品牌、系列、型号开始查询"); self.empty_hint.place(relx=.5,rely=.5,anchor="center"); self.status.config(text="请输入品牌、系列、型号或别名"); self.entry.focus_set()


def install_app_actions(SearchApp):
    SearchApp.render=_render_search_matrix; SearchApp.favorite_groups=favorite_groups; SearchApp._new_window=_new_window; SearchApp.clear_search=clear_search; SearchApp._poll_async_results=_poll_async_results; SearchApp._apply_async_result=_apply_async_result; SearchApp._queue_async_result=_queue_async_result; SearchApp._debounced_search=_debounced_search
    install_app_actions(SearchApp)

install_app_actions(SearchApp)
