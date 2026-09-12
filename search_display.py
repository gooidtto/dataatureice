"""Unified search-result presentation.

The source rows remain authoritative.  The matrix is generated from the rows
returned by each search: fixed identity columns are followed by the actual
price-condition names found in that result, then source image.  Nothing is
silently discarded when several source rows share one condition/date.
"""
import re
import unicodedata
from value_order import sort_rows, value_rank

FIXED_COLUMNS = (
    ("data_date", "数据日期"),
    ("identity", "手机/品牌/系列/型号/网络型号"),
)
IDENTITY_FIELDS = ("category", "brand", "series", "model", "model_code")
SOURCE_COLUMN = ("source_image", "来源图片")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def build_identity(row):
    return " ".join(clean(row.get(field, "")) for field in IDENTITY_FIELDS if clean(row.get(field, "")))


def _condition_key(value):
    return clean(value).replace(" ", "")


def _condition_sort_key(row):
    # Condition columns follow the same real-world value semantics as records.
    return tuple(-x for x in value_rank(row)) + (
        clean(row.get("condition", "")),
    )


def _char_width(text):
    """Approximate Tk/Excel display width from actual character occupancy."""
    width = 0
    for ch in clean(text):
        width += 2 if unicodedata.east_asian_width(ch) in {"W", "F"} else 1
    return width


def column_width(title, values=(), minimum=90, maximum=420):
    occupied = max([_char_width(title)] + [_char_width(v) for v in values])
    return max(minimum, min(maximum, occupied * 9 + 22))


def _condition_columns(rows):
    representatives = {}
    for row in rows:
        condition = clean(row.get("condition", ""))
        if not condition:
            continue
        representatives.setdefault(_condition_key(condition), row)
    ordered = sorted(representatives.values(), key=_condition_sort_key)
    return [(f"condition_{i}", clean(r.get("condition", ""))) for i, r in enumerate(ordered)]


def _group_rows(rows):
    groups = {}
    for row in rows:
        identity_key = tuple(clean(row.get(field, "")) for field in IDENTITY_FIELDS)
        date = clean(row.get("data_date", ""))
        groups.setdefault((identity_key, date), []).append(row)
    return groups


def build_display_columns(rows):
    """Create columns from the actual result set, preserving real condition names."""
    condition_reps = {}
    for row in rows:
        condition = clean(row.get("condition", ""))
        if condition:
            condition_reps.setdefault(_condition_key(condition), row)
    ordered = sorted(condition_reps.values(), key=_condition_sort_key)
    columns = [(field, title, 0) for field, title in FIXED_COLUMNS]
    for i, row in enumerate(ordered):
        columns.append((f"condition_{i}", clean(row.get("condition", "")), 0))
    columns.append((SOURCE_COLUMN[0], SOURCE_COLUMN[1], 0))

    grouped = _group_rows(rows)
    values_by_field = {field: [] for field, _title, _width in columns}
    for (identity_key, date), group in grouped.items():
        values_by_field["data_date"].append(date)
        values_by_field["identity"].append(build_identity(group[0]))
        values_by_field["source_image"].extend(clean(r.get("source_image", "")) for r in group)
        for i, (_field, title, _width) in enumerate(columns[2:-1]):
            values_by_field[f"condition_{i}"].extend(clean(r.get("price", "")) for r in group if _condition_key(r.get("condition", "")) == _condition_key(title))
    return tuple((field, title, column_width(title, values_by_field.get(field, ()))) for field, title, _ in columns)


def normalize_search_results(rows):
    """Return independent model/date blocks with complete condition data."""
    source_rows = list(rows or [])
    columns = build_display_columns(source_rows)
    groups = {}
    for row in source_rows:
        identity_key = tuple(clean(row.get(field, "")) for field in IDENTITY_FIELDS)
        date = clean(row.get("data_date", ""))
        groups.setdefault((identity_key, date), []).append(row)

    # Models are ordered canonically; periods are newest first within a model.
    model_groups = {}
    for (identity_key, date), group in groups.items():
        model_groups.setdefault(identity_key, []).append((date, group))
    model_groups = sorted(model_groups.items(), key=lambda item: _model_sort_key(item[1]))

    result = []
    for model_index, (identity_key, periods) in enumerate(model_groups):
        periods.sort(key=lambda item: item[0], reverse=True)
        for period_index, (date, group) in enumerate(periods):
            condition_values = {}
            source_images = []
            for row in group:
                condition = clean(row.get("condition", ""))
                price = clean(row.get("price", ""))
                key = _condition_key(condition)
                if key and price:
                    condition_values.setdefault(key, []).append(price)
                image = clean(row.get("source_image", ""))
                if image and image not in source_images:
                    source_images.append(image)
            out = {
                "data_date": date,
                "identity": build_identity(group[0]),
                "source_image": " / ".join(source_images),
                "_rows": sort_rows(group),
                "_model_key": identity_key,
                "_period_key": date,
                "_model_index": model_index,
                "_period_index": period_index,
                "_columns": columns,
            }
            for i, (_field, title, _width) in enumerate(columns[2:-1]):
                vals = condition_values.get(_condition_key(title), [])
                # Never discard duplicate facts: preserve every price in the same cell.
                out[f"condition_{i}"] = " / ".join(vals)
            result.append(out)
        if model_index < len(model_groups) - 1:
            result.append({"_separator": "model", "_columns": columns})
    return result


def _model_sort_key(periods):
    rows = [r for _date, group in periods for r in group]
    ordered = sort_rows(rows)
    if not ordered:
        return ()
    return tuple(-x for x in value_rank(ordered[0])) + (
        build_identity(ordered[0]),
    )


# Backward-compatible alias used by tests and older imports.
DISPLAY_COLUMNS = (
    ("data_date", "数据日期", 105),
    ("identity", "手机/品牌/系列/型号/网络型号", 420),
    ("condition_0", "开机靓机/靓机/开机好屏", 145),
    ("condition_1", "开机好屏/内屏碎", 145),
    ("condition_2", "开机好碎", 145),
    ("condition_3", "开机碎屏", 145),
    ("condition_4", "不开机/开机坏配件", 145),
    ("condition_5", "废板·整机", 145),
    ("source_image", "来源图片", 150),
)
