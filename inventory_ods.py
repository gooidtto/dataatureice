import re
from copy import deepcopy
from odf.opendocument import load, OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P
from odf import teletype

MODEL_ALIASES = ["型号", "机型", "机型及配置", "机型与配置", "机型与规格", "品名/型号", "产品型号", "规格型号"]
BRAND_ALIASES = ["品牌", "品牌名称", "厂商", "品牌/系列", "品牌系列"]
SERIES_ALIASES = ["系列", "产品系列", "型号系列", "品牌/系列"]
QUANTITY_ALIASES = ["数量", "数量(台)", "数量（台）", "件数", "库存", "库存数量", "台数", "个数", "件", "台", "qty", "quantity"]
PRICE_FIELDS = [("p1", "靓好"), ("p2", "好碎"), ("p3", "碎屏"), ("p4", "压屏"), ("p5", "不开机"), ("p6", "废板")]


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").replace("\ufeff", "").replace("\u200b", "").strip())


def key(value):
    return re.sub(r"[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+", "", clean(value).casefold())


def cell_text(cell):
    return clean(teletype.extractText(cell))


def row_values(row):
    values = []
    for node in row.childNodes:
        if getattr(node, "qname", None) and node.qname[1] == "table-cell":
            repeat = int(node.getAttribute("numbercolumnsrepeated") or 1)
            values.extend([cell_text(node)] * repeat)
    while values and values[-1] == "":
        values.pop()
    return values


def parse_number(value):
    s = re.sub(r"[^0-9.+-]", "", clean(value))
    if not s or s in {"+", "-", "."}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def find_col(headers, aliases):
    normalized = {key(h): i for i, h in enumerate(headers) if clean(h)}
    for alias in aliases:
        if key(alias) in normalized:
            return normalized[key(alias)]
    for i, h in enumerate(headers):
        kh = key(h)
        if any(key(a) in kh or kh in key(a) for a in aliases):
            return i
    return None


def stage_label(name):
    m = re.search(r"(\d{3,})$", str(name))
    return m.group(1) if m else ("当前" if str(name) == "当前数据" else str(name))


def stage_sort_key(name):
    m = re.search(r"(\d{3,})$", str(name))
    return (0, int(m.group(1))) if m else (1, str(name))


def build_price_maps(datasets):
    result = {}
    for dataset_name, rows in datasets.items():
        mapping = {}
        for d in rows:
            brand, series, model = key(d.get("source")), key(d.get("series")), key(d.get("model"))
            if not model:
                continue
            mapping[(brand, series, model)] = d
            mapping.setdefault((brand, "", model), d)
            mapping.setdefault(("", "", model), d)
        result[dataset_name] = mapping
    return result


def find_match(brand, series, model, price_maps):
    kb, ks, km = key(brand), key(series), key(model)
    for dataset_name, mapping in price_maps.items():
        d = (mapping.get((kb, ks, km)) or
             mapping.get((kb, "", km)) or
             mapping.get(("", "", km)))
        if d:
            yield dataset_name, d


def add_cell(row, value):
    cell = TableCell(valuetype="string")
    cell.addElement(P(text=clean(value)))
    row.addElement(cell)


def format_number(value):
    return "-" if value is None else f"{value:g}"


def format_price(value):
    n = parse_number(value)
    return "未找到价格" if n is None else f"{format_number(n)} 元"


def inventory_quantity(value):
    n = parse_number(value)
    return n if n is not None and n >= 0 else None


def import_ods_with_prices(input_path, output_path, datasets, price_condition="靓好"):
    """
    读取库存 ODS，在原表右侧追加价格参考、数量识别、多阶段单价/估值、涨跌额和估值变化。
    默认按“靓好”价格估值；保留原有三参数调用方式。
    """
    doc = load(input_path)
    price_maps = build_price_maps(datasets)
    stage_names = sorted(price_maps.keys(), key=stage_sort_key)
    stage_labels = [stage_label(s) for s in stage_names]
    out = OpenDocumentSpreadsheet()
    matched = unmatched = quantity_found = 0
    overall_totals = {s: 0.0 for s in stage_names}
    overall_counts = {s: 0 for s in stage_names}
    first_stage = stage_names[0] if stage_names else None
    last_stage = stage_names[-1] if stage_names else None

    for src_table in doc.spreadsheet.getElementsByType(Table):
        # Clone the whole table first: this keeps table attributes, column definitions and other
        # structure better than rebuilding the table from scratch.
        out_table = deepcopy(src_table)
        for node in list(out_table.childNodes):
            if getattr(node, "qname", None) and node.qname[1] == "table-row":
                out_table.removeChild(node)
        out.spreadsheet.addElement(out_table)

        src_rows = src_table.getElementsByType(TableRow)
        header_index = None
        header = []
        model_col = brand_col = series_col = qty_col = None
        for idx, row in enumerate(src_rows):
            vals = row_values(row)
            if not vals:
                continue
            mc = find_col(vals, MODEL_ALIASES)
            if mc is not None:
                header_index = idx
                header = vals
                model_col = mc
                brand_col = find_col(vals, BRAND_ALIASES)
                series_col = find_col(vals, SERIES_ALIASES)
                qty_col = find_col(vals, QUANTITY_ALIASES)
                break

        extra_headers = ["价格参考", "数量识别", "估值口径"]
        for label in stage_labels:
            extra_headers.extend([f"{label}单价", f"{label}估值"])
        extra_headers.extend(["涨跌额", "估值变化"])
        table_totals = {s: 0.0 for s in stage_names}

        for idx, src_row in enumerate(src_rows):
            vals = row_values(src_row)
            if header_index is None or idx < header_index:
                out_table.addElement(deepcopy(src_row))
                continue
            if idx == header_index:
                new_row = deepcopy(src_row)
                for h in extra_headers:
                    add_cell(new_row, h)
                out_table.addElement(new_row)
                continue

            new_row = deepcopy(src_row)
            brand = vals[brand_col] if brand_col is not None and len(vals) > brand_col else ""
            series = vals[series_col] if series_col is not None and len(vals) > series_col else ""
            model = vals[model_col] if model_col is not None and len(vals) > model_col else ""
            qty_raw = vals[qty_col] if qty_col is not None and len(vals) > qty_col else ""
            qty = inventory_quantity(qty_raw)
            if qty is not None:
                quantity_found += 1

            matches = dict(find_match(brand, series, model, price_maps)) if model else {}
            if matches:
                matched += 1
            elif model:
                unmatched += 1

            refs = []
            stage_prices = {}
            for stage in stage_names:
                d = matches.get(stage)
                if d:
                    parts = [f"{label}{format_price(d.get(field))}" for field, label in PRICE_FIELDS if parse_number(d.get(field)) is not None]
                    if parts:
                        refs.append(f"{stage_label(stage)}: " + " / ".join(parts))
                    stage_prices[stage] = next((parse_number(d.get(field)) for field, label in PRICE_FIELDS if label == price_condition and parse_number(d.get(field)) is not None), None)
                else:
                    stage_prices[stage] = None

            add_cell(new_row, "\n".join(refs) if refs else "未找到价格")
            add_cell(new_row, format_number(qty) if qty is not None else "未识别")
            add_cell(new_row, price_condition)

            valuations = {}
            for stage in stage_names:
                unit = stage_prices.get(stage)
                valuation = unit * qty if unit is not None and qty is not None else None
                valuations[stage] = valuation
                if valuation is not None:
                    table_totals[stage] += valuation
                    overall_totals[stage] += valuation
                    overall_counts[stage] += 1
                add_cell(new_row, format_number(unit) if unit is not None else "-")
                add_cell(new_row, format_number(valuation) if valuation is not None else "-")

            if first_stage and last_stage and first_stage != last_stage:
                first_unit, last_unit = stage_prices.get(first_stage), stage_prices.get(last_stage)
                first_val, last_val = valuations.get(first_stage), valuations.get(last_stage)
                unit_diff = None if first_unit is None or last_unit is None else last_unit - first_unit
                value_diff = None if first_val is None or last_val is None else last_val - first_val
            else:
                unit_diff = value_diff = None
            add_cell(new_row, (f"+{format_number(unit_diff)}" if unit_diff is not None and unit_diff > 0 else format_number(unit_diff)) if unit_diff is not None else "-")
            add_cell(new_row, (f"+{format_number(value_diff)}" if value_diff is not None and value_diff > 0 else format_number(value_diff)) if value_diff is not None else "-")
            out_table.addElement(new_row)

        if header_index is not None and stage_names:
            summary = TableRow()
            for _ in header:
                add_cell(summary, "")
            add_cell(summary, "阶段总估值")
            add_cell(summary, "")
            add_cell(summary, price_condition)
            for stage in stage_names:
                add_cell(summary, "")
                add_cell(summary, format_number(table_totals[stage]))
            if first_stage and last_stage and first_stage != last_stage:
                diff = table_totals[last_stage] - table_totals[first_stage]
                add_cell(summary, "-")
                add_cell(summary, f"+{format_number(diff)}" if diff > 0 else format_number(diff))
            else:
                add_cell(summary, "-")
                add_cell(summary, "-")
            out_table.addElement(summary)

    out.save(output_path)
    return {
        "matched": matched,
        "unmatched": unmatched,
        "quantity_found": quantity_found,
        "stages": stage_names,
        "stage_labels": stage_labels,
        "price_condition": price_condition,
        "stage_totals": {stage_label(k): v for k, v in overall_totals.items()},
        "stage_rows": {stage_label(k): v for k, v in overall_counts.items()},
    }
