"""Post-layout refinements for the modern desktop search surface."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ui_theme import THEME, FONT_BODY, FONT_TITLE


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
        pady=THEME["button_pad_y"],
        cursor="hand2",
    )


def _normalize_search_controls(app):
    """Separate input from search/category controls without changing callbacks."""
    shell = getattr(app, "search_bar", None)
    entry = getattr(app, "entry", None)
    old_search = getattr(app, "search_button", None)
    clear = getattr(app, "clear_button", None)
    old_cat = getattr(app, "cat", None)
    if not all((shell, entry, old_search, clear, old_cat)):
        return
    try:
        root = shell.master
        utility = getattr(getattr(app, "target", None), "master", None)

        # Remove only the obsolete controls. The entry and clear button remain
        # in the original search surface, preserving history anchoring.
        old_search.pack_forget()
        old_cat.pack_forget()
        old_search.destroy()
        old_cat.destroy()

        # Keep the search surface visually compact. Do not stretch controls to
        # the shell height; native Tk buttons should keep their natural height.
        shell.pack_forget()
        shell.configure(height=44)
        shell.pack_propagate(False)
        pack_kwargs = dict(
            side="left",
            fill="x",
            expand=True,
            padx=(THEME["space_lg"], THEME["space_sm"]),
            pady=(THEME["space_lg"], THEME["space_sm"]),
        )
        if utility is not None:
            pack_kwargs["before"] = utility
        shell.pack(**pack_kwargs)

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

        controls_kwargs = dict(
            side="left",
            fill="y",
            padx=(0, THEME["space_lg"]),
            pady=(THEME["space_lg"], THEME["space_sm"]),
        )
        if utility is not None:
            controls_kwargs["before"] = utility
        controls.pack(**controls_kwargs)

        search_button = tk.Button(
            controls,
            text="搜索",
            command=app.search,
            **_button_style_kwargs(accent=True),
        )
        search_button.configure(width=7)
        search_button.pack(side="left", padx=(0, THEME["space_sm"]))

        tk.Label(
            controls,
            text="分类",
            bg=THEME["window_bg"],
            fg=THEME["text_secondary"],
            font=FONT_BODY,
        ).pack(side="left", padx=THEME["space_xs"])

        category_var = tk.StringVar(value="全部")
        cat = ttk.Combobox(
            controls,
            textvariable=category_var,
            values=["全部", "手机", "平板", "电脑", "其它", "手机配件"],
            state="readonly",
            width=10,
        )
        cat.set("全部")
        cat.configure(font=FONT_BODY)
        cat.pack(side="left", padx=(0, THEME["space_sm"]))

        manage = tk.Button(
            controls,
            text="管理分类",
            command=lambda: _manage_categories(app),
            **_button_style_kwargs(),
        )
        manage.configure(width=7)
        manage.pack(side="left")

        app.search_button = search_button
        app.cat = cat
        app._category_var = category_var
        app.manage_category_button = manage
        app.clear_button = clear
    except tk.TclError:
        return


def _manage_categories(app):
    try:
        win = app._new_window("管理分类", "560x420", (460, 340))
    except Exception:
        return
    try:
        win.configure(background=THEME["window_bg"])
        body = tk.Frame(
            win,
            bg=THEME["surface"],
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=THEME["border_soft"],
        )
        body.pack(fill="both", expand=True, padx=THEME["space_lg"], pady=THEME["space_lg"])
        tk.Label(
            body,
            text="分类筛选",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=FONT_TITLE,
        ).pack(anchor="w", padx=THEME["space_lg"], pady=(THEME["space_lg"], 4))
        tk.Label(
            body,
            text="选择分类后，独立的分类筛选控件会立即更新。",
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=FONT_BODY,
        ).pack(anchor="w", padx=THEME["space_lg"], pady=(0, THEME["space_md"]))

        values = list(app.cat.cget("values"))
        listbox = tk.Listbox(
            body,
            font=FONT_BODY,
            bg=THEME["surface"],
            fg=THEME["text"],
            selectbackground=THEME["selection"],
            selectforeground=THEME["text"],
            relief="solid",
            bd=1,
            highlightthickness=0,
            activestyle="none",
        )
        listbox.pack(fill="both", expand=True, padx=THEME["space_lg"], pady=(0, THEME["space_md"]))
        for value in values:
            listbox.insert("end", value)
        current = app.cat.get()
        if current in values:
            index = values.index(current)
            listbox.selection_set(index)
            listbox.see(index)

        actions = tk.Frame(body, bg=THEME["surface"])
        actions.pack(fill="x", padx=THEME["space_lg"], pady=(0, THEME["space_lg"]))

        def choose():
            selection = listbox.curselection()
            if selection:
                app.cat.set(listbox.get(selection[0]))
            win.destroy()

        tk.Button(actions, text="应用", command=choose, **_button_style_kwargs(accent=True)).pack(
            side="right", padx=(THEME["space_sm"], 0)
        )
        tk.Button(actions, text="关闭", command=win.destroy, **_button_style_kwargs()).pack(side="right")
        win.bind("<Escape>", lambda _e: win.destroy())
    except tk.TclError:
        try:
            win.destroy()
        except tk.TclError:
            pass


def organize_search_toolbar(app):
    """Reflow existing result actions; callbacks and result ordering stay intact."""
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
        toolbar.grid_rowconfigure(0, weight=0)
        toolbar.grid_rowconfigure(1, weight=0)
        title_group = next((c for c in children if c is not action_frame and _find_text(c, "搜索结果") is not None), None)
        if title_group is None:
            title_group = children[0]
        title_group.grid(row=0, column=0, rowspan=2, sticky="w", padx=(THEME["space_md"], THEME["space_lg"]), pady=THEME["space_sm"])
        action_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=THEME["space_sm"], pady=THEME["space_xs"])

        buttons = _button_children(action_frame)
        if len(buttons) < 7:
            return
        # Original construction order:
        # copy, CSV, Excel, one-click favorite, favorites, condition, history.
        ordered = [buttons[3], buttons[4], buttons[0], buttons[1], buttons[2], buttons[5], buttons[6]]
        groups = (ordered[0:2], ordered[2:5], ordered[5:7])
        column = 0
        for group_index, group in enumerate(groups):
            for index, button in enumerate(group):
                left_pad = 0 if index == 0 else 3
                if group_index and index == 0:
                    left_pad = THEME["space_md"]
                button.grid(
                    row=0,
                    column=column,
                    padx=(left_pad, 3),
                    pady=THEME["space_xs"],
                    sticky="ew",
                )
                column += 1
                try:
                    button.configure(pady=max(4, THEME["button_pad_y"] - 1))
                except tk.TclError:
                    pass
        toolbar.configure(background=THEME["surface"])
    except tk.TclError:
        return


def apply(app):
    _normalize_search_controls(app)
    organize_search_toolbar(app)
