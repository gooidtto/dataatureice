#!/usr/bin/env python3
"""Add a conservative ninth pass of clearly readable 2026-07 image facts."""
import hashlib
from pathlib import Path
from date_database import FIELDS, load, write
ROOT=Path(__file__).resolve().parents[1]

def add(rows,date,cat,sub,brand,series,model,cond,price,unit,img,path,note=''):
 r={k:'' for k in FIELDS};r.update(data_date=date,category=cat,subtype=sub,brand=brand,series=series,model=model,condition=cond,price=str(price),unit=unit,note=note,origin='image',source_image=img,source_path=path,verified='1',confidence='1.0',verification='visual_verified_from_uploaded_image')
 r['record_id']=hashlib.sha256('|'.join(r.get(x,'') for x in ('data_date','category','subtype','brand','series','model','condition','price','unit')).encode()).hexdigest()[:16];rows.append(r)
def matrix(rows,date,cat,sub,brand,series,model,conds,vals,unit,img,path,note=''):
 for c,v in zip(conds,vals):
  if v not in (None,'/'): add(rows,date,cat,sub,brand,series,model,c,v,unit,img,path,note)

# 0710 phone-screen image repeats the clearly readable six-row screen-scrap table.
rows=load('2026-07-10');img='手机屏幕.jpg';path='数码网报价单-0710更新/手机配件/'+img
items=[('全面屏/水滴屏/刘海屏',1.2,'要求有4成内屏不破；全破0.4元/个'),('COF',1.5,'要求有3成内屏不破；全破0.5元/个'),('TFT',1,'要求有3成内屏不破；全破0.4元/个'),('6-8代苹果屏统点',1.2,''),('X以上苹果屏',3.5,'')]
for model,price,note in items: add(rows,'2026-07-10','手机配件','手机屏幕','','报废手机屏',model,'点数',price,'元/个',img,path,note)
add(rows,'2026-07-10','手机配件','手机屏幕','','称斤系列','称斤废屏','称斤',5,'元/斤',img,path)
write('2026-07-10',rows)

rows=load('2026-07-10');img='手机摄像头.jpg';path='数码网报价单-0710更新/手机配件/'+img
for model,price in [('国产单头',0.2),('国产后置双头',0.5),('国产后置三头',1)]: add(rows,'2026-07-10','手机配件','手机摄像头','国产','摄像头',model,'点数',price,'元/个',img,path)
write('2026-07-10',rows)

rows=load('2026-07-10');img='废手机主板.jpg';path='数码网报价单-0710更新/手机配件/'+img
items=[('废手机主板（正常货）',260),('品牌智能机像头',450),('杂牌智能机像头',500),('功能机像头',500),('智能机小板',150),('智能机排线',150),('功能机排线',100),('功能机小板',100),('扁圆形震动',90),('圆柱形震动',90),('报废手机屏幕',8),('塑料手机壳',0.5),('铁、钢手机壳',5)]
for model,price in items: add(rows,'2026-07-10','手机配件','废手机拆解配件','','手机拆解件',model,'称斤',price,'元/斤',img,path,'图片表格标题为“称斤/公斤”；斜杠项目跳过')
write('2026-07-10',rows)

rows=load('2026-07-10'); write('2026-07-10',rows)
