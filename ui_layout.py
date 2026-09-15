"""Canonical desktop search-toolbar layout.

The layout is applied after either the reference SearchApp UI or the legacy
phone_search.App UI.  It deliberately removes duplicate search/category
controls instead of leaving two competing toolbars visible.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui_theme import THEME, FONT_BODY, FONT_LABEL, FONT_TITLE, FONT_SEARCH


def _walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def _find_text(widget, text):
    for child in _walk(widget):
        try:
            if str(child.cget("text")) == text:
                return child
        except (tk.TclError, TypeError):
            continue
    return None


def _button_children(frame):
    out = []
    for child in frame.winfo_children():
        try:
            if child.winfo_class() == "Button":
                out.append(child)
        except tk.TclError:
            pass
    return out


def _button_style_kwargs(accent=False):
    return dict(
        font=FONT_BODY,
        bg=THEME["button_bg"],
        fg=THEME["button_accent_text"] if accent else THEME["button_text"],
        activebackground=THEME["accent_soft"] if accent else THEME["button_hover"],
        activeforeground=THEME["accent"],
        relief="solid",
        bd=1,
        highlightthickness=0,
        padx=THEME["primary_pad_x"] if accent else THEME["button_pad_x"],
        pady=THEME["primary_pad_y"] if accent else THEME["button_pad_y"],
        cursor="hand2",
    )


def _configure_category(root, parent):
    style_name = "Search.Category.TCombobox"
    style = ttk.Style(root)
    style.configure(
        style_name,
        font=FONT_BODY,
        padding=(THEME["button_pad_x"], THEME["button_pad_y"]),
        fieldbackground=THEME["button_bg"],
        background=THEME["button_bg"],
        foreground=THEME["button_text"],
        arrowcolor=THEME["accent"],
        borderwidth=1,
        relief="solid",
    )
    style.map(
        style_name,
        fieldbackground=[("readonly", THEME["button_bg"]), ("active", THEME["button_hover"])],
        background=[("readonly", THEME["button_bg"]), ("active", THEME["button_hover"])],
        foreground=[("readonly", THEME["button_text"])],
    )
    var = tk.StringVar(value="全部")
    combo = ttk.Combobox(
        parent,
        textvariable=var,
        values=["全部", "手机", "平板", "电脑", "其它", "手机配件"],
        state="readonly",
        width=7,
        style=style_name,
    )
    combo.set("全部")
    combo.pack(side="left")
    return var, combo


def _build_canonical_row(app, host):
    root = app.root
    old_entry = getattr(app, "entry", None)
    q = getattr(app, "q", None) or tk.StringVar()

    for child in list(host.winfo_children()):
        try:
            child.destroy()
        except tk.TclError:
            pass
    host.configure(padding=0)
    host.pack(fill="x", padx=THEME["space_lg"], pady=(THEME["space_lg"], THEME["space_sm"]))

    shell = tk.Frame(
        host,
        bg=THEME["surface"],
        bd=1,
        relief="solid",
        highlightthickness=1,
        highlightbackground=THEME["border"],
        highlightcolor=THEME["accent"],
        height=44,
    )
    shell.pack(side="left", fill="x", expand=True, pady=0)
    shell.pack_propagate(False)

    tk.Label(
        shell,
        text="⌕",
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("SimHei", 18),
        padx=THEME["space_md"],
    ).pack(side="left")

    entry = tk.Entry(
        shell,
        textvariable=q,
        font=FONT_SEARCH,
        bg=THEME["surface"],
        fg=THEME["text"],
        insertbackground=THEME["accent"],
        relief="flat",
        bd=0,
        highlightthickness=0,
    )
    entry.pack(side="left", padx=(0, THEME["space_sm"]), ipady=7, fill="x", expand=True)
    entry.bind("<Return>", lambda _e: app.search())
    entry.bind("<FocusIn>", lambda _e: root.after_idle(getattr(app, "_refresh_suggestions", lambda: None)))
    entry.bind("<Escape>", lambda _e: getattr(app, "_hide_suggestions", lambda: None)())

    clear = tk.Button(
        shell,
        text="×",
        command=app.clear_search,
        bg=THEME["surface"],
        fg=THEME["text_muted"],
        activebackground=THEME["surface_subtle"],
        activeforeground=THEME["text"],
        relief="flat",
        bd=0,
        font=("SimHei", 16),
        padx=7,
        cursor="hand2",
    )
    clear.pack(side="left")

    search_button = tk.Button(
        host,
        text="搜索",
        command=app.search,
        **_button_style_kwargs(accent=True),
    )
    search_button.configure(width=7)
    search_button.pack(side="left", padx=(THEME["space_sm"], THEME["space_lg"]))

    category_group = tk.Frame(host, bg=THEME["window_bg"], bd=0, highlightthickness=0)
    category_group.pack(side="left", padx=(0, THEME["space_lg"]))
    tk.Label(
        category_group,
        text="分类：",
        bg=THEME["window_bg"],
        fg=THEME["text_secondary"],
        font=FONT_BODY,
    ).pack(side="left", padx=(0, THEME["space_xs"]))
    category_var, cat = _configure_category(root, category_group)

    app.search_bar = shell
    app.q = q
    app.entry = entry
    app.clear_button = clear
    app.search_button = search_button
    app.cat = cat
    app._category_var = category_var
    app.manage_category_button = None
    if old_entry is not None:
        try:
            old_entry.destroy()
        except tk.TclError:
            pass


def _normalize_search_controls(app):
    shell = getattr(app, "search_bar", None)
    if shell is None:
        return
    try:
        # SearchApp already owns a dedicated top-level search shell.  The
        # legacy App owns a padded top frame and has no search_button attr.
        if getattr(app, "search_button", None) is None:
            _build_canonical_row(app, shell)
            return

        root = shell.master
        utility = getattr(getattr(app, "target", None), "master", None)
        old_search = app.search_button
        old_cat = getattr(app, "cat", None)
        clear = getattr(app, "clear_button", None)
        if old_cat is None or clear is None:
            return

        old_search.pack_forget()
        old_cat.pack_forget()
        old_search.destroy()
        old_cat.destroy()

        shell.pack_forget()
        shell.configure(height=44)
        shell.pack_propagate(False)
        kwargs = dict(side="left", fill="x", expand=True, padx=(THEME["space_lg"], THEME["space_sm"]), pady=10)
        if utility is not None:
            kwargs["before"] = utility
        shell.pack(**kwargs)

        controls = getattr(app, "_search_controls", None)
        if controls is None or not controls.winfo_exists():
            controls = tk.Frame(root, bg=THEME["window_bg"], bd=0, highlightthickness=0)
            app._search_controls = controls
        else:
            controls.pack_forget()
            for child in controls.winfo_children():
                try:
                    child.destroy()
                except tk.TclError:
                    pass
        ckwargs = dict(side="left", padx=(0, THEME["space_lg"]), pady=10)
        if utility is not None:
            ckwargs["before"] = utility
        controls.pack(**ckwargs)

        search_button = tk.Button(controls, text="搜索", command=app.search, **_button_style_kwargs(accent=True))
        search_button.configure(width=7)
        search_button.pack(side="left", padx=(0, THEME["space_md"]))
        category_group = tk.Frame(controls, bg=THEME["window_bg"], bd=0, highlightthickness=0)
        category_group.pack(side="left")
        tk.Label(category_group, text="分类：", bg=THEME["window_bg"], fg=THEME["text_secondary"], font=FONT_BODY).pack(side="left", padx=(0, THEME["space_xs"]))
        category_var, cat = _configure_category(root, category_group)

        app.search_button = search_button
        app.cat = cat
        app._category_var = category_var
        app.clear_button = clear
        app.manage_category_button = None
    except tk.TclError:
        return


def organize_search_toolbar(app):
    """Keep result actions in the required semantic order."""
    root = app.root
    title = _find_text(root, "搜索结果")
    if title is None:
        return
    try:
        toolbar = title.master
        children = list(toolbar.winfo_children())
        action_frame = next((c for c in children if len(_button_children(c)) >= 7), None)
        if action_frame is None:
            return
        for child in children:
            try:
                child.pack_forget()
            except tk.TclError:
                pass
        for child in action_frame.winfo_children():
            try:
                child.pack_forget()
                child.grid_forget()
            except tk.TclError:
                pass
        toolbar.grid_columnconfigure(0, weight=1)
        toolbar.grid_columnconfigure(1, weight=0)
        title_group = next((c for c in children if c is not action_frame and _find_text(c, "搜索结果") is not None), None)
        if title_group is None:
            title_group = children[0]
        title_group.grid(row=0, column=0, rowspan=2, sticky="w", padx=(THEME["space_md"], THEME["space_lg"]), pady=THEME["space_sm"])
        action_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=THEME["space_sm"], pady=THEME["space_xs"])
        buttons = _button_children(action_frame)
        if len(buttons) < 7:
            return
        ordered = [buttons[3], buttons[4], buttons[0], buttons[1], buttons[2], buttons[5], buttons[6]]
        groups = (ordered[0:2], ordered[2:5], ordered[5:7])
        column = 0
        for group_index, group in enumerate(groups):
            for index, button in enumerate(group):
                left_pad = 0 if index == 0 else 3
                if group_index and index == 0:
                    left_pad = THEME["space_md"]
                button.grid(row=0, column=column, padx=(left_pad, 3), pady=THEME["space_xs"], sticky="ew")
                column += 1
        toolbar.configure(background=THEME["surface"])
    except tk.TclError:
        return


def _manage_categories(app):
    return None


def apply(app):
    _normalize_search_controls(app)
    organize_search_toolbar(app)
