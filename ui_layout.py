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

        # Put the two collection actions at the front of the central action
        # row. The remaining actions shift right once, keeping their relative
        # order and callbacks unchanged:
        # 一键收藏 | 展示收藏 | 复制全部 | 导出 CSV | 导出 Excel | 条件比价 | 历史对比
        ordered = [buttons[3], buttons[4], buttons[0], buttons[1], buttons[2], buttons[5], buttons[6]]

        # Visual groups now follow the new priority: favorites first, data
        # operations second, comparison utilities last.
        groups = [
            ordered[0:2],
            ordered[2:5],
            ordered[5:7],
        ]
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
    organize_search_toolbar(app)
