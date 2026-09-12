"""Actions for the unified dynamic search-result matrix."""
import csv
import tkinter as tk
from tkinter import filedialog
from openpyxl import Workbook
from openpyxl.styles import Font

import phone_search
from search_display import build_display_columns, normalize_search_results
from value_order import sort_rows


def _columns(rows):
    return build_display_columns(rows)


def visible_matrix_rows(rows):
    """Return display rows in exactly the order shown by the matrix UI."""
    return [row for row in normalize_search_results(sort_rows(rows)) if not row.get("_separator")]


def matrix_headers(rows):
    return [label for _field, label, _width in _columns(rows)]


def matrix_values(display_row, columns):
    return [display_row.get(field, "") for field, _label, _width in columns]


def raw_rows_for_payloads(payloads):
    """Flatten source rows without content duplication."""
    out = []
    seen = set()
    for payload in payloads:
        for row in payload.get("_rows", []):
            key = phone_search.generateContentKey(row)
            if key in seen: continue
            seen.add(key); out.append(row)
    return sort_rows(out)


def selected_payloads(app):
    selected = []
    matrix_map = getattr(app, "_matrix_map", {})
    for iid in app.tree.selection():
        payload = matrix_map.get(iid)
        if payload and not payload.get("_separator"): selected.append(payload)
    # Selection order is not presentation order.
    return sorted(selected, key=lambda p: (p.get("_model_index", 0), p.get("_period_index", 0)))


def _payloads_or_all(app):
    selected = selected_payloads(app)
    if selected: return selected
    return visible_matrix_rows(app.rows)


def _matrix_text(payloads, columns):
    lines = ["\t".join(matrix_headers([r for p in payloads for r in p.get("_rows", [])]))]
    last_model = last_date = None
    for payload in payloads:
        model = payload.get("_model_key")
        date = payload.get("_period_key")
        if last_model is not None and model != last_model: lines.extend(["\t" * (len(columns) - 1)] * 2)
        elif last_date is not None and date != last_date: lines.append("\t" * (len(columns) - 1))
        lines.append("\t".join(str(v) for v in matrix_values(payload, columns)))
        last_model, last_date = model, date
    return "\r\n".join(lines)


def add_favorite(app):
    payloads = _payloads_or_all(app)
    if not payloads: return app.toast("当前没有搜索结果")
    return app.addToFavorites(raw_rows_for_payloads(payloads))


def copy_selected(app, event=None):
    payloads = selected_payloads(app)
    if not payloads:
        app.toast("请先选择搜索结果"); return "break" if event else None
    raw = [r for p in payloads for r in p.get("_rows", [])]
    columns = _columns(raw)
    app.root.clipboard_clear(); app.root.clipboard_append(_matrix_text(payloads, columns)); app.root.update()
    app.status.config(text=f"已复制搜索结果 {len(payloads)} 个结果块")
    return "break" if event else None


def copy_all(app):
    payloads = visible_matrix_rows(app.rows)
    if not payloads: return app.toast("当前没有搜索结果")
    columns = _columns(app.rows)
    app.root.clipboard_clear(); app.root.clipboard_append(_matrix_text(payloads, columns)); app.root.update()
    app.status.config(text=f"已复制搜索结果 {len(payloads)} 个结果块")


def _export_csv(app, payloads, path):
    raw = [r for p in payloads for r in p.get("_rows", [])]
    columns = _columns(raw)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f); writer.writerow(matrix_headers(raw))
        last_model = last_date = None
        for payload in payloads:
            model = payload.get("_model_key"); date = payload.get("_period_key")
            if last_model is not None and model != last_model: writer.writerow([""] * len(columns)); writer.writerow([""] * len(columns))
            elif last_date is not None and date != last_date: writer.writerow([""] * len(columns))
            writer.writerow(matrix_values(payload, columns)); last_model, last_date = model, date


def _export_xlsx(app, payloads, path):
    raw = [r for p in payloads for r in p.get("_rows", [])]
    columns = _columns(raw); headers = matrix_headers(raw)
    wb = Workbook(); ws = wb.active; ws.title = "搜索结果"
    for col, label in enumerate(headers, 1): ws.cell(1, col, label).font = Font(bold=True)
    row_index = 2; last_model = last_date = None
    for payload in payloads:
        model = payload.get("_model_key"); date = payload.get("_period_key")
        if last_model is not None and model != last_model: row_index += 2
        elif last_date is not None and date != last_date: row_index += 1
        for col, value in enumerate(matrix_values(payload, columns), 1): ws.cell(row_index, col, value)
        row_index += 1; last_model, last_date = model, date
    ws.freeze_panes = "A2"
    for col, (_field, title, width) in enumerate(columns, 1): ws.column_dimensions[ws.cell(1, col).column_letter].width = max(10, min(60, width / 8))
    wb.save(path)


def export_csv(app):
    payloads = _payloads_or_all(app)
    if not payloads: return app.toast("当前没有搜索结果")
    path = filedialog.asksaveasfilename(parent=app.root, title="导出搜索结果 CSV", defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")], initialfile="数码价格搜索结果.csv")
    if not path: return
    _export_csv(app, payloads, path); app.status.config(text=f"已导出搜索结果 {len(payloads)} 个结果块")


def export_xlsx(app):
    payloads = _payloads_or_all(app)
    if not payloads: return app.toast("当前没有搜索结果")
    path = filedialog.asksaveasfilename(parent=app.root, title="导出搜索结果 Excel", defaultextension=".xlsx", filetypes=[("Excel 文件", "*.xlsx")], initialfile="数码价格搜索结果.xlsx")
    if not path: return
    _export_xlsx(app, payloads, path); app.status.config(text=f"已导出搜索结果 {len(payloads)} 个结果块")


def _add_raw_button(app):
    for widget in app.root.winfo_children():
        if not isinstance(widget, (tk.Frame, __import__("tkinter").ttk.Frame)): continue
        buttons = [child for child in widget.winfo_children() if hasattr(child, "cget")]
        if any(str(child.cget("text")) == "🧾原始价格" for child in buttons): return
        if any(str(child.cget("text")) == "☆ 一键收藏" for child in buttons):
            __import__("tkinter").ttk.Button(widget, text="🧾原始价格", command=app.detail).pack(side="left", padx=4); return


def install(App):
    if getattr(App, "_matrix_actions_installed", False): return
    App._matrix_actions_installed = True
    App.add_favorite = add_favorite; App.copy = copy_selected; App.copy_all = copy_all; App.export_csv = export_csv; App.export_xlsx = export_xlsx
    original_init = App.__init__
    def init_with_matrix_actions(self, root): original_init(self, root); _add_raw_button(self)
    App.__init__ = init_with_matrix_actions
