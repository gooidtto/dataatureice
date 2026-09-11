#!/usr/bin/env python3
"""Add a conservative seventh pass of clearly readable 2026-07 image facts."""
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

# 0705 mobile-screen scrap image: all six table rows are legible; slash cells are skipped.
p,rows=load('2026-07-05');img='手机屏幕2.jpg';path='数码网报价单-0705更新/2.手机配件/'+img
items=[('全面屏/水滴屏/刘海屏',1.2,'要求有4成内爆不破；全破0.4元/个'),('COF',1.5,'要求有3成内屏不破；全破0.5元/个'),('TFT',1,'要求有3成内屏不破；全破0.4元/个'),('6-8代苹果屏统点',1.2,''),('X以上苹果屏',3.5,'')]
for model,price,note in items: add(rows,'2026-07-05','手机配件','手机屏幕','','报废手机屏',model,'点数',price,'元/个',img,path,note)
add(rows,'2026-07-05','手机配件','手机屏幕','','称斤系列','称斤废屏','称斤',5,'元/斤',img,path)
write('2026-07-05',p,rows)

# 0705 elderly-phone image: table rows are legible. Page itself shows an update date of 2026-07-14; archive date remains the 0705 batch.
p,rows=load('2026-07-05');img='老年机.jpg';path='数码网报价单-0705更新/2.手机配件/'+img
items=[('功能机（老年机）有电池',11,'有电池'),('功能机（老年机）无电池',10,'无电池'),('翻盖老款机（称斤杂机）',200,''),('两面以上翻盖机（称斤杂机）',90,''),('直板机（称斤杂机）',75,''),('双卡大喇叭',8.1,''),('老款5110系列',40,''),('老款翻盖系列',26,''),('老款低档翻盖系列',20,''),('老款低档翻盖至70、72系列',30,''),('老款低档翻盖至V3、L6L7系列',30,''),('老款摩托罗拉大哥大',60,''),('保千里守护V9至尊版',1999,''),('TCL999D配件',1666,''),('双小卡老年机银机',12,''),('双小卡老年机通点',11,'')]
for model,price,note in items:
 cond='价格' if not note else note
 unit='元/台' if price>=100 else '元/个'
 add(rows,'2026-07-05','手机配件','老年机','','老年机',model,cond,price,unit,img,path,'图片页面更新时间显示2026-07-14；按0705批次归档')
write('2026-07-05',p,rows)

# 0705 Apple high-end original-screen image: slash cells are not guessed or entered.
p,rows=load('2026-07-05');img='苹果手机屏幕.jpg';path='数码网报价单-0705更新/2.手机配件/'+img
apple=[('苹果16pro',(300,150,None,None)),('苹果16',(40,15,15,3)),('苹果15Promax',(40,10,8,3)),('苹果15Pro',(40,10,8,3)),('苹果13',(None,None,None,None)),('苹果14Promax',(15,10,8,3)),('苹果15',(None,None,None,None))]
for model,v in apple: matrix(rows,'2026-07-05','手机配件','苹果手机屏幕','苹果','高端原装内爆屏',model,['LG内爆点亮原IC','LG内爆点亮无IC','LG内爆不亮','三星内爆不亮'],v,'元/个',img,path,'清一色炸屏屏不要；断排线的不要')
write('2026-07-05',p,rows)
