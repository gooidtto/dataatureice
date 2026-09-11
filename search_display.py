"""Search-result presentation normalization.

Presentation only: canonical 19-field database rows are never modified or
collapsed on disk. Search rows are grouped by identity/date, while every
source price condition is rendered in its corresponding horizontal bucket
with the original condition text and price preserved.
"""
import re
import unicodedata

PRICE_COLUMNS = (
    ("condition_grade", "开机靓机/靓机"),
    ("condition_screen", "开机好屏/内屏"),
    ("condition_good_broken", "开机好碎"),
    ("condition_cracked", "开机碎屏"),
    ("condition_bad_parts", "不开机/坏配件"),
    ("condition_waste", "废板·整机"),
)
DISPLAY_COLUMNS = (
    ("data_date", "数据日期", 105),
    ("identity", "手机/品牌/系列/型号/网络型号", 420),
    *tuple((key, label, 175) for key, label in PRICE_COLUMNS),
    ("source_image", "来源图片", 150),
)
IDENTITY_FIELDS = ("category", "brand", "series", "model", "model_code")


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def _condition_bucket(condition):
    """Place the original source condition into its display bucket only.

    The bucket is presentation-only. The original condition text remains
    visible in the cell, and the canonical source row remains unchanged.
    """
    value = clean(condition)
    compact = value.replace(" ", "")
    if not compact:
        return None
    if "废板" in compact or compact == "整机":
        return "condition_waste"
    if "不开机" in compact or "坏配件" in compact:
        return "condition_bad_parts"
    if compact == "开机好碎" or ("好碎" in compact and "屏" not in compact):
        return "condition_good_broken"
    if "好屏" in compact or "内屏" in compact or "屏好" in compact:
        return "condition_screen"
    if "碎屏" in compact or compact == "开机屏碎":
        return "condition_cracked"
    if "靓机" in compact or "靓好" in compact or compact in {"靓机", "靓好", "开机好"}:
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
    """Return display-only model/date rows with every quote in its bucket."""
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
            {"identity": identity, "source_images": [], "prices": {}, "rows": []},
        )
        group["rows"].append(row)

        source = clean(row.get("source_image", ""))
        if source and source not in group["source_images"]:
            group["source_images"].append(source)

        bucket = _condition_bucket(row.get("condition", ""))
        quote = _quote_text(row)
        if bucket and quote:
            group["prices"].setdefault(bucket, []).append(quote)

    result = []
    for key, group in groups.items():
        _category, _brand, _series, _model, _model_code, date = key
        out = {
            "data_date": date,
            "identity": group["identity"],
            "source_image": "；".join(group["source_images"]),
            "_rows": list(group["rows"]),
        }
        for bucket, _label in PRICE_COLUMNS:
            out[bucket] = "\n".join(group["prices"].get(bucket, []))
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
