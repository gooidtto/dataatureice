"""Favorites window rendered with the same matrix surface as search results."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from search_display import build_result_blocks, sort_rows

_MODEL_PALETTE = ("#eef7ff", "#f5efff", "#eefaf2", "#fff7e8", "#f3f3f3")


def show_favorites_matrix(self):
    rows = list(self.fav.dedupe())
    w = self._new_window("⭐ 我的收藏", "1650x760", (1150, 560))
    ttk.Label(
        w,
        text=f"我的收藏 · {len(rows)} 条 · 与搜索结果保持同版式",
        font=("微软雅黑", 12, "bold"),
    ).pack(anchor="w", padx=12, pady=10)

    host = ttk.Frame(w, padding=(12, 0, 12, 10))
    host.pack(fill="both", expand=True)
    canvas = tk.Canvas(host, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    host.grid_rowconfigure(0, weight=1)
    host.grid_columnconfigure(0, weight=1)
    inner = tk.Frame(canvas, bd=0, highlightthickness=0)
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))

    blocks = build_result_blocks(sort_rows(rows))
    mapping = {}
    trees = []
    for index, block in enumerate(blocks):
        if index:
            spacer = tk.Frame(inner, height=8)
            spacer.pack(fill="x")

        columns = tuple(block.get("_columns") or ())
        fields = [c[0] for c in columns] + ["favorite"]
        frame = tk.Frame(inner, bd=0, highlightthickness=0)
        tree = ttk.Treeview(frame, columns=fields, show="headings", height=1, selectmode="browse")
        for field, title, width in columns:
            tree.heading(field, text=title)
            tree.column(
                field,
                width=width,
                minwidth=max(60, min(width, 90)),
                anchor="center" if field == "data_date" else "w",
                stretch=False,
            )
        tree.heading("favorite", text="收藏")
        tree.column("favorite", width=110, minwidth=90, anchor="center", stretch=False)

        iid = f"favorite-{index}"
        tree.insert(
            "",
            "end",
            iid=iid,
            values=[block.get(field, "") for field, _, _ in columns] + ["★ 已收藏"],
            tags=(f"m{block['_model_index']}",),
        )
        tree.tag_configure(
            f"m{block['_model_index']}",
            background=_MODEL_PALETTE[block["_model_index"] % len(_MODEL_PALETTE)],
        )
        tree.bind("<Double-1>", lambda _e, b=block: self.detail_rows(b.get("_rows", [])))
        tree.bind("<Button-3>", lambda e, b=block: _favorite_menu(self, e, tree, b, w))
        tree.pack(fill="x", expand=True)
        frame.pack(fill="x", expand=True, pady=(0, 2))
        trees.append(tree)
        mapping[iid] = block

    def selected_blocks():
        selected = []
        for tree in trees:
            for iid in tree.selection():
                block = mapping.get(iid)
                if block:
                    selected.append(block)
        return selected

    def selected_rows():
        blocks_selected = selected_blocks()
        return [r for block in blocks_selected for r in block.get("_rows", [])]

    def all_rows():
        return [r for block in blocks for r in block.get("_rows", [])]

    def remove_selected():
        picked = selected_rows()
        if not picked:
            from tkinter import messagebox
            return messagebox.showinfo("我的收藏", "请先选择要移除的收藏", parent=w)
        self.fav.remove(picked)
        w.destroy()
        self.show_favorites()
        self.status.config(text=f"已移除收藏 {len(picked)} 条")

    bar = ttk.Frame(w, padding=(12, 0, 12, 10))
    bar.pack(fill="x")
    ttk.Button(bar, text="查看详情", command=lambda: self.detail_rows(selected_rows() or all_rows())).pack(side="left", padx=4)
    ttk.Button(bar, text="移除收藏", command=remove_selected).pack(side="left", padx=4)
    ttk.Button(bar, text="复制", command=lambda: self.copy_popup(selected_rows() or all_rows())).pack(side="left", padx=4)
    ttk.Button(bar, text="导出CSV", command=lambda: self.export_popup(selected_rows() or all_rows(), False)).pack(side="left", padx=4)
    ttk.Button(bar, text="导出Excel", command=lambda: self.export_popup(selected_rows() or all_rows(), True)).pack(side="left", padx=4)
    ttk.Button(bar, text="关闭", command=w.destroy).pack(side="right", padx=4)
    w.bind("<Escape>", lambda _e: w.destroy())
    return w


def _favorite_menu(self, event, tree, block, window):
    iid = tree.identify_row(event.y)
    if not iid:
        return
    tree.selection_set(iid)
    rows = list(block.get("_rows", []))
    menu = tk.Menu(tree, tearoff=False)
    menu.add_command(label="查看详情", command=lambda: self.detail_rows(rows))
    menu.add_command(label="移除收藏", command=lambda: _remove_block(self, window, rows))
    menu.add_command(label="复制", command=lambda: self.copy_popup(rows))
    menu.tk_popup(event.x_root, event.y_root)


def _remove_block(self, window, rows):
    if not rows:
        return
    self.fav.remove(rows)
    window.destroy()
    self.show_favorites()
    self.status.config(text=f"已移除收藏 {len(rows)} 条")
