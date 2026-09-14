"""Unified search-result presentation.

Each result block is built independently from its own source rows. Fixed identity
columns are followed only by the actual price-condition names found in that
block, then source image. This prevents one result's dynamic columns from
shifting or borrowing columns from another result.
"""
import re
import unicodedata
from value_order import sort_rows, value_rank

FIXED_COLUMNS = (("data_date", "数据日期"), ("identity", "手机/品牌/系列/型号/网络型号"))
IDENTITY_FIELDS = ("category", "brand", "series", "model", "model_code")
SOURCE_COLUMN = ("source_image", "来源图片")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def build_identity(row):
    return " ".join(clean(row.get(field, "")) for field in IDENTITY_FIELDS if clean(row.get(field, "")))


def identity_key(row):
    """Canonical model identity shared by search and favorites."""
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
    """Return ``[(identity_key, [date_block, ...]), ...]`` in canonical order.

    Identity grouping is shared by search/favorites. Date blocks are always
    newest first. Historical price is never used for either grouping or order.
    """
    grouped = {}
    for row in list(rows or []):
        key = identity_key(row)
        date = clean(row.get("data_date", ""))
        grouped.setdefault(key, {}).setdefault(date, []).append(row)

    def model_sort_key(item):
        key, dates = item
        rows_for_model = [row for group in dates.values() for row in group]
        ordered = sort_rows(rows_for_model)
        if not ordered:
            return ((), key)
        return (tuple(-x for x in value_rank(ordered[0])), key)

    result = []
    for key, dates in sorted(grouped.items(), key=model_sort_key):
        blocks = [sort_rows(group) for _date, group in sorted(dates.items(), reverse=True)]
        result.append((key, blocks))
    return result


def build_display_columns(rows):
    """Create columns from the exact rows supplied; used for one result block."""
    rows = list(rows or [])
    reps = {}
    for row in rows:
        condition = clean(row.get("condition", ""))
        if condition:
            reps.setdefault(_condition_key(condition), row)
    ordered = sorted(reps.values(), key=_condition_sort_key)
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
    """Return dynamic columns strictly for one result block."""
    return build_display_columns(rows)


def normalize_search_results(rows):
    """Build model/date result blocks; every block owns an independent column set."""
    model_groups = group_model_dates(rows)
    result = []
    for model_index, (_identity_key, periods) in enumerate(model_groups):
        for period_index, group in enumerate(periods):
            if period_index > 0:
                result.append({"_separator": "period", "_model_index": model_index, "_period_index": period_index})
            block_rows = sort_rows(group)
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
            out = {
                "data_date": clean(block_rows[0].get("data_date", "")) if block_rows else "",
                "identity": build_identity(block_rows[0]) if block_rows else "",
                "source_image": " / ".join(source_images),
                "_rows": block_rows,
                "_model_key": identity_key(block_rows[0]) if block_rows else (),
                "_period_key": clean(block_rows[0].get("data_date", "")) if block_rows else "",
                "_model_index": model_index,
                "_period_index": period_index,
                "_columns": columns,
            }
            for field, title, _width in columns[2:-1]:
                out[field] = " / ".join(condition_values.get(_condition_key(title), []))
            result.append(out)
        if model_index < len(model_groups) - 1:
            for _ in range(2):
                result.append({"_separator": "model", "_model_index": model_index})
    return result


# Legacy import compatibility. This constant is intentionally only a fallback;
# runtime search rendering now builds columns per result block.
DISPLAY_COLUMNS = (("data_date", "数据日期", 105), ("identity", "手机/品牌/系列/型号/网络型号", 420), ("condition_0", "开机靓机/靓机/开机好屏", 145), ("condition_1", "开机好屏/内屏碎", 145), ("condition_2", "开机好碎", 145), ("condition_3", "开机碎屏", 145), ("condition_4", "不开机/开机坏配件", 145), ("condition_5", "废板·整机", 145), ("source_image", "来源图片", 150))
