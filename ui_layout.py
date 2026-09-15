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
    """Keep search input separate from one compact, independent category selector."""
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

        old_search.pack_forget()
        old_cat.pack_forget()
        old_search.destroy()
        old_cat.destroy()

        # The search surface contains only the input and clear affordance.
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
        search_button.pack(side="left", padx=(0, THEME["space_md"]))

        # Keep category as the only category control in the main toolbar.
        category_group = tk.Frame(
            controls,
            bg=THEME["window_bg"],
            bd=0,
            highlightthickness=0,
        )
        category_group.pack(side="left", fill="y")

        tk.Label(
            category_group,
            text="分类",
            bg=THEME["window_bg"],
            fg=THEME["text_secondary"],
            font=FONT_BODY,
        ).pack(side="left", padx=(0, THEME["space_xs"]))

        combo_style = "Search.Category.TCombobox"
        style = ttk.Style(root)
        style.configure(
            combo_style,
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
            combo_style,
            fieldbackground=[("readonly", THEME["button_bg"]), ("active", THEME["button_hover"])],
            background=[("readonly", THEME["button_bg"]), ("active", THEME["button_hover"])],
            foreground=[("readonly", THEME["button_text"])],
        )
        category_var = tk.StringVar(value="全部")
        cat = ttk.Combobox(
            category_group,
            textvariable=category_var,
            values=["全部", "手机", "平板", "电脑", "其它", "手机配件"],
            state="readonly",
            width=7,
            style=combo_style,
        )
        cat.set("全部")
        cat.pack(side="left")

        app.search_button = search_button
        app.cat = cat
        app._category_var = category_var
        app.clear_button = clear
        app.manage_category_button = None
    except tk.TclError:
        return


def _manage_categories(app):
    """Legacy compatibility entry point; category selection now lives in the toolbar."""
    return None


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
