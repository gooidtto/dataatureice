"""Search-result presentation normalization.

Two identity columns are always fixed. Quote columns are generated from the
actual raw ``condition`` names present in the current search result. Each row
fills only the conditions it owns. Quote columns are ordered by their highest
numeric price, high to low, and source image is always the final column.
"""
import re
import unicodedata

DATA_DATE_WIDTH = 115
IDENTITY_WIDTH = 380
QUOTE_WIDTH = 150
SOURCE_WIDTH = 140
FIXED_DISPLAY_COLUMNS = (("data_date", "数据日期", DATA_DATE_WIDTH),("identity", "手机/品牌/系列/型号/网络型号", IDENTITY_WIDTH))
DISPLAY_COLUMNS = (*FIXED_DISPLAY_COLUMNS,("source_image","来源图片",SOURCE_WIDTH))
IDENTITY_FIELDS=("category","brand","series","model","model_code")
# Kept as a compatibility constant for callers that still import it.
PRICE_COLUMNS=()

def clean(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", "" if value is None else str(value))).strip()

def _price_number(value):
    text=clean(value)
    if not text:return None
    m=re.search(r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)",text)
    try:return float(m.group(0)) if m else None
    except Exception:return None

def dynamic_quote_columns(rows):
    """Distinct raw conditions across the search result, ordered by max price."""
    grouped={}
    for order,row in enumerate(rows or []):
        condition=clean(row.get("condition",""));price=clean(row.get("price",""))
        if not condition or not price:continue
        meta=grouped.setdefault(condition,{"max":None,"order":order})
        number=_price_number(price)
        if number is not None and (meta["max"] is None or number>meta["max"]):meta["max"]=number
    ordered=sorted(grouped.items(),key=lambda item:(-(item[1]["max"] if item[1]["max"] is not None else float("-inf")),item[1]["order"],item[0]))
    return tuple(condition for condition,_meta in ordered)

def dynamic_quote_values(rows):
    """Price-only values for a result, preserving high-to-low order."""
    result={}
    for condition in dynamic_quote_columns(rows):
        values=[]
        for row in rows or []:
            if clean(row.get("condition",""))==condition and clean(row.get("price","")):
                values.append(clean(row.get("price","")))
        values.sort(key=lambda value: -(_price_number(value) if _price_number(value) is not None else float("-inf")))
        result[condition]="\n".join(values)
    return result

def build_identity(row):
    return " ".join(clean(row.get(field,"")) for field in IDENTITY_FIELDS if clean(row.get(field,"")))

def _quote_text(row):
    condition=clean(row.get("condition",""));price=clean(row.get("price",""));unit=clean(row.get("unit",""))
    if not condition and not price:return ""
    suffix=f" {unit}" if unit else ""
    return f"{condition}：{price}{suffix}" if condition else f"{price}{suffix}"

def display_columns_for_rows(rows):
    """Fixed identity columns + all raw conditions present in this search + source image last."""
    return tuple([*FIXED_DISPLAY_COLUMNS,*[(condition,condition,QUOTE_WIDTH) for condition in dynamic_quote_columns(rows)],("source_image","来源图片",SOURCE_WIDTH)])

def normalize_search_results(rows):
    groups={}
    for row in rows:
        category=clean(row.get("category",""));brand=clean(row.get("brand",""));series=clean(row.get("series",""));model=clean(row.get("model",""));model_code=clean(row.get("model_code",""));date=clean(row.get("data_date",""));identity=build_identity(row)
        key=(category,brand,series,model,model_code,date)
        group=groups.setdefault(key,{"identity":identity,"source_images":[],"quote_rows":[],"rows":[]})
        group["rows"].append(row)
        source=clean(row.get("source_image",""))
        if source and source not in group["source_images"]:group["source_images"].append(source)
        quote=_quote_text(row)
        if quote:group["quote_rows"].append(quote)
    result=[]
    for key,group in groups.items():
        _category,_brand,_series,_model,_model_code,date=key
        result.append({"data_date":date,"identity":group["identity"],"source_image":"；".join(group["source_images"]),"quote_detail":"；".join(group["quote_rows"]),"_rows":list(group["rows"]),**dynamic_quote_values(group["rows"])})
    result.sort(key=lambda row:(row["identity"],-int(row["data_date"].replace("-","") or 0)))
    ordered=[];last_identity=None
    for row in result:
        identity=row["identity"]
        if last_identity is not None and identity!=last_identity:ordered.append({"_separator":True})
        ordered.append(row);last_identity=identity
    return ordered
