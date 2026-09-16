"""Canonical search-result model and presentation helpers."""
import re
import unicodedata
from typing import TypedDict
from value_order import value_rank

FIXED_COLUMNS=(("data_date","数据日期"),("identity","手机/品牌/系列/型号/网络型号"))
IDENTITY_FIELDS=("category","brand","series","model","model_code")
MODEL_GROUP_FIELDS=("category","brand","model")
SOURCE_COLUMN=("source_image","来源图片")

class ResultBlock(TypedDict):
    data_date:str
    identity:str
    source_image:str
    _rows:list
    _model_key:tuple
    _period_key:str
    _model_index:int
    _period_index:int
    _columns:tuple

def clean(value):return re.sub(r"\s+"," ",unicodedata.normalize("NFKC","" if value is None else str(value))).strip()
def build_identity(row):return " ".join(clean(row.get(field,"")) for field in IDENTITY_FIELDS if clean(row.get(field,"")))
def identity_key(row):return tuple(clean(row.get(field,"")) for field in IDENTITY_FIELDS)

def model_family(value):
    """Return a conservative model-family key for suffix variants such as A59s/A59t/A59 5G."""
    text=clean(value)
    if not text:return ""
    base=clean(text.split("(",1)[0])
    compact=re.sub(r"\s+","",base).casefold()
    if compact.endswith("5g"):
        compact=compact[:-2]
    match=re.match(r"^(.+?\d+)(?:[a-z]{1,2})?$",compact)
    return match.group(1) if match else compact

def model_group_key(row):
    """Canonical real-world group key; series spelling must not split one model family."""
    return (clean(row.get("category","")),clean(row.get("brand","")),model_family(row.get("model","")))
def block_key(row):return identity_key(row)

def _date_key(value):
    text=clean(value)
    digits=re.sub(r"[^0-9]","",text)
    try:return int(digits or "0")
    except ValueError:return 0

def _model_group_sort_key(group_key,rows):
    representative=rows[0] if rows else {}
    return tuple(clean(representative.get(field,"" )).casefold() for field in ("category","brand")) + (group_key[-1].casefold(), clean(representative.get("series","")).casefold())

def canonical_display_sort(rows):
    """Final display order shared by search and favorites.

    Search relevance is deliberately ignored here. First group all matching rows by
    canonical category/brand/model-family, then sort groups deterministically. Inside
    each group, dates are descending and model-code/detail blocks stay together.
    """
    grouped={}
    for position,row in enumerate(list(rows or [])):
        key_=model_group_key(row)
        grouped.setdefault(key_,[]).append((position,row))

    ordered_groups=sorted(grouped.items(),key=lambda item:_model_group_sort_key(item[0],[r for _,r in item[1]]))
    result=[]
    for _,items in ordered_groups:
        items.sort(key=lambda pair:(-_date_key(pair[1].get("data_date","")),clean(pair[1].get("model_code","")).casefold(),tuple(-x for x in value_rank(pair[1])),clean(pair[1].get("condition","")).casefold(),pair[0]))
        result.extend(row for _,row in items)
    return result

def sort_rows(rows):return canonical_display_sort(rows)
def _condition_key(value):return clean(value).replace(" ","")
def _condition_sort_key(row):return tuple(-x for x in value_rank(row))+(clean(row.get("condition","")),)
def _char_width(text):return sum(2 if unicodedata.east_asian_width(ch) in {"W","F"} else 1 for ch in clean(text))
def column_width(title,values=(),minimum=90,maximum=420):
    occupied=max([_char_width(title)]+[_char_width(v) for v in values]);return max(minimum,min(maximum,occupied*9+22))

def group_model_dates(rows):
    """Build contiguous model/date blocks from rows already in canonical display order."""
    ordered=canonical_display_sort(rows)
    model_groups={}
    model_order=[]
    for row in ordered:
        model=model_group_key(row)
        if model not in model_groups:
            model_groups[model]=[]
            model_order.append(model)
        model_groups[model].append(row)

    groups=[]
    for model_index,model in enumerate(model_order):
        current_date=None
        current_code=None
        current_rows=[]
        period_index=-1
        for row in model_groups[model]:
            date=clean(row.get("data_date",""))
            code=clean(row.get("model_code",""))
            if current_rows and (date!=current_date or code!=current_code):
                groups.append((block_key(current_rows[0]),current_date,current_rows,model_index,period_index))
                current_rows=[]
            if not current_rows:
                period_index+=1
                current_date=date
                current_code=code
            current_rows.append(row)
        if current_rows:
            groups.append((block_key(current_rows[0]),current_date,current_rows,model_index,period_index))
    return groups

def build_display_columns(rows):
    """Build quote columns in canonical real-world value order."""
    rows=list(rows or []);reps={}
    for row in rows:
        condition=clean(row.get("condition",""));ck=_condition_key(condition)
        if condition and ck not in reps:reps[ck]=row
    ordered=sorted(reps.values(),key=_condition_sort_key)
    columns=[(field,title,0) for field,title in FIXED_COLUMNS]
    for i,row in enumerate(ordered):columns.append((f"condition_{i}",clean(row.get("condition","")),0))
    columns.append(SOURCE_COLUMN+(0,));values={field:[] for field,_,_ in columns}
    for row in rows:
        values["data_date"].append(clean(row.get("data_date","")));values["identity"].append(build_identity(row));values["source_image"].append(clean(row.get("source_image","")))
        for field,title,_ in columns[2:-1]:
            if _condition_key(row.get("condition",""))==_condition_key(title):values[field].append(clean(row.get("price","")))
    return tuple((field,title,column_width(title,values.get(field,()))) for field,title,_ in columns)

def build_result_columns(rows):return build_display_columns(rows)

def _build_block(model_index,period_index,block_rows):
    block_rows=list(block_rows or []);columns=build_result_columns(block_rows);condition_values={};source_images=[]
    for row in block_rows:
        condition=clean(row.get("condition",""));price=clean(row.get("price",""));ck=_condition_key(condition)
        if ck and price:condition_values.setdefault(ck,[]).append(price)
        image=clean(row.get("source_image",""))
        if image and image not in source_images:source_images.append(image)
    first=block_rows[0] if block_rows else {};out={"data_date":clean(first.get("data_date","")),"identity":build_identity(first),"source_image":" / ".join(source_images),"_rows":block_rows,"_model_key":model_group_key(first) if first else (),"_period_key":clean(first.get("data_date","")),"_model_index":model_index,"_period_index":period_index,"_columns":columns}
    for field,title,_ in columns[2:-1]:out[field]=" / ".join(condition_values.get(_condition_key(title),[]))
    return out

def build_result_blocks(rows):
    blocks=[]
    for model_key,date,group,model_index,period_index in group_model_dates(rows):blocks.append(_build_block(model_index,period_index,group))
    for display_index,block in enumerate(blocks):block["_display_index"]=display_index
    return blocks

def normalize_search_results(rows):
    blocks=build_result_blocks(rows);result=[]
    for index,block in enumerate(blocks):
        if index and block["_model_index"]!=blocks[index-1]["_model_index"]:
            result.append({"_separator":"model","_model_index":blocks[index-1]["_model_index"]})
        result.append(block)
    return result

DISPLAY_COLUMNS=(("data_date","数据日期",105),("identity","手机/品牌/系列/型号/网络型号",420),("condition_0","开机靓机/靓机/开机好屏",145),("condition_1","开机好屏/内屏碎",145),("condition_2","开机好碎",145),("condition_3","开机碎屏",145),("condition_4","不开机/开机坏配件",145),("condition_5","废板·整机",145),("source_image","来源图片",150))