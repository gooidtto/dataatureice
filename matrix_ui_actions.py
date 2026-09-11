"""Actions for independent per-result horizontal quote matrices."""
import csv
import tkinter as tk
from tkinter import filedialog
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

import phone_search
from search_display import DISPLAY_COLUMNS, display_columns_for_rows, normalize_search_results


def visible_matrix_rows(rows):
    return normalize_search_results(rows)


def matrix_columns(rows=None):
    return display_columns_for_rows(rows or []) if rows is not None else DISPLAY_COLUMNS


def matrix_headers(rows=None):
    return [label for _field, label, _width in matrix_columns(rows)]


def matrix_values(display_row, rows=None):
    columns = display_row.get("_columns") if display_row.get("_columns") else matrix_columns(rows)
    return [display_row.get(field, "") for field, _label, _width in columns]


def raw_rows_for_payloads(payloads):
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
    return selected or visible_matrix_rows(app.rows)


def _matrix_text(payloads, columns=None):
    lines = []
    for index, payload in enumerate(payloads):
        block_columns = payload.get("_columns") or columns or DISPLAY_COLUMNS
        if index:
            lines.append("")
            lines.append("")
        lines.append("\t".join(label for _field, label, _width in block_columns))
        lines.append("\t".join(str(payload.get(field, "")) for field, _label, _width in block_columns))
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
    app.root.clipboard_append(_matrix_text(payloads, getattr(app, "_matrix_columns", DISPLAY_COLUMNS)))
    app.root.update()
    app.status.config(text=f"已复制搜索结果 {len(payloads)} 个结果")
    return "break" if event else None


def copy_all(app):
    payloads = visible_matrix_rows(app.rows)
    if not payloads:
        return app.toast("当前没有搜索结果")
    app.root.clipboard_clear()
    app.root.clipboard_append(_matrix_text(payloads))
    app.root.update()
    app.status.config(text=f"已复制搜索结果 {len(payloads)} 个结果")


def _export_csv(app, payloads, path, columns=None):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        for index, payload in enumerate(payloads):
            block_columns = payload.get("_columns") or columns or DISPLAY_COLUMNS
            if index:
                writer.writerow([])
                writer.writerow([])
            writer.writerow([label for _field, label, _width in block_columns])
            writer.writerow([payload.get(field, "") for field, _label, _width in block_columns])


def _export_xlsx(app, payloads, path, columns=None):
    wb = Workbook()
    ws = wb.active
    ws.title = "搜索结果"
    row_index = 1
    for index, payload in enumerate(payloads):
        block_columns = payload.get("_columns") or columns or DISPLAY_COLUMNS
        if index:
            row_index += 2
        headers = [label for _field, label, _width in block_columns]
        for col, label in enumerate(headers, 1):
            cell = ws.cell(row_index, col, label)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        row_index += 1
        for col, (field, _label, _width) in enumerate(block_columns, 1):
            cell = ws.cell(row_index, col, payload.get(field, ""))
            cell.alignment = Alignment(horizontal="center", vertical="center")
        row_index += 1
    ws.freeze_panes = "A1"
    wb.save(path)


def export_csv(app):
    payloads = _payloads_or_all(app)
    if not payloads:
        return app.toast("当前没有搜索结果")
    path = filedialog.asksaveasfilename(parent=app.root, title="导出搜索结果 CSV", defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")], initialfile="数码价格搜索结果.csv")
    if not path:
        return
    _export_csv(app, payloads, path)
    app.status.config(text=f"已导出搜索结果 {len(payloads)} 个结果")


def export_xlsx(app):
    payloads = _payloads_or_all(app)
    if not payloads:
        return app.toast("当前没有搜索结果")
    path = filedialog.asksaveasfilename(parent=app.root, title="导出搜索结果 Excel", defaultextension=".xlsx", filetypes=[("Excel 文件", "*.xlsx")], initialfile="数码价格搜索结果.xlsx")
    if not path:
        return
    _export_xlsx(app, payloads, path)
    app.status.config(text=f"已导出搜索结果 {len(payloads)} 个结果")


def _add_raw_button(app):
    for widget in app.root.winfo_children():
        if not isinstance(widget, (tk.Frame, __import__("tkinter").ttk.Frame)):
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
        self._matrix_columns = DISPLAY_COLUMNS
        _add_raw_button(self)

    App.__init__ = init_with_matrix_actions
