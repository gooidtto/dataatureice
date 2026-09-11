"""Search-result presentation for independent per-result quote matrices.

Each result owns its complete horizontal matrix. The identity columns are fixed;
quote columns come only from that result's own raw condition names. Quote
columns are ordered by the highest numeric price for that condition, descending.
The source image column is always last. No source row is mutated.
"""
import re
import unicodedata

DATA_DATE_WIDTH = 115
IDENTITY_WIDTH = 380
QUOTE_WIDTH = 150
SOURCE_WIDTH = 140
FIXED_DISPLAY_COLUMNS = (
    ("data_date", "数据日期", DATA_DATE_WIDTH),
    ("identity", "手机/品牌/系列/型号/网络型号", IDENTITY_WIDTH),
)
DISPLAY_COLUMNS = (*FIXED_DISPLAY_COLUMNS, ("source_image", "来源图片", SOURCE_WIDTH))
IDENTITY_FIELDS = ("category", "brand", "series", "model", "model_code")
# Compatibility only; quote columns are now generated from raw condition names.
PRICE_COLUMNS = ()


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def _price_number(value):
    text = clean(value)
    if not text:
        return None
    match = re.search(r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)", text)
    try:
        return float(match.group(0)) if match else None
    except Exception:
        return None


def dynamic_quote_columns(rows):
    """Return this result's raw conditions ordered by highest price, high to low."""
    grouped = {}
    for order, row in enumerate(rows or []):
        condition = clean(row.get("condition", ""))
        price = clean(row.get("price", ""))
        if not condition or not price:
            continue
        meta = grouped.setdefault(condition, {"max": None, "order": order})
        number = _price_number(price)
        if number is not None and (meta["max"] is None or number > meta["max"]):
            meta["max"] = number
    return tuple(
        condition
        for condition, meta in sorted(
            grouped.items(),
            key=lambda item: (
                -(item[1]["max"] if item[1]["max"] is not None else float("-inf")),
                item[1]["order"],
                item[0],
            ),
        )
    )


def dynamic_quote_values(rows):
    """Return price-only values keyed by the result's own raw condition names."""
    result = {}
    for condition in dynamic_quote_columns(rows):
        values = [clean(row.get("price", "")) for row in rows or [] if clean(row.get("condition", "")) == condition and clean(row.get("price", ""))]
        values.sort(key=lambda value: -(_price_number(value) if _price_number(value) is not None else float("-inf")))
        result[condition] = "\n".join(values)
    return result


def build_identity(row):
    return " ".join(clean(row.get(field, "")) for field in IDENTITY_FIELDS if clean(row.get(field, "")))


def result_display_columns(rows):
    """Build one complete column definition set for exactly one result."""
    conditions = dynamic_quote_columns(rows)
    return tuple([*FIXED_DISPLAY_COLUMNS, *[(condition, condition, QUOTE_WIDTH) for condition in conditions], ("source_image", "来源图片", SOURCE_WIDTH)])


def display_columns_for_rows(rows):
    """Build columns for a single result; retained for compatibility."""
    return result_display_columns(rows)


def _quote_text(row):
    condition = clean(row.get("condition", ""))
    price = clean(row.get("price", ""))
    unit = clean(row.get("unit", ""))
    if not condition and not price:
        return ""
    suffix = f" {unit}" if unit else ""
    return f"{condition}：{price}{suffix}" if condition else f"{price}{suffix}"


def normalize_search_results(rows):
    """Normalize raw rows into independent result blocks with independent columns.

    Preserve the incoming result order. The search/store layer already defines
    the ranking order (for example, newest date first), so a second alphabetical
    sort here could move an older/lower-ranked result ahead of the result the
    user actually searched for and make independent blocks appear mismatched.
    """
    groups = {}
    for row in rows:
        category = clean(row.get("category", ""))
        brand = clean(row.get("brand", ""))
        series = clean(row.get("series", ""))
        model = clean(row.get("model", ""))
        model_code = clean(row.get("model_code", ""))
        date = clean(row.get("data_date", ""))
        identity = build_identity(row)
        key = (category, brand, series, model, model_code, date)
        group = groups.setdefault(key, {"identity": identity, "source_images": [], "quote_rows": [], "rows": []})
        group["rows"].append(row)
        source = clean(row.get("source_image", ""))
        if source and source not in group["source_images"]:
            group["source_images"].append(source)
        quote = _quote_text(row)
        if quote:
            group["quote_rows"].append(quote)

    result = []
    for (_category, _brand, _series, _model, _model_code, date), group in groups.items():
        raw_rows = list(group["rows"])
        columns = result_display_columns(raw_rows)
        result.append(
            {
                "data_date": date,
                "identity": group["identity"],
                "source_image": "；".join(group["source_images"]),
                "quote_detail": "；".join(group["quote_rows"]),
                "_rows": raw_rows,
                "_columns": columns,
                "_condition_order": dynamic_quote_columns(raw_rows),
                **dynamic_quote_values(raw_rows),
            }
        )

    return result
