"""Primary actions for the new horizontal search-result matrix.

The matrix is presentation-only. Canonical 19-field rows remain unchanged and
are retained behind each matrix row for the dedicated raw-price detail view.
"""
import csv
import tkinter as tk
from tkinter import filedialog
from openpyxl import Workbook
from openpyxl.styles import Font

import phone_search
from search_display import DISPLAY_COLUMNS, normalize_search_results


def visible_matrix_rows(rows):
    """Return display rows in the same order shown by the matrix UI."""
    return [row for row in normalize_search_results(rows) if not row.get("_separator")]


def matrix_headers():
    return [label for _field, label, _width in DISPLAY_COLUMNS]


def matrix_values(display_row):
    return [display_row.get(field, "") for field, _label, _width in DISPLAY_COLUMNS]


def raw_rows_for_payloads(payloads):
    """Flatten the source rows behind matrix payloads without content duplication."""
    out = []
    seen = set()
    for payload in payloads:
        for row in payload.get("_rows", []):
            key = phone_search.generateContentKey(row)
            if key in seen:
                continue
            seen.add(key)
            out.append(row)
    return out


def selected_payloads(app):
    selected = []
    matrix_map = getattr(app, "_matrix_map", {})
    for iid in app.tree.selection():
        payload = matrix_map.get(iid)
        if payload and not payload.get("_separator"):
            selected.append(payload)
    return selected


def _payloads_or_all(app):
    selected = selected_payloads(app)
    if selected:
        return selected
    return visible_matrix_rows(app.rows)


def _matrix_text(payloads):
    lines = ["\t".join(matrix_headers())]
    last_identity = None
    for payload in payloads:
        identity = payload.get("identity", "")
        if last_identity is not None and identity != last_identity:
            lines.append("\t" * (len(DISPLAY_COLUMNS) - 1))
        lines.append("\t".join(str(v) for v in matrix_values(payload)))
        last_identity = identity
    return "\r\n".join(lines)


def add_favorite(app):
    payloads = _payloads_or_all(app)
    if not payloads:
        return app.toast("当前没有搜索结果")
    raw_rows = raw_rows_for_payloads(payloads)
    return app.addToFavorites(raw_rows)


def copy_selected(app, event=None):
    payloads = selected_payloads(app)
    if not payloads:
        app.toast("请先选择搜索结果")
        return "break" if event else None
    app.root.clipboard_clear()
    app.root.clipboard_append(_matrix_text(payloads))
    app.root.update()
    app.status.config(text=f"已复制搜索结果 {len(payloads)} 行")
    return "break" if event else None


def copy_all(app):
    payloads = visible_matrix_rows(app.rows)
    if not payloads:
        return app.toast("当前没有搜索结果")
    app.root.clipboard_clear()
    app.root.clipboard_append(_matrix_text(payloads))
    app.root.update()
    app.status.config(text=f"已复制搜索结果 {len(payloads)} 行")


def _export_csv(app, payloads, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(matrix_headers())
        last_identity = None
        for payload in payloads:
            identity = payload.get("identity", "")
            if last_identity is not None and identity != last_identity:
                writer.writerow([""] * len(DISPLAY_COLUMNS))
            writer.writerow(matrix_values(payload))
            last_identity = identity


def _export_xlsx(app, payloads, path):
    wb = Workbook()
    ws = wb.active
    ws.title = "搜索结果"
    headers = matrix_headers()
    for col, label in enumerate(headers, 1):
        cell = ws.cell(1, col, label)
        cell.font = Font(bold=True)
    row_index = 2
    last_identity = None
    for payload in payloads:
        identity = payload.get("identity", "")
        if last_identity is not None and identity != last_identity:
            row_index += 1
        for col, value in enumerate(matrix_values(payload), 1):
            ws.cell(row_index, col, value)
        row_index += 1
        last_identity = identity
    ws.freeze_panes = "A2"
    for col in range(1, len(headers) + 1):
        values = [len(str(ws.cell(r, col).value or "")) for r in range(1, ws.max_row + 1)]
        ws.column_dimensions[chr(64 + col) if col <= 26 else f"{chr(64 + (col - 1) // 26)}{chr(65 + (col - 1) % 26)}"].width = min(48, max(12, max(values, default=12) + 2))
    wb.save(path)


def export_csv(app):
    payloads = _payloads_or_all(app)
    if not payloads:
        return app.toast("当前没有搜索结果")
    path = filedialog.asksaveasfilename(
        parent=app.root,
        title="导出搜索结果 CSV",
        defaultextension=".csv",
        filetypes=[("CSV 文件", "*.csv")],
        initialfile="数码价格搜索结果.csv",
    )
    if not path:
        return
    _export_csv(app, payloads, path)
    app.status.config(text=f"已导出搜索结果 {len(payloads)} 行")


def export_xlsx(app):
    payloads = _payloads_or_all(app)
    if not payloads:
        return app.toast("当前没有搜索结果")
    path = filedialog.asksaveasfilename(
        parent=app.root,
        title="导出搜索结果 Excel",
        defaultextension=".xlsx",
        filetypes=[("Excel 文件", "*.xlsx")],
        initialfile="数码价格搜索结果.xlsx",
    )
    if not path:
        return
    _export_xlsx(app, payloads, path)
    app.status.config(text=f"已导出搜索结果 {len(payloads)} 行")


def _add_raw_button(app):
    """Add one dedicated legacy/raw-price button to the existing action bar."""
    for widget in app.root.winfo_children():
        if not isinstance(widget, tk.Frame) and not isinstance(widget, __import__("tkinter").ttk.Frame):
            continue
        buttons = [child for child in widget.winfo_children() if hasattr(child, "cget")]
        if any(str(child.cget("text")) == "🧾原始价格" for child in buttons):
            return
        if any(str(child.cget("text")) == "☆ 一键收藏" for child in buttons):
            __import__("tkinter").ttk.Button(widget, text="🧾原始价格", command=app.detail).pack(side="left", padx=4)
            return


def install(App):
    if getattr(App, "_matrix_actions_installed", False):
        return
    App._matrix_actions_installed = True
    App.add_favorite = add_favorite
    App.copy = copy_selected
    App.copy_all = copy_all
    App.export_csv = export_csv
    App.export_xlsx = export_xlsx
    original_init = App.__init__

    def init_with_matrix_actions(self, root):
        original_init(self, root)
        _add_raw_button(self)

    App.__init__ = init_with_matrix_actions
