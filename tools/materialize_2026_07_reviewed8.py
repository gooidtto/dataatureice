#!/usr/bin/env python3
"""Add a conservative eighth pass of clearly readable 2026-07 image facts."""
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

# 0710 Apple inner-broken screens: same clearly legible price matrix as the source table.
p,rows=load('2026-07-10');img='苹果内爆屏幕.jpg';path='数码网报价单-0710更新/手机配件/'+img
apple=[('苹果16pro',(300,150,None,None)),('苹果16',(40,15,15,3)),('苹果15Promax',(40,10,8,3)),('苹果15Pro',(40,10,8,3)),('苹果13',(None,None,None,None)),('苹果14Promax',(15,10,8,3)),('苹果15',(None,None,None,None))]
for model,v in apple: matrix(rows,'2026-07-10','手机配件','苹果手机屏幕','苹果','高端原装内爆屏',model,['LG内爆点亮原IC','LG内爆点亮无IC','LG内爆不亮','三星内爆不亮'],v,'元/个',img,path,'清一色炸屏屏不要；断排线的不要')
write('2026-07-10',p,rows)

# 0710 battery image: all 23 price rows are legible; units follow each table header.
p,rows=load('2026-07-10');img='电池.jpg';path='数码网报价单-0710更新/手机配件/'+img
for model,price,note in [('软电池（斤）',44,'原装货没泡水不带充电宝软夹线；不收小货'),('品牌电池（斤）',35,'OV/小米/华为/三星/苹果/金立/联想/酷派/魅族/诺基亚等'),('杂牌电池（斤）',15,'包含杂牌4G、杂牌老年机；参考图说明')]: add(rows,'2026-07-10','手机配件','电池','','废旧电池（正常通货）',model,'正常',price,'元/斤',img,path,note)
add(rows,'2026-07-10','手机配件','电池','','软电池（挑货）','双电芯（斤）','挑货',52,'元/斤',img,path)
add(rows,'2026-07-10','手机配件','电池','vivo','品牌电池（挑货）','Y31电池','挑货',8,'元/个',img,path,'vivo Y31手机电池')
for model,price,note in [('杂牌薄片（斤）',20,'非品牌智能机电池'),('杂牌黄皮（斤）',9,'一般为老年机电池')]: add(rows,'2026-07-10','手机配件','电池','','杂牌电池（挑货）',model,'挑货',price,'元/斤',img,path,note)
for model,price in [('14系列',6),('13系列',4),('11/12系列',2.8),('X系列（x/xs/xsmax）',2.8),('8/8p系列',2.1),('7系列',1.8),('6s系列',1.8),('6以上的苹果缆货（斤）',60),('废苹果电池（斤）',60),('ipad电池（斤）',13)]: add(rows,'2026-07-10','手机配件','电池','苹果','苹果电池',model,'正常',price,'元/斤',img,path)
add(rows,'2026-07-10','手机配件','电池','汽车','动力电池','汽车动力电池18650','正常',1.5,'元/个',img,path,'来源新能源电动汽车')
add(rows,'2026-07-10','手机配件','电池','汽车','动力电池','汽车动力电池18650废电池','正常',3,'元/斤',img,path)
for model,price in [('铁锂电池（斤）',3),('镍氢电池（斤）',5),('镍钴电池（斤）',2)]: add(rows,'2026-07-10','手机配件','电池','锂电池','锂电池系列',model,'正常',price,'元/斤',img,path)
add(rows,'2026-07-10','手机配件','电池','','充电宝','充电宝（斤）','正常',5,'元/斤',img,path)
write('2026-07-10',p,rows)
