"""Search-result presentation normalization.

This module changes presentation only. Canonical 19-field database rows are
never modified or collapsed on disk. Search rows are grouped by date +
brand + series + model + network model, then condition prices are pivoted into
stable columns for fast quote lookup.
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
    ("source_image", "来源图片", 150),
)


def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()


def _condition_bucket(condition):
    value = clean(condition)
    compact = value.replace(" ", "")
    if any(token in compact for token in ("废板", "整机")):
        return "condition_waste"
    if any(token in compact for token in ("不开机", "不开", "坏配件", "配件坏")):
        return "condition_bad_parts"
    if "碎屏" in compact:
        return "condition_cracked"
    if "好碎" in compact:
        return "condition_good_broken"
    if any(token in compact for token in ("内屏碎", "屏碎", "屏幕碎")):
        return "condition_screen"
    if any(token in compact for token in ("靓机", "靓好", "靓", "好屏", "开机好")):
        return "condition_grade"
    return None


def _identity(row):
    parts = [
        clean(row.get("category", "")),
        clean(row.get("brand", "")),
        clean(row.get("series", "")),
        clean(row.get("model", "")),
        clean(row.get("model_code", "")),
    ]
    return " ".join(part for part in parts if part)


def normalize_search_results(rows):
    """Return display-only model/date rows, newest date first within each model."""
    groups = {}
    for row in rows:
        key = (
            clean(row.get("category", "")),
            clean(row.get("brand", "")),
            clean(row.get("series", "")),
            clean(row.get("model", "")),
            clean(row.get("model_code", "")),
            clean(row.get("data_date", "")),
        )
        group = groups.setdefault(key, {"source_image": "", "prices": {}, "rows": []})
        group["rows"].append(row)
        source = clean(row.get("source_image", ""))
        if source and not group["source_image"]:
            group["source_image"] = source
        bucket = _condition_bucket(row.get("condition", ""))
        if bucket and clean(row.get("price", "")) and bucket not in group["prices"]:
            group["prices"][bucket] = clean(row.get("price", ""))

    result = []
    for key, group in groups.items():
        category, brand, series, model, model_code, date = key
        out = {
            "data_date": date,
            "identity": " ".join(x for x in (category, brand, series, model, model_code) if x),
            "source_image": group["source_image"],
            "_rows": list(group["rows"]),
        }
        for bucket, _label in PRICE_COLUMNS:
            out[bucket] = group["prices"].get(bucket, "")
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
