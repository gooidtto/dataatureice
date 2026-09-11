"""Search-result presentation normalization.

Presentation only: canonical 19-field database rows are never modified or
collapsed on disk. Search rows are grouped by the fields that actually exist
in the source rows, while every source price condition remains recoverable in
the horizontal result view and in the raw-price detail view.
"""
import re
import unicodedata

PRICE_COLUMNS = (
    ("condition_grade", "开机靓机/靓机/开机好屏"),
    ("condition_screen", "开机好屏/内屏碎"),
    ("condition_good_broken", "开机好碎"),
    ("condition_cracked", "开机碎屏"),
    ("condition_bad_parts", "不开机/开机坏配件"),
    ("condition_waste", "废板·整机"),
)
DISPLAY_COLUMNS = (
    ("data_date", "数据日期", 105),
    ("identity", "手机/品牌/系列/型号/网络型号", 420),
    *tuple((key, label, 145) for key, label in PRICE_COLUMNS),
    ("quote_detail", "全部报价（原始条件/价格）", 460),
    ("source_image", "来源图片", 150),
)
IDENTITY_FIELDS = ("category", "brand", "series", "model", "model_code")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def _condition_bucket(condition):
    """Map only established condition names; never invent a price state."""
    value = clean(condition)
    compact = value.replace(" ", "")
    if compact == "废板·整机":
        return "condition_waste"
    if compact in {"不开机", "开机坏配件"}:
        return "condition_bad_parts"
    if compact == "开机好碎":
        return "condition_good_broken"
    if compact in {"开机碎屏", "开机屏碎"}:
        return "condition_cracked"
    if compact in {"开机好屏/内屏碎", "内屏碎"}:
        return "condition_screen"
    if compact in {"开机靓好", "开机靓机", "靓机", "开机好屏", "开机好"}:
        return "condition_grade"
    return None


def build_identity(row):
    """Build the compact identity from fields that actually exist in the row."""
    return " ".join(clean(row.get(field, "")) for field in IDENTITY_FIELDS if clean(row.get(field, "")))


def _quote_text(row):
    condition = clean(row.get("condition", ""))
    price = clean(row.get("price", ""))
    unit = clean(row.get("unit", ""))
    if not condition and not price:
        return ""
    suffix = f" {unit}" if unit else ""
    return f"{condition}：{price}{suffix}" if condition else f"{price}{suffix}"


def normalize_search_results(rows):
    """Return display-only model/date rows while retaining every source quote."""
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
        group = groups.setdefault(
            key,
            {"identity": identity, "source_images": [], "prices": {}, "quote_rows": [], "rows": []},
        )
        group["rows"].append(row)

        source = clean(row.get("source_image", ""))
        if source and source not in group["source_images"]:
            group["source_images"].append(source)

        quote = _quote_text(row)
        if quote:
            group["quote_rows"].append(quote)

        bucket = _condition_bucket(row.get("condition", ""))
        price = clean(row.get("price", ""))
        if bucket and price:
            group["prices"].setdefault(bucket, []).append(price)

    result = []
    for key, group in groups.items():
        _category, _brand, _series, _model, _model_code, date = key
        out = {
            "data_date": date,
            "identity": group["identity"],
            "quote_detail": "；".join(group["quote_rows"]),
            "source_image": "；".join(group["source_images"]),
            "_rows": list(group["rows"]),
        }
        for bucket, _label in PRICE_COLUMNS:
            # Never discard repeated source values. The detail view retains the
            # underlying rows; the matrix cell simply renders all values.
            out[bucket] = " / ".join(group["prices"].get(bucket, []))
        result.append(out)

    result.sort(key=lambda row: (
        row["identity"],
        -int(row["data_date"].replace("-", "") or 0),
    ))

    ordered = []
    last_identity = None
    for row in result:
        identity = row["identity"]
        if last_identity is not None and identity != last_identity:
            ordered.append({"_separator": True})
        ordered.append(row)
        last_identity = identity
    return ordered
