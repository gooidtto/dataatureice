"""Canonical search-result model and presentation helpers."""
import re
import unicodedata
from typing import TypedDict
from value_order import value_rank
FIXED_COLUMNS=(("data_date","数据日期"),("identity","手机/品牌/系列/型号/网络型号"))
IDENTITY_FIELDS=("category","brand","series","model","model_code")
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
def sort_rows(rows):return list(rows or [])
def _condition_key(value):return clean(value).replace(" ","")
def _condition_sort_key(row):return tuple(-x for x in value_rank(row))+(clean(row.get("condition","")),)
def _char_width(text):return sum(2 if unicodedata.east_asian_width(ch) in {"W","F"} else 1 for ch in clean(text))
def column_width(title,values=(),minimum=90,maximum=420):
    occupied=max([_char_width(title)]+[_char_width(v) for v in values]);return max(minimum,min(maximum,occupied*9+22))
def group_model_dates(rows):
    """Group only contiguous model/date runs; never move a supplied row."""
    groups=[];current_model=None;current_date=None;current_rows=[];model_index=-1;period_index=0
    for row in list(rows or []):
        model=identity_key(row);date=clean(row.get("data_date",""))
        if current_rows and (model!=current_model or date!=current_date):
            groups.append((current_model,current_date,current_rows,model_index,period_index));current_rows=[]
            if model!=current_model:model_index+=1;period_index=0
            else:period_index+=1
        if not current_rows and model!=current_model:
            if model_index<0:model_index=0
            period_index=0
        current_model,current_date=model,date;current_rows.append(row)
    if current_rows:groups.append((current_model,current_date,current_rows,model_index,period_index))
    return groups
def build_display_columns(rows):
    rows=list(rows or []);reps={};condition_order=[]
    for row in rows:
        condition=clean(row.get("condition",""));ck=_condition_key(condition)
        if condition and ck not in reps:reps[ck]=row;condition_order.append(ck)
    ordered=[reps[k] for k in condition_order];columns=[(field,title,0) for field,title in FIXED_COLUMNS]
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
    first=block_rows[0] if block_rows else {};out={"data_date":clean(first.get("data_date","")),"identity":build_identity(first),"source_image":" / ".join(source_images),"_rows":block_rows,"_model_key":identity_key(first) if first else (),"_period_key":clean(first.get("data_date","")),"_model_index":model_index,"_period_index":period_index,"_columns":columns}
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
        if index and block["_model_index"]==blocks[index-1]["_model_index"]:result.append({"_separator":"period","_model_index":block["_model_index"],"_period_index":block["_period_index"]})
        elif index:result.extend(({"_separator":"model","_model_index":blocks[index-1]["_model_index"]},{"_separator":"model","_model_index":blocks[index-1]["_model_index"]}))
        result.append(block)
    return result
DISPLAY_COLUMNS=(("data_date","数据日期",105),("identity","手机/品牌/系列/型号/网络型号",420),("condition_0","开机靓机/靓机/开机好屏",145),("condition_1","开机好屏/内屏碎",145),("condition_2","开机好碎",145),("condition_3","开机碎屏",145),("condition_4","不开机/开机坏配件",145),("condition_5","废板·整机",145),("source_image","来源图片",150))
