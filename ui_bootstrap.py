"""Stable Tk bootstrap for the search/result surface."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from queue import Empty
import phone_search
import app_actions
from app_actions import install as install_app_actions
from matrix_ui_actions import install as install_matrix_actions
from search_display import build_result_blocks, group_model_dates
from ui_theme import THEME, FONT_BODY, FONT_LABEL, FONT_TITLE, FONT_SEARCH

_UI_QUEUE=__import__('queue').Queue()

def _screen_fit_geometry(root,geometry=None,minsize=None):
    root.update_idletasks();sw,sh=root.winfo_screenwidth(),root.winfo_screenheight();raw_w,raw_h=1200,720
    if geometry:
        try: raw_w,raw_h=(int(x) for x in str(geometry).split('+',1)[0].lower().split('x',1))
        except (ValueError,TypeError): pass
    w=min(raw_w,max(760,sw-36));h=min(raw_h,max(520,sh-72))
    if minsize:
        mw,mh=minsize;w=min(max(w,min(mw,sw-36)),sw-36);h=min(max(h,min(mh,sh-72)),sh-72)
    return w,h,max(12,(sw-w)//2),max(12,(sh-h)//2)

def _new_window(self,title,geometry=None,minsize=None):
    if '我的收藏' in str(title):title=str(title).replace('我的收藏','展示收藏')
    w=tk.Toplevel(self.root);w.title(title);width,height,x,y=_screen_fit_geometry(w,geometry,minsize);w.geometry(f'{width}x{height}+{x}+{y}');w.minsize(min(width,x+width),min(height,y+height));w.configure(background=THEME['window_bg'])
    try:w.transient(self.root);w.lift();w.focus_force()
    except tk.TclError:pass
    return w

class SearchApp(phone_search.App):
    _new_window=_new_window
    def ui(self):
        root=self.root;root.configure(background=THEME['window_bg']);style=ttk.Style(root)
        try:
            style.theme_use('clam');style.configure('TFrame',background=THEME['window_bg']);style.configure('Search.TFrame',background=THEME['surface_alt'],borderwidth=1,relief='solid');style.configure('Info.TFrame',background=THEME['surface']);style.configure('Action.TFrame',background=THEME['surface_alt']);style.configure('Results.TFrame',background=THEME['border_soft'],borderwidth=1,relief='solid');style.configure('TLabel',background=THEME['window_bg'],foreground=THEME['text'],font=FONT_BODY);style.configure('Search.TLabel',background=THEME['surface_alt'],foreground=THEME['text'],font=FONT_LABEL);style.configure('Title.TLabel',background=THEME['surface'],foreground=THEME['text'],font=FONT_TITLE);style.configure('Meta.TLabel',background=THEME['surface'],foreground=THEME['text_secondary'],font=FONT_BODY);style.configure('Status.TLabel',background=THEME['surface_alt'],foreground=THEME['text_muted'],font=FONT_BODY)
            base=dict(background=THEME['button_bg'],font=FONT_BODY,padding=(THEME['button_pad_x'],THEME['button_pad_y']),relief='solid',borderwidth=1);style.configure('TButton',**base,foreground=THEME['button_text']);style.map('TButton',background=[('active',THEME['button_hover']),('pressed',THEME['button_pressed']),('disabled',THEME['button_disabled'])])
            for name in ('Primary.TButton','Favorite.TButton','Compare.TButton'):
                style.configure(name,**base,foreground=THEME['button_accent_text']);style.map(name,background=[('active',THEME['button_hover']),('pressed',THEME['button_pressed']),('disabled',THEME['button_disabled'])])
            style.configure('Search.Treeview',font=FONT_BODY,rowheight=THEME['table_row_height'],background=THEME['table_bg'],fieldbackground=THEME['table_bg'],foreground=THEME['text'],borderwidth=0,relief='flat');style.configure('Search.Treeview.Heading',font=FONT_TITLE,background=THEME['table_header'],foreground=THEME['text'],padding=(THEME['space_sm'],3),relief='flat',borderwidth=0);style.configure('TCombobox',fieldbackground=THEME['surface'],background=THEME['surface'],foreground=THEME['text'],arrowcolor=THEME['accent'])
        except tk.TclError:pass
        top=ttk.Frame(root,style='Search.TFrame',padding=(THEME['space_lg'],THEME['space_md']));top.pack(fill='x',padx=THEME['space_lg'],pady=(THEME['space_lg'],THEME['space_sm']));self.search_bar=top
        ttk.Label(top,text='⌕ 品牌 / 系列 / 型号 / 别名',style='Search.TLabel').pack(side='left');self.q=tk.StringVar();self.entry=tk.Entry(top,textvariable=self.q,font=FONT_SEARCH,width=30,bg=THEME['surface'],fg=THEME['text'],insertbackground=THEME['accent'],relief='flat',highlightthickness=1,highlightbackground=THEME['border'],highlightcolor=THEME['accent']);self.entry.pack(side='left',padx=(THEME['space_md'],THEME['space_xs']),ipady=5,fill='x',expand=True);self.entry.bind('<Return>',lambda _e:self.search());self.entry.bind('<FocusIn>',lambda _e:self.root.after_idle(self._refresh_suggestions));self.entry.bind('<Escape>',lambda _e:self._hide_suggestions())
        self.cat=ttk.Combobox(top,textvariable=tk.StringVar(value='全部'),values=['全部','手机','平板','电脑','其它','手机配件'],state='readonly',width=8);self.cat.set('全部');self.cat.pack(side='left',padx=THEME['space_xs'])
        for text,command,style_name in (('×',self.clear_search,'TButton'),('查询',self.search,'Primary.TButton'),('刷新',self.load,'TButton'),('数据目录',self.open_dir,'TButton'),('来源结构',self.sources,'TButton')):ttk.Button(top,text=text,command=command,style=style_name).pack(side='left',padx=THEME['space_xs'])
        self.status=ttk.Label(top,text='',style='Status.TLabel');self.status.pack(side='right',padx=(THEME['space_md'],0))
        info=ttk.Frame(root,style='Info.TFrame',padding=(THEME['space_lg'],THEME['space_sm'],THEME['space_lg'],THEME['space_md']));info.pack(fill='x');self.target=ttk.Label(info,text='输入品牌、系列、型号开始查询',style='Title.TLabel');self.target.pack(side='left');self.meta=ttk.Label(info,text='',style='Meta.TLabel');self.meta.pack(side='right')
        actions=ttk.Frame(root,style='Action.TFrame',padding=(THEME['space_lg'],0,THEME['space_lg'],THEME['space_md']));actions.pack(fill='x');ttk.Button(actions,text='☆ 一键收藏',command=self.add_favorite,style='Favorite.TButton').pack(side='left',padx=THEME['space_xs']);ttk.Button(actions,text='展示收藏',command=self.show_favorites,style='Favorite.TButton').pack(side='left',padx=THEME['space_xs']);ttk.Button(actions,text='条件比价',command=self.condition_compare,style='Primary.TButton').pack(side='left',padx=THEME['space_xs']);ttk.Button(actions,text='历史对比',command=self.history_compare,style='Compare.TButton').pack(side='left',padx=THEME['space_xs']);ttk.Label(actions,text='搜索区只展示；收藏区负责选择与操作',style='Status.TLabel').pack(side='right')
        host=ttk.Frame(root,style='Results.TFrame',padding=1);host.pack(fill='both',expand=True,padx=THEME['space_lg'],pady=(0,THEME['space_lg']));self._results_canvas=tk.Canvas(host,highlightthickness=0,bd=0,background=THEME['surface'],relief='flat');scroll=ttk.Scrollbar(host,orient='vertical',command=self._results_canvas.yview);self._results_canvas.configure(yscrollcommand=scroll.set);self._results_canvas.grid(row=0,column=0,sticky='nsew');scroll.grid(row=0,column=1,sticky='ns');host.grid_rowconfigure(0,weight=1);host.grid_columnconfigure(0,weight=1);self._results_inner=tk.Frame(self._results_canvas,background=THEME['surface']);self._results_window=self._results_canvas.create_window((0,0),window=self._results_inner,anchor='nw');self._results_inner.bind('<Configure>',lambda _e:self._results_canvas.configure(scrollregion=self._results_canvas.bbox('all')));self._results_canvas.bind('<Configure>',self._resize_results_inner);self.empty_hint=ttk.Label(host,text='输入品牌、系列、型号开始查询',font=FONT_TITLE,foreground=THEME['text_muted'],background=THEME['surface']);self._result_views=[];self._result_trees=[];self._result_tree_map={};self._result_order=[];self._matrix_map={};self._display_columns=();self.tree=ttk.Treeview(host,columns=[x[0] for x in phone_search.COLS]+['favorite'],show='headings',selectmode='none');self.tree.grid_remove()
    def _resize_results_inner(self,event):
        try:self._results_canvas.itemconfigure(self._results_window,width=event.width)
        except tk.TclError:pass
    def _new_window(self,title,geometry=None,minsize=None):return _new_window(self,title,geometry,minsize)
    def _result_double_click(self,iid):
        rows=list((self._matrix_map.get(iid) or {}).get('_rows') or [])
        if rows:self.detail_rows(rows)
        return 'break'
    def _refresh_suggestions(self):
        if not hasattr(self,'entry') or not hasattr(self,'h'):return
        items=self.h.suggestions(phone_search.clean(self.q.get()),10);panel=getattr(self,'_history_panel',None)
        if not items:self._hide_suggestions();return
        try:
            if panel is None or not panel.winfo_exists():panel=tk.Frame(self.search_bar,bg=THEME['surface'],bd=1,relief='solid',highlightthickness=1,highlightbackground=THEME['border']);self._history_panel=panel
            for child in panel.winfo_children():child.destroy()
            header=tk.Frame(panel,bg=THEME['surface_alt']);header.pack(fill='x');tk.Label(header,text='搜索历史',anchor='w',bg=THEME['surface_alt'],fg=THEME['text_secondary'],font=FONT_LABEL,padx=THEME['space_md'],pady=THEME['space_sm']).pack(side='left',fill='x',expand=True);ttk.Button(header,text='清除',style='TButton',command=self.clear_search_history).pack(side='right',padx=THEME['space_xs'],pady=THEME['space_xs'])
            for item in items:
                label=tk.Label(panel,text=item,anchor='w',bg=THEME['surface'],fg=THEME['text'],font=FONT_BODY,padx=THEME['space_md'],pady=THEME['space_sm'],cursor='hand2');label.pack(fill='x');label.bind('<Button-1>',lambda _e,value=item:self._use_suggestion(value));label.bind('<Enter>',lambda _e,w=label:w.configure(bg=THEME['selection']));label.bind('<Leave>',lambda _e,w=label:w.configure(bg=THEME['surface']))
            panel.update_idletasks();panel.place(x=self.entry.winfo_x(),y=self.entry.winfo_y()+self.entry.winfo_height()+3,width=max(self.entry.winfo_width(),420));panel.lift()
        except tk.TclError:self._hide_suggestions()
    def _use_suggestion(self,value):self.q.set(value);self._hide_suggestions();self.search()
    def clear_search_history(self):
        try:self.h.clear()
        except Exception as exc:self.status.config(text=f'清除搜索历史失败：{exc}');return
        self._hide_suggestions();self.status.config(text='搜索历史已清除');self.entry.focus_set()
    def _hide_suggestions(self):
        panel=getattr(self,'_history_panel',None)
        if panel is not None:
            try:panel.place_forget();panel.destroy()
            except tk.TclError:pass
        self._history_panel=None
    def _dismiss_suggestions(self,event=None):
        if event is None:return
        panel=getattr(self,'_history_panel',None)
        if panel is None:return
        try:
            ex,ey=event.x_root,event.y_root;px,py=self.entry.winfo_rootx(),self.entry.winfo_rooty()
            if px<=ex<=px+self.entry.winfo_width() and py<=ey<=py+self.entry.winfo_height():self.root.after_idle(self._refresh_suggestions);return
            x,y=panel.winfo_rootx(),panel.winfo_rooty()
            if x<=ex<=x+panel.winfo_width() and y<=ey<=y+panel.winfo_height():return
        except tk.TclError:pass
        self._hide_suggestions()
    def condition_compare(self):
        rows=list(self.rows or [])
        if not rows:return self.toast('请先查询品牌、系列或型号')
        from detail_compare_view import show_condition_compare
        return show_condition_compare(self,rows)
    def history_compare(self):
        rows=list(self.rows or [])
        if not rows:return self.toast('请先查询品牌、系列或型号')
        from detail_compare_view import show_history_compare
        return show_history_compare(self,rows)

def _clear_result_views(self):
    for frame in getattr(self,'_result_views',[]):
        try:frame.destroy()
        except tk.TclError:pass
    self._result_views=[];self._result_trees=[];self._result_tree_map={};self._result_order=[]

def _configure_result_tree(tree,columns,iid,display,favorite):
    fields=[c[0] for c in columns]+['favorite'];tree.configure(columns=fields,show='headings',height=1,selectmode='none',style='Search.Treeview')
    for field,title,width in columns:tree.heading(field,text=title);tree.column(field,width=width,minwidth=max(60,min(width,90)),anchor='center' if field=='data_date' or field.startswith('condition_') else 'w',stretch=True)
    tree.heading('favorite',text='收藏');tree.column('favorite',width=110,minwidth=90,anchor='center',stretch=True);values=[display.get(field,'') for field,_,_ in columns];tag=f"m{display['_model_index']}d{display['_period_index']}";tree.insert('','end',iid=iid,values=values+['★ 已收藏' if favorite else '☆ 一键收藏'],tags=(tag,));tree.tag_configure(tag,background=THEME['model_bands'][display['_model_index']%len(THEME['model_bands'])])

def _render_search_matrix(self,result):
    _clear_result_views(self);self.map={};self._matrix_map={};self._display_columns=();blocks=build_result_blocks(list(result or []));parent=getattr(self,'_results_inner',None)
    if parent is None:self.rows=list(result or []);return
    previous_model=None
    for block in blocks:
        model_index,period_index=block['_model_index'],block['_period_index']
        if previous_model is not None and model_index!=previous_model:
            for _ in range(2):spacer=tk.Frame(parent,height=THEME['model_gap'],background=THEME['surface'],highlightthickness=1,highlightbackground=THEME['border_soft']);spacer.pack(fill='x',pady=(THEME['space_xs'],THEME['space_xs']));self._result_views.append(spacer)
        elif period_index>0:
            spacer=tk.Frame(parent,height=THEME['period_gap'],background=THEME['surface'],highlightthickness=1,highlightbackground=THEME['border_soft']);spacer.pack(fill='x',pady=(THEME['space_xs'],THEME['space_xs']));self._result_views.append(spacer)
        columns=tuple(block.get('_columns') or ());self._display_columns=columns or self._display_columns;iid=f'result-{len(self._matrix_map)}';rows=list(block.get('_rows') or []);favorite_keys={self.fav.identity(r) for r in self.fav.dedupe()};favorite=any(self.fav.identity(r) in favorite_keys for r in rows);frame=tk.Frame(parent,bd=0,highlightthickness=0,background=THEME['surface']);tree=ttk.Treeview(frame,columns=(),show='headings',height=1,selectmode='none',style='Search.Treeview');_configure_result_tree(tree,columns,iid,block,favorite);tree.bind('<Double-1>',lambda _event,iid=iid:self._result_double_click(iid));tree.pack(fill='x',expand=True);frame.pack(fill='x',expand=True,pady=(0,THEME['result_gap']));self._result_views.append(frame);self._result_trees.append(tree);self._result_tree_map[iid]=tree;self._result_order.append(iid);self._matrix_map[iid]=block
        if rows:
            self.map[iid]=rows[0]
            for row in rows:
                rid=phone_search.rid(row)
                if rid:self.map[rid]=row
        previous_model=model_index
    try:self._results_canvas.configure(scrollregion=self._results_canvas.bbox('all'));self.empty_hint.place_forget() if self._matrix_map else self.empty_hint.place(relx=.5,rely=.5,anchor='center')
    except tk.TclError:pass

def favorite_groups(self):return group_model_dates(self.fav.dedupe())
def _poll_async_results(self):
    try:
        while True:query_id,q,record_history,future=_UI_QUEUE.get_nowait();_apply_async_result(self,query_id,q,record_history,future)
    except Empty:pass
    try:self.root.after(25,lambda:_poll_async_results(self))
    except tk.TclError:pass

def _apply_async_result(self,query_id,q,record_history,future):
    if query_id!=getattr(self,'_search_query_id',0):return
    try:result=future.result()
    except Exception as exc:self.status.config(text=f'搜索失败：{type(exc).__name__}: {exc}');return
    self.rows=list(result or []);self.h.add(q) if record_history else None;self.render(self.rows);self.target.config(text=f'搜索结果：{q} · {len(self._matrix_map)} 个结果块');self.status.config(text=f'找到 {len(self._matrix_map)} 个结果块');self._refresh_suggestions()
def _queue_async_result(query_id,q,record_history,future):_UI_QUEUE.put((query_id,q,record_history,future))
def _debounced_search(self):
    try:self.root.after_cancel(self._search_after_id)
    except Exception:pass
    self._search_after_id=self.root.after(180,lambda:self.search(False))
def clear_search(self):
    for attr in ('_search_after_id','_sync_search_after_id'):
        try:self.root.after_cancel(getattr(self,attr))
        except Exception:pass
    self._search_query_id=getattr(self,'_search_query_id',0)+1;self.q.set('');self._hide_suggestions();self.rows=[];self.map={};self._matrix_map={};self._display_columns=()
    try:self.tree.delete(*self.tree.get_children())
    except tk.TclError:pass
    _clear_result_views(self);self.target.config(text='输入品牌、系列、型号开始查询')
    try:self.empty_hint.place(relx=.5,rely=.5,anchor='center')
    except tk.TclError:pass
    self.status.config(text='请输入品牌、系列、型号或别名');self.entry.focus_set()
def add_favorite_all_search_results(self):return self.addToFavorites(list(self.rows or []))
install_app_actions(SearchApp);install_matrix_actions(SearchApp);SearchApp.render=_render_search_matrix;SearchApp.favorite_groups=favorite_groups;SearchApp.clear_search=clear_search;SearchApp.add_favorite=add_favorite_all_search_results;SearchApp._poll_async_results=_poll_async_results;SearchApp._apply_async_result=_apply_async_result;SearchApp._queue_async_result=_queue_async_result;SearchApp._debounced_search=_debounced_search
if __name__=='__main__':root=tk.Tk();app=SearchApp(root);root.mainloop()
