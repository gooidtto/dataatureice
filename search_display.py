"""Canonical search-result model and presentation helpers."""
import csv
import re
import unicodedata
from pathlib import Path
from typing import TypedDict

from value_order import value_rank

FIXED_COLUMNS = (("data_date", "数据日期"), ("identity", "手机/品牌/系列/型号/网络型号"))
IDENTITY_FIELDS = ("category", "brand", "series", "model", "model_code")
SOURCE_COLUMN = ("source_image", "来源图片")


class ResultBlock(TypedDict):
    data_date: str
    identity: str
    source_image: str
    _rows: list
    _model_key: tuple
    _period_key: str
    _model_index: int
    _period_index: int
    _columns: tuple


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def build_identity(row):
    return " ".join(clean(row.get(field, "")) for field in IDENTITY_FIELDS if clean(row.get(field, "")))


def identity_key(row):
    return tuple(clean(row.get(field, "")) for field in IDENTITY_FIELDS)


def _condition_key(value):
    return clean(value).replace(" ", "")


def _condition_sort_key(row):
    return tuple(-x for x in value_rank(row)) + (clean(row.get("condition", "")),)


def _char_width(text):
    return sum(2 if unicodedata.east_asian_width(ch) in {"W", "F"} else 1 for ch in clean(text))


def column_width(title, values=(), minimum=90, maximum=420):
    occupied = max([_char_width(title)] + [_char_width(v) for v in values])
    return max(minimum, min(maximum, occupied * 9 + 22))


def group_model_dates(rows):
    """Group rows without changing the relative order supplied by search/favorites."""
    grouped = {}
    model_order = []
    date_order = {}
    for row in list(rows or []):
        key = identity_key(row)
        date = clean(row.get("data_date", ""))
        if key not in grouped:
            grouped[key] = {}
            model_order.append(key)
            date_order[key] = []
        if date not in grouped[key]:
            grouped[key][date] = []
            date_order[key].append(date)
        grouped[key][date].append(row)
    return [(key, [grouped[key][date] for date in date_order[key]]) for key in model_order]


def build_display_columns(rows):
    """Create columns from the supplied rows."""
    rows = list(rows or [])
    reps = {}
    condition_order = []
    for row in rows:
        condition = clean(row.get("condition", ""))
        if condition and _condition_key(condition) not in reps:
            reps[_condition_key(condition)] = row
            condition_order.append(_condition_key(condition))
    ordered = [reps[k] for k in condition_order]
    columns = [(field, title, 0) for field, title in FIXED_COLUMNS]
    for i, row in enumerate(ordered):
        columns.append((f"condition_{i}", clean(row.get("condition", "")), 0))
    columns.append(SOURCE_COLUMN + (0,))

    values = {field: [] for field, _title, _width in columns}
    for row in rows:
        values["data_date"].append(clean(row.get("data_date", "")))
        values["identity"].append(build_identity(row))
        values["source_image"].append(clean(row.get("source_image", "")))
        for field, title, _width in columns[2:-1]:
            if _condition_key(row.get("condition", "")) == _condition_key(title):
                values[field].append(clean(row.get("price", "")))
    return tuple((field, title, column_width(title, values.get(field, ()))) for field, title, _ in columns)


def build_result_columns(rows):
    return build_display_columns(rows)


def _build_block(model_index, period_index, block_rows):
    """Build a block while preserving row order exactly as supplied."""
    block_rows = list(block_rows or [])
    columns = build_result_columns(block_rows)
    condition_values = {}
    source_images = []
    for row in block_rows:
        condition = clean(row.get("condition", ""))
        price = clean(row.get("price", ""))
        key = _condition_key(condition)
        if key and price:
            condition_values.setdefault(key, []).append(price)
        image = clean(row.get("source_image", ""))
        if image and image not in source_images:
            source_images.append(image)
    first = block_rows[0] if block_rows else {}
    out = {
        "data_date": clean(first.get("data_date", "")),
        "identity": build_identity(first),
        "source_image": " / ".join(source_images),
        "_rows": block_rows,
        "_model_key": identity_key(first) if first else (),
        "_period_key": clean(first.get("data_date", "")),
        "_model_index": model_index,
        "_period_index": period_index,
        "_columns": columns,
    }
    for field, title, _width in columns[2:-1]:
        out[field] = " / ".join(condition_values.get(_condition_key(title), []))
    return out


def build_result_blocks(rows):
    """Return ResultBlocks in the exact first-seen model/date order of supplied rows."""
    blocks = []
    for model_index, (_key, periods) in enumerate(group_model_dates(rows)):
        for period_index, group in enumerate(periods):
            blocks.append(_build_block(model_index, period_index, group))
    for display_index, block in enumerate(blocks):
        block["_display_index"] = display_index
    return blocks


def normalize_search_results(rows):
    """Add visual separators without changing ResultBlock order."""
    blocks = build_result_blocks(rows)
    result = []
    for index, block in enumerate(blocks):
        if index and block["_model_index"] == blocks[index - 1]["_model_index"]:
            result.append({"_separator": "period", "_model_index": block["_model_index"], "_period_index": block["_period_index"]})
        elif index:
            result.extend((
                {"_separator": "model", "_model_index": blocks[index - 1]["_model_index"]},
                {"_separator": "model", "_model_index": blocks[index - 1]["_model_index"]},
            ))
        result.append(block)
    return result


def grouped_row_blocks(rows):
    """Return exportable blocks in first-seen model/date order, with no independent sorting."""
    return build_result_blocks(list(rows or []))


def grouped_text(rows, columns=None):
    """Create clipboard text using the same model/date spacing as the UI."""
    rows = list(rows or [])
    if not rows:
        return ""
    columns = tuple(columns or ((field, title, 0) for field, title, _ in build_display_columns(rows)))
    blocks = grouped_row_blocks(rows)
    headers = [title for _field, title, _width in columns]
    lines = ["\t".join(headers)]
    previous_model = previous_date = None
    for block in blocks:
        model = block.get("_model_key")
        date = block.get("_period_key")
        if previous_model is not None and model != previous_model:
            lines.extend(["\t" * (len(columns) - 1)] * 2)
        elif previous_date is not None and date != previous_date:
            lines.append("\t" * (len(columns) - 1))
        values = [block.get(field, "") for field, _title, _width in columns]
        lines.append("\t".join(str(value) for value in values))
        previous_model, previous_date = model, date
    return "\r\n".join(lines)


def grouped_csv_rows(rows, columns=None):
    """Yield CSV rows with blank-row spacing identical to the display rules."""
    rows = list(rows or [])
    if not rows:
        return []
    columns = tuple(columns or ((field, title, 0) for field, title, _ in build_display_columns(rows)))
    output = [[title for _field, title, _width in columns]]
    previous_model = previous_date = None
    for block in grouped_row_blocks(rows):
        model = block.get("_model_key")
        date = block.get("_period_key")
        if previous_model is not None and model != previous_model:
            output.extend([[""] * len(columns), [""] * len(columns)])
        elif previous_date is not None and date != previous_date:
            output.append([""] * len(columns))
        output.append([block.get(field, "") for field, _title, _width in columns])
        previous_model, previous_date = model, date
    return output


def grouped_excel_rows(rows, columns=None):
    """Yield Excel rows with blank rows matching grouped_csv_rows()."""
    return grouped_csv_rows(rows, columns=columns)


DISPLAY_COLUMNS = (("data_date", "数据日期", 105), ("identity", "手机/品牌/系列/型号/网络型号", 420), ("condition_0", "开机靓机/靓机/开机好屏", 145), ("condition_1", "开机好屏/内屏碎", 145), ("condition_2", "开机好碎", 145), ("condition_3", "开机碎屏", 145), ("condition_4", "不开机/开机坏配件", 145), ("condition_5", "废板·整机", 145), ("source_image", "来源图片", 150))
