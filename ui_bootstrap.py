"""Windows release bootstrap with independent per-result quote matrices."""
import os
import re
import tkinter as tk
from tkinter import ttk
import phone_search
from favorite_toggle import toggle_favorite
from app_actions import install as install_app_actions
from app_actions_fix import install_fix as install_app_action_fixes
from search_display import DISPLAY_COLUMNS, result_display_columns, normalize_search_results

phone_search.CAT["手机配件"] = "手机配件"
phone_search.COLS = DISPLAY_COLUMNS
_EMPTY_HINT = "输入品牌 / 系列 / 型号开始查询\n\n数据来自已验证的图片事实价格库"
_original_ui = phone_search.App.ui
_original_load = phone_search.App.load
_real_toplevel = phone_search.tk.Toplevel


def _canonical_store_load(self):
    self.rows=[]; self.snapshots={}; self.manifest=[]; self.errors=[]
    db=os.path.join(self.d,'database'); loaded_dates=set()
    def load_paths(date,paths):
        data=[]; seen=set()
        for p in paths:
            try: rows=phone_search.read_csv(p)
            except Exception as e: self.errors.append(f'{date}: {e}'); continue
            for raw in rows:
                r={k:phone_search.clean(raw.get(k,'')) for k in phone_search.FIELDS}
                r['category']=phone_search.CAT.get(r['category'],r['category'])
                if r['data_date']!=date:self.errors.append(f'{date}: data_date不一致')
                if r['category'] not in phone_search.CAT.values():self.errors.append(f'{date}: 非标准分类 {r["category"]}')
                if not phone_search.valid(r):continue
                rid=r['record_id']
                if rid in seen:self.errors.append(f'{date}: 重复 record_id {rid}');continue
                seen.add(rid);data.append(r)
        self.snapshots[date]=data; self.rows.extend(data)
    if os.path.isdir(db):
        for date in sorted(os.listdir(db)):
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):continue
            folder=os.path.join(db,date)
            if not os.path.isdir(folder):continue
            paths=[os.path.join(folder,n) for n in sorted(os.listdir(folder)) if n.lower().endswith('.csv') and os.path.isfile(os.path.join(folder,n))]
            if paths:load_paths(date,paths);loaded_dates.add(date)
    sd=os.path.join(self.d,'snapshots')
    if os.path.isdir(sd):
        for date in sorted(os.listdir(sd)):
            if date in loaded_dates or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):continue
            folder=os.path.join(sd,date)
            if not os.path.isdir(folder):continue
            paths=[os.path.join(folder,n) for n in sorted(os.listdir(folder)) if n.lower().endswith('.csv')]
            if paths:load_paths(date,paths)
    mp=os.path.join(self.d,'source_image_manifest.csv')
    if os.path.isfile(mp):
        try:self.manifest=phone_search.read_csv(mp)
        except Exception as e:self.errors.append(f'来源清单: {e}')


def _rebuild_matrix_surface(self):
    parent=self.tree.master
    self.tree.grid_remove()
    for widget in list(parent.winfo_children()):
        if isinstance(widget,ttk.Scrollbar):widget.destroy()
    canvas=tk.Canvas(parent,highlightthickness=0,bg='white')
    canvas.grid(row=0,column=0,sticky='nsew')
    ybar=ttk.Scrollbar(parent,orient='vertical',command=canvas.yview)
    xbar=ttk.Scrollbar(parent,orient='horizontal',command=canvas.xview)
    ybar.grid(row=0,column=1,sticky='ns');xbar.grid(row=1,column=0,sticky='ew')
    canvas.configure(yscrollcommand=ybar.set,xscrollcommand=xbar.set)
    inner=tk.Frame(canvas,bg='white')
    window_id=canvas.create_window((0,0),window=inner,anchor='nw')
    inner.bind('<Configure>',lambda _e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window_id,width=max(e.width,1)))
    canvas.bind('<MouseWheel>',lambda e:canvas.yview_scroll(int(-1*(e.delta/120 or -1)),'units'))
    canvas.bind('<Button-4>',lambda _e:canvas.yview_scroll(-3,'units'))
    canvas.bind('<Button-5>',lambda _e:canvas.yview_scroll(3,'units'))
    self._matrix_canvas=canvas;self._matrix_inner=inner;self._matrix_window_id=window_id
    self._matrix_widgets={};self._selected_matrix_iid=None


def clear_search(self):
    self.q.set('');self.hide_suggestions();self.rows=[];self.map={};self._matrix_map={};self._matrix_columns=DISPLAY_COLUMNS
    if hasattr(self,'_matrix_inner'):
        for child in self._matrix_inner.winfo_children():child.destroy()
        self._matrix_canvas.configure(scrollregion=(0,0,0,0))
    self.target.config(text='输入品牌 / 系列 / 型号开始查询')
    if hasattr(self,'empty_hint'):self.empty_hint.place(relx=0.5,rely=0.5,anchor='center')
    self.status.config(text='请输入品牌、系列、型号或别名');self.entry.focus_set()


def ui(self):
    _original_ui(self)
    for widget in self.root.winfo_children():
        if isinstance(widget,ttk.Frame):
            for child in widget.winfo_children():
                if isinstance(child,ttk.Combobox):
                    values=list(child.cget('values'))
                    if '手机配件' not in values:child.configure(values=values+['手机配件'])
                    break
    _rebuild_matrix_surface(self)
    self.empty_hint=tk.Label(self._matrix_canvas,text=_EMPTY_HINT,font=('微软雅黑',15),justify='center',fg='#666666',bg='#ffffff',padx=28,pady=22)
    self.empty_hint.place(relx=0.5,rely=0.5,anchor='center')
    self._matrix_map={};self._matrix_columns=DISPLAY_COLUMNS


def _result_column_anchor(field):
    if field=='identity':return 'w'
    return 'center'


def _select_result(self,iid,payload,event=None):
    self._selected_matrix_iid=iid
    self.tree.selection_set(iid)
    self.tree.focus(iid)
    for key,widgets in getattr(self,'_matrix_widgets',{}).items():
        selected=(key==iid)
        for widget in widgets:
            try:widget.configure(bg='#eef4ff' if selected else 'white')
            except tk.TclError:pass
    if payload:
        self.status.config(text=f'已选择：{payload.get("identity","")} · {payload.get("data_date","")}')


def _matrix_menu(self,iid,payload,event):
    _select_result(self,iid,payload,event)
    menu=tk.Menu(self.root,tearoff=False)
    menu.add_command(label='添加收藏',command=lambda:self.addToFavorites(payload.get('_rows',[])))
    menu.add_command(label='复制选中',command=self.copy)
    menu.add_command(label='查看详情',command=self.detail)
    menu.tk_popup(event.x_root,event.y_root)


def _render_search_matrix(self,result):
    display_rows=normalize_search_results(result)
    self.rows=result;self.map={};self._matrix_map={};self._matrix_columns=DISPLAY_COLUMNS
    for child in self._matrix_inner.winfo_children():child.destroy()
    self._matrix_widgets={}
    self.tree.delete(*self.tree.get_children())
    row_index=0
    for block_index,display in enumerate(display_rows):
        iid=str(row_index);row_index+=1
        raw_rows=display.get('_rows',[])
        self.tree.insert('','end',iid=iid,values=[display.get('data_date',''),display.get('identity','')])
        self.map[iid]=raw_rows[0] if raw_rows else None
        self._matrix_map[iid]=display
        columns=display.get('_columns') or result_display_columns(raw_rows)
        block=tk.Frame(self._matrix_inner,bg='white',bd=0,highlightthickness=0)
        block.grid(row=block_index,column=0,sticky='ew',padx=8,pady=(10,8))
        inner_width=sum(width for _field,_label,width in columns)
        block.grid_columnconfigure(len(columns)-1,minsize=1)
        header=[];values=[]
        for col,(field,label,width) in enumerate(columns):
            block.grid_columnconfigure(col,minsize=width,weight=0)
            h=tk.Label(block,text=label,font=('微软雅黑',10,'bold'),bg='white',anchor='center',justify='center',wraplength=max(width-12,80),padx=4,pady=3)
            h.grid(row=0,column=col,sticky='ew')
            v=tk.Label(block,text=display.get(field,''),font=('微软雅黑',10),bg='white',anchor=_result_column_anchor(field),justify='center' if field!='identity' else 'left',wraplength=max(width-12,80),padx=4,pady=6)
            v.grid(row=1,column=col,sticky='ew')
            header.append(h);values.append(v)
        widgets=header+values+[block]
        self._matrix_widgets[iid]=widgets
        for widget in widgets:
            widget.bind('<Button-1>',lambda e,_iid=iid,_payload=display:_select_result(self,_iid,_payload,e),add='+')
            widget.bind('<Double-Button-1>',lambda e,_iid=iid,_payload=display:( _select_result(self,_iid,_payload,e), self.detail(e) ),add='+')
            widget.bind('<Button-3>',lambda e,_iid=iid,_payload=display:_matrix_menu(self,_iid,_payload,e),add='+')
        if block_index<len(display_rows)-1:
            spacer=tk.Frame(self._matrix_inner,height=4,bg='white');spacer.grid(row=block_index,column=0,sticky='ew')
    if self._matrix_map:
        self.empty_hint.place_forget()
    else:
        self.empty_hint.place(relx=0.5,rely=0.5,anchor='center')
    return display_rows


def search(self,record_history=True):
    q=phone_search.clean(self.q.get())
    if not q:
        self.hide_suggestions();self.rows=[];self.map={};self._matrix_map={};self._matrix_columns=DISPLAY_COLUMNS
        for child in self._matrix_inner.winfo_children():child.destroy()
        self.target.config(text='输入品牌 / 系列 / 型号开始查询')
        self.empty_hint.place(relx=0.5,rely=0.5,anchor='center')
        self.status.config(text='请输入品牌、系列、型号或别名');return []
    if record_history:self.h.add(q)
    result=self.s.search(q,self.cat.get());display_rows=_render_search_matrix(self,result)
    count=len(display_rows)
    self.target.config(text=f'搜索结果：{q} · {count} 个独立结果')
    self.status.config(text=f'找到 {count} 个独立结果')
    self.refresh_suggestions();return result


def load(self):
    self.s.load();self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}')
    q=phone_search.clean(self.q.get())
    if q:self.search(False)
    else:
        self.rows=[];self.map={};self._matrix_map={};self._matrix_columns=DISPLAY_COLUMNS
        for child in self._matrix_inner.winfo_children():child.destroy()
        self.target.config(text='输入品牌 / 系列 / 型号开始查询');self.empty_hint.place(relx=0.5,rely=0.5,anchor='center');self.status.config(text='数据已就绪，请输入查询条件')
    self.root.after_idle(self.entry.focus_set);self.root.after_idle(self.show_suggestions)


def _toggle_matrix_favorite(self,iid,payload):
    rows=payload.get('_rows',[])
    if not rows:return
    selected_all=all(self.fav.has(r) for r in rows)
    if selected_all:
        for row in rows:self.fav.remove([row])
    else:self.fav.add(rows)
    _render_search_matrix(self,self.rows)


def favorite_groups(self):
    groups={}
    for r in self.fav.dedupe():groups.setdefault(phone_search.key(r.get('model','')),[]).append(r)
    ordered=[]
    for model_key,rows in groups.items():
        dates=sorted({r.get('data_date','') for r in rows},reverse=True);blocks=[[r for r in rows if r.get('data_date','')==d] for d in dates];ordered.append((model_key,dates[0] if dates else '',blocks))
    ordered.sort(key=lambda x:(x[1],x[0]),reverse=True);return [(k,b) for k,_,b in ordered]


def _standardize_window(w):
    try:
        if not w.winfo_exists() or bool(w.overrideredirect()):return
        title=phone_search.clean(w.title());specs=(("搜索历史",560,620,420,420),("我的收藏",1500,760,1050,560),("记录详情",760,560,600,420),("历史价格对比",1650,760,1100,600),("来源图片结构",1100,620,800,480));width,height,min_w,min_h=900,600,640,420
        for marker,sw,sh,smw,smh in specs:
            if marker in title:width,height,min_w,min_h=sw,sh,smw,smh;break
        parent=w.master if getattr(w,'master',None) is not None else w.winfo_toplevel();parent.update_idletasks();pw,ph=parent.winfo_width(),parent.winfo_height();px,py=parent.winfo_rootx(),parent.winfo_rooty();w.minsize(min_w,min_h);w.geometry(f'{width}x{height}+{max(0,px+(pw-width)//2)}+{max(0,py+(ph-height)//2)}');w.transient(parent.winfo_toplevel());w.bind('<Escape>',lambda _e:w.destroy(),add='+');w.protocol('WM_DELETE_WINDOW',w.destroy);w.focus_set()
    except tk.TclError:pass


def standardized_toplevel(*args,**kwargs):
    w=_real_toplevel(*args,**kwargs);w.after_idle(lambda:_standardize_window(w));return w

install_app_actions(phone_search.App);install_app_action_fixes(phone_search.App)
phone_search.COLS=DISPLAY_COLUMNS
phone_search.Store.load=_canonical_store_load
phone_search.App.ui=ui;phone_search.App.search=search;phone_search.App.render=_render_search_matrix;phone_search.App.load=load;phone_search.App.clear_search=clear_search;phone_search.App.favorite_groups=favorite_groups;phone_search.tk.Toplevel=standardized_toplevel

def main():
    root=tk.Tk();phone_search.App(root);root.mainloop()
if __name__=='__main__':main()
