"""Reference-style Tk bootstrap for the desktop search/result surface."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from queue import Empty

import phone_search
from app_actions import install as install_app_actions
from matrix_ui_actions import install as install_matrix_actions
from search_display import build_result_blocks, group_model_dates
from ui_theme import THEME, FONT_BODY, FONT_LABEL, FONT_TITLE, FONT_SEARCH

_UI_QUEUE = __import__("queue").Queue()


def _screen_fit_geometry(root, geometry=None, minsize=None):
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    raw_w, raw_h = 1200, 720
    if geometry:
        try:
            raw_w, raw_h = (
                int(x) for x in str(geometry).split("+", 1)[0].lower().split("x", 1)
            )
        except (ValueError, TypeError):
            pass
    w = min(raw_w, max(900, sw - 36))
    h = min(raw_h, max(600, sh - 72))
    if minsize:
        mw, mh = minsize
        w = min(max(w, min(mw, sw - 36)), sw - 36)
        h = min(max(h, min(mh, sh - 72)), sh - 72)
    return w, h, max(12, (sw - w) // 2), max(12, (sh - h) // 2)


def _new_window(self, title, geometry=None, minsize=None):
    if "我的收藏" in str(title):
        title = str(title).replace("我的收藏", "展示收藏")
    w = tk.Toplevel(self.root)
    w.title(title)
    width, height, x, y = _screen_fit_geometry(w, geometry, minsize)
    w.geometry(f"{width}x{height}+{x}+{y}")
    w.minsize(min(width, x + width), min(height, y + height))
    w.configure(background=THEME["window_bg"])
    try:
        w.transient(self.root)
        w.lift()
        w.focus_force()
    except tk.TclError:
        pass
    return w


class SearchApp(phone_search.App):
    _new_window = _new_window

    def ui(self):
        root = self.root
        root.configure(background=THEME["window_bg"])
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
            style.configure("TFrame", background=THEME["window_bg"])
            style.configure("Search.TFrame", background=THEME["surface"], borderwidth=1, relief="solid")
            style.configure("Results.TFrame", background=THEME["surface"])
            style.configure("Info.TFrame", background=THEME["surface"])
            style.configure("Action.TFrame", background=THEME["surface"])
            style.configure("TLabel", background=THEME["window_bg"], foreground=THEME["text"], font=FONT_BODY)
            style.configure("Search.TLabel", background=THEME["surface"], foreground=THEME["text_secondary"], font=FONT_LABEL)
            style.configure("Title.TLabel", background=THEME["surface"], foreground=THEME["text"], font=FONT_TITLE)
            style.configure("Meta.TLabel", background=THEME["surface"], foreground=THEME["text_secondary"], font=FONT_BODY)
            style.configure("Status.TLabel", background=THEME["surface"], foreground=THEME["text_muted"], font=FONT_BODY)
            base = dict(background=THEME["button_bg"], font=FONT_BODY, padding=(THEME["button_pad_x"], THEME["button_pad_y"]), relief="solid", borderwidth=1)
            style.configure("TButton", **base, foreground=THEME["button_text"])
            style.map("TButton", background=[("active", THEME["button_hover"]), ("pressed", THEME["button_pressed"]), ("disabled", THEME["button_disabled"])], foreground=[("disabled", THEME["text_muted"])])
            for name in ("Primary.TButton", "Favorite.TButton", "Compare.TButton"):
                style.configure(name, **base, foreground=THEME["button_accent_text"])
                style.map(name, background=[("active", THEME["accent_soft"]), ("pressed", THEME["button_pressed"]), ("disabled", THEME["button_disabled"])])
            style.configure("Search.Treeview", font=FONT_BODY, rowheight=THEME["table_row_height"], background=THEME["table_bg"], fieldbackground=THEME["table_bg"], foreground=THEME["text"], borderwidth=0, relief="flat")
            style.configure("Search.Treeview.Heading", font=FONT_TITLE, background=THEME["table_header"], foreground=THEME["text"], padding=(THEME["space_sm"], 5), relief="flat", borderwidth=0)
            style.map("Search.Treeview", background=[("selected", THEME["selection"])], foreground=[("selected", THEME["text"])])
            style.configure("TCombobox", fieldbackground=THEME["surface"], background=THEME["surface"], foreground=THEME["text"], arrowcolor=THEME["accent"])
        except tk.TclError:
            pass

        # Canonical horizontal search toolbar: input+clear, search button, category group.
        toolbar = tk.Frame(root, bg=THEME["window_bg"], bd=0, highlightthickness=0)
        toolbar.pack(fill="x", padx=THEME["space_lg"], pady=(THEME["space_lg"], THEME["space_sm"]))
        toolbar.grid_columnconfigure(0, weight=1)
        toolbar.grid_rowconfigure(0, minsize=44, weight=0)

        search_shell = tk.Frame(toolbar, bg=THEME["surface"], bd=1, relief="solid", highlightthickness=1, highlightbackground=THEME["border"], highlightcolor=THEME["accent"], height=44)
        search_shell.grid(row=0, column=0, sticky="ew")
        search_shell.pack_propagate(False)
        self.search_bar = search_shell
        tk.Label(search_shell, text="⌕", bg=THEME["surface"], fg=THEME["text"], font=("SimHei", 18), padx=THEME["space_md"]).pack(side="left")
        self.q = tk.StringVar()
        self.entry = tk.Entry(search_shell, textvariable=self.q, font=FONT_SEARCH, width=30, bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["accent"], relief="flat", bd=0, highlightthickness=0)
        self.entry.pack(side="left", padx=(0, THEME["space_sm"]), ipady=7, fill="x", expand=True)
        self.entry.bind("<Return>", lambda _e: self.search())
        self.entry.bind("<FocusIn>", lambda _e: self.root.after_idle(self._refresh_suggestions_ui))
        self.entry.bind("<Escape>", lambda _e: self._hide_suggestions_ui())
        self.entry.bind("<KeyRelease>", lambda _e: self.root.after_idle(self._reposition_history_popup))
        self.clear_button = tk.Button(search_shell, text="×", command=self.clear_search, bg=THEME["surface"], fg=THEME["text_muted"], activebackground=THEME["surface_subtle"], activeforeground=THEME["text_secondary"], relief="flat", bd=0, font=("SimHei", 17), padx=7, cursor="hand2", height=1)
        self.clear_button.pack(side="left", padx=(0, 4))

        search_button = tk.Button(toolbar, text="搜索", command=self.search, bg=THEME["button_bg"], fg=THEME["button_text"], activebackground=THEME["button_hover"], activeforeground=THEME["accent"], relief="solid", bd=1, highlightthickness=0, font=FONT_BODY, padx=THEME["button_pad_x"], pady=THEME["button_pad_y"], cursor="hand2", width=7, height=1)
        search_button.grid(row=0, column=1, sticky="ns", padx=(THEME["space_sm"], 0))
        self.search_button = search_button

        category_group = tk.Frame(toolbar, bg=THEME["window_bg"], bd=0, highlightthickness=0, height=44)
        category_group.grid(row=0, column=2, sticky="ns", padx=(THEME["space_lg"], 0))
        category_group.pack_propagate(False)
        tk.Label(category_group, text="分类：", bg=THEME["window_bg"], fg=THEME["text_secondary"], font=FONT_BODY).pack(side="left", fill="y", padx=(0, THEME["space_xs"]))
        category_var = tk.StringVar(value="全部")
        cat_style = "Search.Category.TCombobox"
        style.configure(cat_style, font=FONT_BODY, padding=(THEME["button_pad_x"], THEME["button_pad_y"]), fieldbackground=THEME["button_bg"], background=THEME["button_bg"], foreground=THEME["button_text"], arrowcolor=THEME["accent"], borderwidth=1, relief="solid")
        style.map(cat_style, fieldbackground=[("readonly", THEME["button_bg"]), ("active", THEME["button_hover"])], background=[("readonly", THEME["button_bg"]), ("active", THEME["button_hover"])], foreground=[("readonly", THEME["button_text"])])
        self.cat = ttk.Combobox(category_group, textvariable=category_var, values=["全部", "手机", "平板", "电脑", "其它", "手机配件"], state="readonly", width=7, style=cat_style)
        self.cat.set("全部")
        self.cat.pack(side="left", fill="y")
        self._category_var = category_var
        self.manage_category_button = None

        utility = ttk.Frame(root, style="Info.TFrame", padding=(THEME["space_lg"], 0, THEME["space_lg"], 8))
        utility.pack(fill="x")
        self.target = ttk.Label(utility, text="输入品牌、系列、型号开始查询", style="Title.TLabel")
        self.target.pack(side="left")
        self.status = ttk.Label(utility, text="", style="Status.TLabel")
        self.status.pack(side="right")

        host = ttk.Frame(root, style="Results.TFrame", padding=0)
        host.pack(fill="both", expand=True, padx=THEME["space_lg"], pady=(0, THEME["space_lg"]))
        result_toolbar = tk.Frame(host, bg=THEME["surface"], highlightthickness=1, highlightbackground=THEME["border_soft"], bd=0)
        result_toolbar.pack(fill="x")
        left = tk.Frame(result_toolbar, bg=THEME["surface"])
        left.pack(side="left", padx=THEME["space_md"], pady=THEME["space_sm"])
        tk.Label(left, text="搜索结果", bg=THEME["surface"], fg=THEME["text"], font=FONT_TITLE).pack(side="left", padx=(0, 8))
        self.result_count = tk.Label(left, text="0 条", bg=THEME["surface"], fg=THEME["text_muted"], font=FONT_BODY)
        self.result_count.pack(side="left")
        actions = tk.Frame(result_toolbar, bg=THEME["surface"])
        actions.pack(side="right", padx=THEME["space_sm"], pady=THEME["space_xs"])
        def action(text, command, accent=False):
            return tk.Button(actions, text=text, command=command, bg=THEME["button_bg"], fg=THEME["button_accent_text"] if accent else THEME["button_text"], activebackground=THEME["accent_soft"] if accent else THEME["button_hover"], activeforeground=THEME["accent"], relief="solid", bd=1, highlightthickness=0, font=FONT_BODY, padx=THEME["button_pad_x"], pady=THEME["button_pad_y"], cursor="hand2")
        # Required order: favorites, data operations, comparison utilities.
        action("☆ 一键收藏", self.add_favorite, True).pack(side="left", padx=2)
        action("展示收藏", self.show_favorites, True).pack(side="left", padx=2)
        action("复制全部", self.copy_all).pack(side="left", padx=2)
        action("导出 CSV", self.export_csv).pack(side="left", padx=2)
        action("导出 Excel", self.export_xlsx).pack(side="left", padx=2)
        action("条件比价", self.condition_compare).pack(side="left", padx=2)
        action("历史对比", self.history_compare).pack(side="left", padx=2)

        matrix_host = tk.Frame(host, bg=THEME["surface"], highlightthickness=1, highlightbackground=THEME["border_soft"], bd=0)
        matrix_host.pack(fill="both", expand=True, pady=(1, 0))
        self._results_canvas = tk.Canvas(matrix_host, highlightthickness=0, bd=0, background=THEME["surface"], relief="flat")
        scroll = ttk.Scrollbar(matrix_host, orient="vertical", command=self._results_canvas.yview)
        self._results_canvas.configure(yscrollcommand=scroll.set)
        self._results_canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        matrix_host.grid_rowconfigure(0, weight=1)
        matrix_host.grid_columnconfigure(0, weight=1)
        self._results_inner = tk.Frame(self._results_canvas, background=THEME["surface"])
        self._results_window = self._results_canvas.create_window((0, 0), window=self._results_inner, anchor="nw")
        self._results_inner.bind("<Configure>", lambda _e: self._results_canvas.configure(scrollregion=self._results_canvas.bbox("all")))
        self._results_canvas.bind("<Configure>", self._resize_results_inner)
        self.empty_hint = tk.Label(matrix_host, text="输入品牌、系列、型号开始查询", bg=THEME["surface"], fg=THEME["text_muted"], font=FONT_TITLE)
        self.empty_hint.place(relx=0.5, rely=0.5, anchor="center")
        self._result_views = []
        self._result_trees = []
        self._result_tree_map = {}
        self._result_order = []
        self._matrix_map = {}
        self._display_columns = ()
        self.tree = ttk.Treeview(matrix_host, columns=[x[0] for x in phone_search.COLS] + ["favorite"], show="headings", selectmode="none")
        self.tree.grid_remove()
        original_remove = self.fav.remove
        def sync_remove(rows):
            result = original_remove(rows)
            current = list(getattr(self, "rows", []) or [])
            if current:
                renderer = getattr(self, "render", None)
                if callable(renderer): renderer(current)
            return result
        self.fav.remove = sync_remove
        root.bind("<Button-1>", self._dismiss_suggestions, add="+")
        root.bind("<Configure>", self._reposition_history_popup, add="+")

    def _resize_results_inner(self, event):
        try: self._results_canvas.itemconfigure(self._results_window, width=event.width)
        except tk.TclError: pass

    def _new_window(self, title, geometry=None, minsize=None): return _new_window(self, title, geometry, minsize)
    def _patch_search_history_ui(self): return None

    def _history_popup(self):
        popup = getattr(self, "suggest_popup", None)
        try:
            if popup is not None and popup.winfo_exists(): return popup
        except tk.TclError: pass
        try:
            popup = tk.Toplevel(self.root); popup.overrideredirect(True); popup.transient(self.root); popup.withdraw(); popup.configure(bg=THEME["surface"]); popup.attributes("-topmost", False); popup.bind("<Escape>", lambda _e: self._hide_suggestions_ui()); self.suggest_popup = popup; return popup
        except tk.TclError:
            self.suggest_popup = None; return None

    def _reposition_history_popup(self, _event=None):
        popup = getattr(self, "suggest_popup", None)
        if popup is None: return
        try:
            if not popup.winfo_exists(): return
            popup.update_idletasks(); width=max(self.entry.winfo_width(),460); x=self.entry.winfo_rootx(); y=self.entry.winfo_rooty()+self.entry.winfo_height()+4; popup.geometry(f"{width}x{popup.winfo_height()}+{x}+{y}")
        except tk.TclError: pass

    def _refresh_suggestions_ui(self):
        if not hasattr(self, "entry") or not hasattr(self, "h"): return
        try:
            query=phone_search.clean(self.q.get()); matches=list(self.h.suggestions(query,12)); items=matches; mode="匹配历史" if query and matches else "最近搜索"
            if query and not matches: items=list(self.h.suggestions("",12))
            popup=self._history_popup()
            if popup is None:return
            for child in popup.winfo_children():child.destroy()
            outer=tk.Frame(popup,bg=THEME["surface"],bd=1,relief="solid",highlightthickness=1,highlightbackground=THEME["border"]);outer.pack(fill="both",expand=True)
            header=tk.Frame(outer,bg=THEME["surface"],height=44);header.pack(fill="x");header.pack_propagate(False)
            tk.Label(header,text="⌕",bg=THEME["surface"],fg=THEME["text"],font=("SimHei",16),padx=THEME["space_md"]).pack(side="left")
            tk.Label(header,text=mode,anchor="w",bg=THEME["surface"],fg=THEME["text"],font=FONT_TITLE).pack(side="left",fill="both",expand=True)
            tk.Label(header,text=f"{len(items)} 条",bg=THEME["surface"],fg=THEME["text_muted"],font=FONT_BODY,padx=THEME["space_sm"]).pack(side="left")
            tk.Button(header,text="清空",command=self.clear_search_history,bg=THEME["surface"],fg=THEME["text_secondary"],activebackground=THEME["surface_subtle"],activeforeground=THEME["accent"],relief="flat",bd=0,font=FONT_BODY,padx=THEME["space_md"],cursor="hand2").pack(side="right",fill="y")
            body=tk.Frame(outer,bg=THEME["surface"],bd=0);body.pack(fill="both",expand=True)
            if items:
                for item in items:
                    row=tk.Frame(body,bg=THEME["surface"],height=40);row.pack(fill="x");row.pack_propagate(False)
                    marker=tk.Label(row,text="◷",bg=THEME["surface"],fg=THEME["text_muted"],font=("SimHei",12),width=3);marker.pack(side="left")
                    label=tk.Label(row,text=item,anchor="w",bg=THEME["surface"],fg=THEME["text"],font=FONT_BODY,padx=THEME["space_xs"],cursor="hand2");label.pack(side="left",fill="both",expand=True)
                    for widget in (row,marker,label):
                        widget.bind("<Button-1>",lambda _e,value=item:self._use_suggestion(value));widget.bind("<Enter>",lambda _e,w=row:self._history_hover(w,True));widget.bind("<Leave>",lambda _e,w=row:self._history_hover(w,False))
            else:
                tk.Label(body,text="暂无搜索历史记录",anchor="w",bg=THEME["surface"],fg=THEME["text_muted"],font=FONT_BODY,padx=THEME["space_md"],pady=THEME["space_md"]).pack(fill="x")
            popup.update_idletasks(); width=max(self.entry.winfo_width(),460); height=max(120,min(44+len(items)*40+2,520)); x=self.entry.winfo_rootx(); y=self.entry.winfo_rooty()+self.entry.winfo_height()+4; popup.geometry(f"{width}x{height}+{x}+{y}"); popup.deiconify(); popup.lift()
        except tk.TclError: self._hide_suggestions_ui()

    def _history_hover(self,row,active):
        try:
            bg=THEME["selection"] if active else THEME["surface"]; row.configure(bg=bg)
            for child in row.winfo_children(): child.configure(bg=bg)
        except tk.TclError: pass

    def clear_search_history(self):
        try: self.h.clear()
        except Exception as exc: self.status.config(text=f"清空搜索历史失败：{exc}"); return
        self.status.config(text="搜索历史已清空"); self.entry.focus_set(); self._refresh_suggestions_ui()

    def _use_suggestion(self,value): self._hide_suggestions_ui(); self.q.set(value); self.search()

    def _hide_suggestions_ui(self):
        popup=getattr(self,"suggest_popup",None)
        if popup is not None:
            try: popup.destroy()
            except tk.TclError: pass
        self.suggest_popup=None

    def _dismiss_suggestions(self,event=None):
        if event is None:return
        popup=getattr(self,"suggest_popup",None)
        if popup is None:return
        try:
            ex,ey=event.x_root,event.y_root; px,py=self.entry.winfo_rootx(),self.entry.winfo_rooty()
            if px<=ex<=px+self.entry.winfo_width() and py<=ey<=py+self.entry.winfo_height(): self.root.after_idle(self._refresh_suggestions_ui); return
            x1,y1=popup.winfo_rootx(),popup.winfo_rooty();x2,y2=x1+popup.winfo_width(),y1+popup.winfo_height()
            if x1<=ex<=x2 and y1<=ey<=y2:return
        except tk.TclError:return
        self._hide_suggestions_ui()

    def _result_double_click(self,iid):
        rows=list((self._matrix_map.get(iid) or {}).get("_rows") or [])
        if rows:self.detail_rows(rows)
        return "break"

    def _result_action_favorite(self,iid):
        rows=list((self._matrix_map.get(iid) or {}).get("_rows") or [])
        return self.addToFavorites(rows) if rows else None

    def condition_compare(self):
        rows=list(self.rows or [])
        if not rows:return self.toast("请先查询品牌、系列或型号")
        from detail_compare_view import show_condition_compare
        return show_condition_compare(self,rows)

    def history_compare(self):
        rows=list(self.rows or [])
        if not rows:return self.toast("请先查询品牌、系列或型号")
        from detail_compare_view import show_history_compare
        return show_history_compare(self,rows)


def _clear_result_views(self):
    for frame in getattr(self,"_result_views",[]):
        try:frame.destroy()
        except tk.TclError:pass
    self._result_views=[];self._result_trees=[];self._result_tree_map={};self._result_order=[]


def _configure_result_tree(tree,columns,iid,display,favorite):
    fields=[c[0] for c in columns]+["favorite"]; tree.configure(columns=fields,show="headings",height=1,selectmode="none",style="Search.Treeview")
    for field,title,width in columns:
        anchor="center" if field=="data_date" or field.startswith("condition_") else "w"; tree.heading(field,text=title); tree.column(field,width=width,minwidth=max(60,min(width,90)),anchor=anchor,stretch=True)
    tree.heading("favorite",text="收藏"); tree.column("favorite",width=110,minwidth=90,anchor="center",stretch=True)
    values=[display.get(field,"") for field,_,_ in columns]; values.append("★ 已收藏" if favorite else "☆ 收藏"); tag=f"m{display['_model_index']}d{display['_period_index']}"; tree.insert("","end",iid=iid,values=values,tags=(tag,)); tree.tag_configure(tag,background=THEME["model_bands"][display["_model_index"]%len(THEME["model_bands"])])


def _render_search_matrix(self,result):
    _clear_result_views(self); self.map={}; self._matrix_map={}; self._display_columns=(); blocks=build_result_blocks(list(result or [])); parent=getattr(self,"_results_inner",None)
    if parent is None:self.rows=list(result or []);return
    previous_model=None
    for block in blocks:
        model_index=block["_model_index"]; period_index=block["_period_index"]
        if previous_model is not None and model_index!=previous_model:
            for _ in range(2):
                spacer=tk.Frame(parent,height=THEME["model_gap"],background=THEME["model_separator"],highlightthickness=1,highlightbackground=THEME["model_separator_line"]); spacer.pack(fill="x",pady=(THEME["space_xs"],THEME["space_xs"])); self._result_views.append(spacer)
        elif period_index>0:
            spacer=tk.Frame(parent,height=THEME["period_gap"],background=THEME["period_separator"],highlightthickness=1,highlightbackground=THEME["separator_line"]); spacer.pack(fill="x",pady=(THEME["space_xs"],THEME["space_xs"])); self._result_views.append(spacer)
        columns=tuple(block.get("_columns") or ()); self._display_columns=columns or self._display_columns; iid=f"result-{len(self._matrix_map)}"; rows=list(block.get("_rows") or []); favorite_keys={self.fav.identity(r) for r in self.fav.dedupe()}; favorite=any(self.fav.identity(r) in favorite_keys for r in rows)
        frame=tk.Frame(parent,bd=0,highlightthickness=0,background=THEME["surface"]); tree=ttk.Treeview(frame,columns=(),show="headings",height=1,selectmode="none",style="Search.Treeview"); _configure_result_tree(tree,columns,iid,block,favorite); tree.bind("<Double-1>",lambda _event,value=iid:self._result_double_click(value))
        def on_click(event,value=iid):
            if tree.identify_column(event.x)==f"#{len(columns)+1}": self._result_action_favorite(value); return "break"
        tree.bind("<Button-1>",on_click,add="+"); tree.pack(fill="x",expand=True); frame.pack(fill="x",expand=True,pady=(0,THEME["result_gap"])); self._result_views.append(frame); self._result_trees.append(tree); self._result_tree_map[iid]=tree; self._result_order.append(iid); self._matrix_map[iid]=block
        if rows:
            self.map[iid]=rows[0]
            for row in rows:
                rid=phone_search.rid(row)
                if rid:self.map[rid]=row
        previous_model=model_index
    try:
        self._results_canvas.configure(scrollregion=self._results_canvas.bbox("all")); self.empty_hint.place_forget() if self._matrix_map else self.empty_hint.place(relx=.5,rely=.5,anchor="center"); self.result_count.config(text=f"{len(self.rows)} 条 · {len(self._matrix_map)} 结果块")
    except tk.TclError:pass


def favorite_groups(self):return group_model_dates(self.fav.dedupe())


def _poll_async_results(self):
    try:
        while True:
            query_id,q,record_history,future=_UI_QUEUE.get_nowait(); _apply_async_result(self,query_id,q,record_history,future)
    except Empty:pass
    try:self.root.after(25,lambda:_poll_async_results(self))
    except tk.TclError:pass


def _apply_async_result(self,query_id,q,record_history,future):
    if query_id!=getattr(self,"_search_query_id",0):return
    try:result=future.result()
    except Exception as exc:self.status.config(text=f"搜索失败：{type(exc).__name__}: {exc}");return
    self.rows=list(result or [])
    if record_history:self.h.add(q)
    self.render(self.rows); self.target.config(text=f"搜索结果：{q}"); self.status.config(text=f"找到 {len(self._matrix_map)} 个结果块"); self._refresh_suggestions_ui()


def _queue_async_result(query_id,q,record_history,future):_UI_QUEUE.put((query_id,q,record_history,future))


def _debounced_search(self):
    try:self.root.after_cancel(self._search_after_id)
    except Exception:pass
    self._search_after_id=self.root.after(180,lambda:self.search(False))


def clear_search(self):
    for attr in ("_search_after_id","_sync_search_after_id"):
        try:self.root.after_cancel(getattr(self,attr))
        except Exception:pass
    self._search_query_id=getattr(self,"_search_query_id",0)+1; self.q.set(""); self._hide_suggestions_ui(); self.rows=[]; self.map={}; self._matrix_map={}; self._display_columns=()
    try:self.tree.delete(*self.tree.get_children())
    except tk.TclError:pass
    _clear_result_views(self); self.target.config(text="输入品牌、系列、型号开始查询"); self.result_count.config(text="0 条")
    try:self.empty_hint.place(relx=.5,rely=.5,anchor="center")
    except tk.TclError:pass
    self.status.config(text="请输入品牌、系列、型号或别名"); self.entry.focus_set()


def add_favorite_all_search_results(self):
    rows=list(self.rows or []); result=self.addToFavorites(rows)
    if rows:
        renderer=getattr(self,"render",None)
        if callable(renderer):renderer(rows)
    return result


install_app_actions(SearchApp)
install_matrix_actions(SearchApp)
SearchApp.render=_render_search_matrix
SearchApp.favorite_groups=favorite_groups
SearchApp.clear_search=clear_search
SearchApp.add_favorite=add_favorite_all_search_results
SearchApp._poll_async_results=_poll_async_results
SearchApp._apply_async_result=_apply_async_result
SearchApp._queue_async_result=_queue_async_result
SearchApp._debounced_search=_debounced_search

if __name__=="__main__":
    root=tk.Tk(); app=SearchApp(root); root.mainloop()
