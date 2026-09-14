"""Detailed comparison windows for the current search target.

Search remains display-only; these windows are read-only detail views. Selection
and mutation stay in 展示收藏.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui_theme import THEME, FONT_BODY, FONT_LABEL, FONT_TITLE
from value_order import value_rank

DETAIL_COLS = (
    ("data_date", "数据日期", 105),
    ("category", "分类", 70),
    ("subtype", "子类型", 80),
    ("brand", "品牌", 105),
    ("series", "系列", 110),
    ("model", "型号", 220),
    ("model_code", "型号代码", 125),
    ("condition", "价格条件", 190),
    ("price", "价格", 90),
    ("unit", "单位", 90),
    ("note", "备注", 260),
    ("source_image", "来源图片", 150),
    ("verified", "已验证", 80),
)


def _clean(value):
    return "" if value is None else str(value).strip()


def _model_key(row):
    return tuple(_clean(row.get(k)).casefold() for k in ("category", "subtype", "brand", "series", "model"))


def _date_key(row):
    return _clean(row.get("data_date"))


def _condition_key(row):
    return tuple(-x for x in value_rank(row)) + (_clean(row.get("condition")),)


def _ordered(rows):
    """Order details semantically; price is never used as a ranking signal."""
    return sorted(list(rows or []), key=lambda r: (_model_key(r), _date_key(r), _condition_key(r)))


def _screen_fit(window, geometry, minsize):
    window.update_idletasks()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    raw_w, raw_h = 1650, 760
    try:
        raw_w, raw_h = (int(x) for x in str(geometry).split("x", 1))
    except (TypeError, ValueError):
        pass
    w = min(raw_w, max(820, sw - 36))
    h = min(raw_h, max(520, sh - 72))
    if minsize:
        w = min(max(w, min(minsize[0], sw - 36)), sw - 36)
        h = min(max(h, min(minsize[1], sh - 72)), sh - 72)
    return w, h, max(12, (sw - w) // 2), max(12, (sh - h) // 2)


def _new_window(app, title):
    w = tk.Toplevel(app.root)
    w.title(title)
    width, height, x, y = _screen_fit(w, "1650x760", (1050, 560))
    w.geometry(f"{width}x{height}+{x}+{y}")
    w.minsize(min(width, w.winfo_screenwidth() - 24), min(height, w.winfo_screenheight() - 48))
    w.configure(background=THEME["window_bg"])
    try:
        w.transient(app.root)
        w.lift()
        w.focus_force()
    except tk.TclError:
        pass
    return w


def _install_styles(style):
    style.configure("CompareHeader.TFrame", background=THEME["surface"], borderwidth=1, relief="solid")
    style.configure("CompareTitle.TLabel", background=THEME["surface"], foreground=THEME["text"], font=FONT_TITLE)
    style.configure("CompareMeta.TLabel", background=THEME["surface"], foreground=THEME["text_secondary"], font=FONT_BODY)
    style.configure("CompareHint.TLabel", background=THEME["surface_alt"], foreground=THEME["text_secondary"], font=FONT_LABEL)
    style.configure("Compare.Treeview", font=FONT_BODY, rowheight=THEME["table_row_height"], background=THEME["surface"], fieldbackground=THEME["surface"], foreground=THEME["text"], borderwidth=0, relief="flat")
    style.configure("Compare.Treeview.Heading", font=FONT_TITLE, background=THEME["table_header"], foreground=THEME["text"], padding=(THEME["space_sm"], 3), relief="flat", borderwidth=0)
    style.configure("CompareSection.TLabel", background=THEME["surface_alt"], foreground=THEME["accent"], font=FONT_LABEL)
    style.configure("CompareClose.TButton", background=THEME["surface"], foreground=THEME["text"], font=FONT_BODY, padding=(THEME["button_pad_x"], THEME["button_pad_y"]), relief="flat", borderwidth=0)
    style.map("CompareClose.TButton", background=[("active", THEME["surface_subtle"]), ("pressed", THEME["selection"])])


def _table(window, rows, title, subtitle, sectioned=True):
    rows = _ordered(rows)
    style = ttk.Style(window)
    try:
        style.theme_use("clam")
        _install_styles(style)
    except tk.TclError:
        pass
    header = ttk.Frame(window, style="CompareHeader.TFrame", padding=(THEME["space_lg"], THEME["space_md"]))
    header.pack(fill="x", padx=THEME["space_lg"], pady=(THEME["space_lg"], THEME["space_sm"]))
    ttk.Label(header, text=title, style="CompareTitle.TLabel").pack(side="left")
    ttk.Label(header, text=subtitle, style="CompareMeta.TLabel").pack(side="right")

    host = ttk.Frame(window, padding=1)
    host.pack(fill="both", expand=True, padx=THEME["space_lg"], pady=(0, THEME["space_sm"]))
    canvas = tk.Canvas(host, background=THEME["surface"], highlightthickness=0, bd=0)
    scroll = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    host.grid_rowconfigure(0, weight=1)
    host.grid_columnconfigure(0, weight=1)
    inner = tk.Frame(canvas, background=THEME["surface"])
    item = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(item, width=e.width))

    previous_model = previous_date = None
    for row in rows:
        model, date = _model_key(row), _date_key(row)
        if sectioned and (model != previous_model or date != previous_date):
            label = f"{_clean(row.get('brand'))} / {_clean(row.get('series'))} / {_clean(row.get('model'))}  ·  {date}"
            ttk.Label(inner, text=label, style="CompareSection.TLabel", padding=(THEME["space_md"], THEME["space_sm"])).pack(fill="x")
        tree = ttk.Treeview(inner, columns=[f for f, _, _ in DETAIL_COLS], show="headings", height=1, selectmode="none", style="Compare.Treeview")
        for field, label, width in DETAIL_COLS:
            tree.heading(field, text=label)
            tree.column(field, width=width, minwidth=60, stretch=True, anchor="center" if field in {"data_date", "condition", "price", "unit", "verified"} else "w")
        tree.insert("", "end", values=[row.get(field, "") for field, _, _ in DETAIL_COLS])
        tree.pack(fill="x", expand=True, pady=(0, THEME["space_xs"]))
        previous_model, previous_date = model, date
    if not rows:
        ttk.Label(inner, text="当前搜索没有可展示的详细记录。", style="CompareHint.TLabel", padding=THEME["space_lg"]).pack(fill="x")
    ttk.Label(window, text="只读详细信息 · 搜索区不提供选择或修改", style="CompareHint.TLabel", padding=(THEME["space_lg"], THEME["space_sm"])).pack(fill="x", padx=THEME["space_lg"])
    ttk.Button(window, text="关闭", style="CompareClose.TButton", command=window.destroy).pack(pady=(THEME["space_sm"], THEME["space_md"]))
    window.bind("<Escape>", lambda _e: window.destroy())
    return window


def show_condition_compare(app, rows):
    rows = list(rows or [])
    if not rows:
        return None
    latest = max((_date_key(r) for r in rows), default="")
    current = [r for r in rows if _date_key(r) == latest] or rows
    models = {_model_key(r) for r in current}
    title = "条件比价 · 当前搜索详细信息"
    subtitle = f"{len(current)} 条报价 · {len(models)} 个型号 · 当前期 {latest}"
    return _table(_new_window(app, title), current, title, subtitle)


def show_history_compare(app, rows):
    rows = list(rows or [])
    if not rows:
        return None
    history = app.s.history(rows) or rows
    dates = sorted({_date_key(r) for r in history if _date_key(r)}, reverse=True)
    models = {_model_key(r) for r in history}
    title = "历史对比 · 当前搜索不同时期详细信息"
    subtitle = f"{len(history)} 条记录 · {len(models)} 个型号 · {len(dates)} 个时期"
    return _table(_new_window(app, title), history, title, subtitle)
