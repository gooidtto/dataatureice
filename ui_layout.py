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


def _normalize_search_controls(app):
    """Keep the input shell focused on input; controls live beside it.

    The search field and clear button remain one coherent search surface.
    Search/category controls are moved outside that surface and use the same
    compact button geometry as the rest of the application.
    """
    shell = getattr(app, "search_bar", None)
    entry = getattr(app, "entry", None)
    search_button = getattr(app, "search_button", None)
    clear_button = getattr(app, "clear_button", None)
    cat = getattr(app, "cat", None)
    if not all((shell, entry, search_button, clear_button, cat)):
        return

    try:
        # The history popup is anchored to the entry, so keeping the shell as
        # the full-width input surface preserves its existing behavior.
        search_button.pack_forget()
        cat.pack_forget()

        controls = getattr(app, "_search_controls", None)
        if controls is None or not controls.winfo_exists():
            controls = tk.Frame(shell.master, bg=THEME["window_bg"], bd=0, highlightthickness=0)
            app._search_controls = controls

        controls.pack_forget()
        controls.pack(fill="x", padx=THEME["space_lg"], pady=(0, THEME["space_sm"]))

        # Keep a stable left-to-right rhythm: search, category, manage.
        search_button.configure(
            text="搜索",
            font=FONT_BODY,
            bg=THEME["button_bg"],
            fg=THEME["button_accent_text"],
            activebackground=THEME["accent_soft"],
            activeforeground=THEME["accent"],
            relief="solid",
            bd=1,
            highlightthickness=0,
            padx=THEME["primary_pad_x"],
            pady=THEME["button_pad_y"],
            cursor="hand2",
        )
        cat.configure(width=10, font=FONT_BODY)

        for widget in (search_button, cat):
            try:
                widget.pack(side="left", padx=(0, THEME["space_sm"]), pady=0, ipadx=0)
            except tk.TclError:
                pass

        manage = getattr(app, "manage_category_button", None)
        if manage is None or not manage.winfo_exists():
            manage = tk.Button(
                controls,
                text="管理分类",
                command=lambda: _manage_categories(app),
                font=FONT_BODY,
                bg=THEME["button_bg"],
                fg=THEME["button_text"],
                activebackground=THEME["button_hover"],
                activeforeground=THEME["text"],
                relief="solid",
                bd=1,
                highlightthickness=0,
                padx=THEME["button_pad_x"],
                pady=THEME["button_pad_y"],
                cursor="hand2",
            )
            app.manage_category_button = manage
        manage.pack(side="left", padx=(0, THEME["space_sm"]), pady=0)

        # Make the three controls visually identical in height without using
        # fixed pixel dimensions, which remain stable across DPI/font scaling.
        for widget in (search_button, manage):
            try:
                widget.configure(pady=THEME["button_pad_y"])
            except tk.TclError:
                pass
    except tk.TclError:
        return


def _manage_categories(app):
    """Open a lightweight category manager without changing search behavior."""
    try:
        win = app._new_window("管理分类", "560x420", (460, 340))
    except Exception:
        return
    try:
        win.configure(background=THEME["window_bg"])
        body = tk.Frame(win, bg=THEME["surface"], bd=1, relief="solid", highlightthickness=1, highlightbackground=THEME["border_soft"])
        body.pack(fill="both", expand=True, padx=THEME["space_lg"], pady=THEME["space_lg"])
        tk.Label(body, text="分类筛选", bg=THEME["surface"], fg=THEME["text"], font=FONT_TITLE).pack(anchor="w", padx=THEME["space_lg"], pady=(THEME["space_lg"], 4))
        tk.Label(body, text="选择分类后，搜索框右侧的分类筛选会立即更新。", bg=THEME["surface"], fg=THEME["text_secondary"], font=FONT_BODY).pack(anchor="w", padx=THEME["space_lg"], pady=(0, THEME["space_md"]))

        values = list(app.cat.cget("values"))
        listbox = tk.Listbox(body, font=FONT_BODY, bg=THEME["surface"], fg=THEME["text"], selectbackground=THEME["selection"], selectforeground=THEME["text"], relief="solid", bd=1, highlightthickness=0, activestyle="none")
        listbox.pack(fill="both", expand=True, padx=THEME["space_lg"], pady=(0, THEME["space_md"]))
        for value in values:
            listbox.insert("end", value)
        current = app.cat.get()
        if current in values:
            listbox.selection_set(values.index(current))
            listbox.see(values.index(current))

        actions = tk.Frame(body, bg=THEME["surface"])
        actions.pack(fill="x", padx=THEME["space_lg"], pady=(0, THEME["space_lg"]))
        def choose():
            selection = listbox.curselection()
            if selection:
                app.cat.set(listbox.get(selection[0]))
            win.destroy()
        tk.Button(actions, text="应用", command=choose, font=FONT_BODY, bg=THEME["button_bg"], fg=THEME["button_accent_text"], activebackground=THEME["accent_soft"], activeforeground=THEME["accent"], relief="solid", bd=1, highlightthickness=0, padx=THEME["primary_pad_x"], pady=THEME["button_pad_y"], cursor="hand2").pack(side="right", padx=(THEME["space_sm"], 0))
        tk.Button(actions, text="关闭", command=win.destroy, font=FONT_BODY, bg=THEME["button_bg"], fg=THEME["button_text"], activebackground=THEME["button_hover"], activeforeground=THEME["text"], relief="solid", bd=1, highlightthickness=0, padx=THEME["button_pad_x"], pady=THEME["button_pad_y"], cursor="hand2").pack(side="right")
        win.bind("<Escape>", lambda _e: win.destroy())
    except tk.TclError:
        try:
            win.destroy()
        except tk.TclError:
            pass


def organize_search_toolbar(app):
    """Reflow the result actions into stable functional groups.

    The existing commands/widgets are reused, so this is layout-only: no
    search, favorite, export, or comparison behavior is changed.
    """
    root = app.root
    title = _find_text(root, "搜索结果")
    if title is None:
        return
    try:
        toolbar = title.master
        children = list(toolbar.winfo_children())
        left = title.master
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
        left.grid(row=0, column=0, rowspan=2, sticky="w", padx=(THEME["space_md"], THEME["space_lg"]), pady=THEME["space_sm"])
        action_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=THEME["space_sm"], pady=THEME["space_xs"])

        buttons = _button_children(action_frame)
        if len(buttons) < 7:
            return

        ordered = [buttons[3], buttons[4], buttons[0], buttons[1], buttons[2], buttons[5], buttons[6]]
        groups = [ordered[0:2], ordered[2:5], ordered[5:7]]
        column = 0
        for group_index, group in enumerate(groups):
            for index, button in enumerate(group):
                padx = (0 if index == 0 else 3, 3)
                if group_index and index == 0:
                    padx = (THEME["space_md"], 3)
                button.grid(row=0, column=column, padx=padx, pady=THEME["space_xs"], sticky="ew")
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
