#!/usr/bin/env python3
"""Add a conservative fifth pass of clearly readable 2026-07 image facts."""
import csv,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
def load(date):
 p=ROOT/'data'/f'{date}.csv'; return p,list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''))) if p.exists() else []
def add(rows,date,cat,sub,brand,series,model,cond,price,unit,img,path,note=''):
 r={k:'' for k in FIELDS};r.update(data_date=date,category=cat,subtype=sub,brand=brand,series=series,model=model,condition=cond,price=str(price),unit=unit,note=note,origin='image',source_image=img,source_path=path,verified='1',confidence='1.0',verification='visual_verified_from_uploaded_image')
 r['record_id']=hashlib.sha256('|'.join(r.get(x,'') for x in ('data_date','category','subtype','brand','series','model','condition','price','unit')).encode()).hexdigest()[:16];rows.append(r)
def matrix(rows,date,cat,sub,brand,series,model,conds,vals,unit,img,path,note=''):
 for c,v in zip(conds,vals):
  if v not in (None,'/'): add(rows,date,cat,sub,brand,series,model,c,v,unit,img,path,note)
def write(date,p,rows):
 seen=set();out=[]
 for r in rows:
  if r['record_id'] not in seen: seen.add(r['record_id']);out.append(r)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 print(date,len(out))

# 0710 box-router image: all 18 rows are legible.
p,rows=load('2026-07-10');img='方盒子路由器.jpg';path='数码网报价单-0710更新/其它/'+img
router=[('华为','WS5280V2',(1,1)),('','A1WS852',(1,1)),('TP-Link','wifi6',(15,5)),('华为','荣耀W851',(10,5)),('TP-Link','TP-Link',(15,5)),('荣耀','PRO2',(15,5)),('荣耀','CD28',(6,5)),('荣耀','CD2',(7,5)),('荣耀','CD16',(7,5)),('腾达','MW6',(7,5)),('荣耀','路由2s',(10,5)),('','TP1950G',(10,5)),('捷稀','Q20；AX1800M',(10,5)),('中兴','ZXHNZ503',(6,5)),('','WS831',(7,5)),('纽曼','wifi6',(7,5)),('','HA030wc',(5,5)),('华为','MS826',(5,5))]
for brand,model,v in router: matrix(rows,'2026-07-10','其它','方盒子路由器',brand,'路由器',model,['通电','不通电'],v,'元/个',img,path)
write('2026-07-10',p,rows)

# 0710 desktop optical/power image: two rows, fully legible.
p,rows=load('2026-07-10');img='台式机光驱.jpg';path='数码网报价单-0710更新/电脑以及电脑配件/'+img
add(rows,'2026-07-10','电脑','台式机配件','','主机光驱','电脑主机光驱','称斤',4.3,'元/斤',img,path)
add(rows,'2026-07-10','电脑','台式机配件','','主机电源','电脑主机电源','称斤',5.2,'元/斤',img,path)
write('2026-07-10',p,rows)

# 0710 monitor image: all 15 price rows are legible.
p,rows=load('2026-07-10');img='显示器.jpg';path='数码网报价单-0710更新/电脑以及电脑配件/'+img
items=[('大头',(40,10,10)),('17寸',(15,15,1.8)),('15寸',(15,15,1.8)),('18.5寸',(22,15,1.8)),('19寸',(22,15,1.8)),('20.7寸',(15,5,1.8)),('20寸',(22,15,1.8)),('21.5寸',(50,15,1.8)),('21.6寸',(22,15,1.8)),('21寸',(22,15,1.8)),('22寸',(50,15,1.8)),('23.6寸',(50,15,1.8)),('24寸',(50,15,1.8)),('26寸',(50,15,1.8)),('32寸',(50,15,1.8))]
for model,v in items: matrix(rows,'2026-07-10','电脑','显示器','','显示器',model,['测屏好','屏坏外壳不破','屏坏外壳破'],v,'元/台',img,path,'图片表头条件逐项对应')
write('2026-07-10',p,rows)
