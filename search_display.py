"""Search-result presentation normalized by the real-world value rule."""
import re
import unicodedata
from value_order import sort_display_groups

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
IDENTITY_FIELDS = ("category", "brand", "series", "model", "model_code")

def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()

def _condition_bucket(condition):
    value = clean(condition); compact = value.replace(" ", "")
    if any(token in compact for token in ("废板", "整机")): return "condition_waste"
    if any(token in compact for token in ("不开机", "不开", "坏配件", "配件坏")): return "condition_bad_parts"
    if "碎屏" in compact: return "condition_cracked"
    if "好碎" in compact: return "condition_good_broken"
    if any(token in compact for token in ("内屏碎", "屏碎", "屏幕碎")): return "condition_screen"
    if any(token in compact for token in ("靓机", "靓好", "靓", "好屏", "开机好")): return "condition_grade"
    return None

def build_identity(row):
    return " ".join(clean(row.get(field, "")) for field in IDENTITY_FIELDS if clean(row.get(field, "")))

def normalize_search_results(rows):
    groups = {}
    for row in rows:
        category = clean(row.get("category", "")); brand = clean(row.get("brand", "")); series = clean(row.get("series", "")); model = clean(row.get("model", "")); model_code = clean(row.get("model_code", "")); date = clean(row.get("data_date", ""))
        identity = build_identity(row); key = (category, brand, series, model, model_code, date)
        group = groups.setdefault(key, {"identity": identity, "source_image": "", "prices": {}, "rows": []})
        group["rows"].append(row)
        source = clean(row.get("source_image", ""))
        if source and not group["source_image"]: group["source_image"] = source
        bucket = _condition_bucket(row.get("condition", ""))
        if bucket and clean(row.get("price", "")) and bucket not in group["prices"]:
            group["prices"][bucket] = clean(row.get("price", ""))
    result = []
    for key, group in groups.items():
        _category, _brand, _series, _model, _model_code, date = key
        out = {"data_date": date, "identity": group["identity"], "source_image": group["source_image"], "_rows": list(group["rows"])}
        for bucket, _label in PRICE_COLUMNS: out[bucket] = group["prices"].get(bucket, "")
        result.append(out)
    result = sort_display_groups(result)
    ordered = []; last_identity = None
    for row in result:
        identity = row["identity"]
        if last_identity is not None and identity != last_identity: ordered.append({"_separator": True})
        ordered.append(row); last_identity = identity
    return ordered
