#!/usr/bin/env python3
"""Add a conservative fourth pass of clearly readable 2026-07 image facts."""
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
 with p.open('w',encoding='utf-8-sig',newline='') as f: csv.DictWriter(f,fieldnames=FIELDS).writerows(out)
 print(date,len(out))

# 0705 POS machine image: table is fully legible.
p,rows=load('2026-07-05');img='POS机.jpg';path='数码网报价单-0705更新/5.其它/'+img
pos=[('sunmi v2pro',(25,25,25,25)),('sunmi v2s',(35,25,25,25)),('sunmi v2',(80,30,10,8)),('商米P2',(35,25,25,8)),('W 5920/US',(35,25,25,8)),('W 6900/p1',(20,20,20,8)),('S90蓝色（OGO移动）',(13,13,13,13)),('S90蓝色（MCO电信）',(13,13,13,13)),('S910（S/N7开头大仓）',(13,13,13,13)),('S910（S/N7开头小仓）',(13,13,13,13)),('S910（S/N0开头）',(13,13,13,13)),('A920白色',(15,15,15,8)),('A8',(20,15,15,8)),('8210',(13,13,13,13)),('7210',(13,13,13,13)),('大屏触摸POS机',(20,15,15,8)),('新款D210',(15,10,10,8)),('新国都G3',(13,13,13,13)),('VX680',(13,13,13,13)),('VX675',(13,13,13,13)),('S90灰色',(13,13,13,13)),('G2',(13,13,13,13)),('Me31',(13,13,13,13)),('MF90',(9,9,9,8)),('H9',(9,9,9,8)),('E350S',(9,9,9,8)),('E350',(9,9,9,8)),('S58（MOO电话机）',(9,9,9,8)),('S58（MOL固定机）',(9,9,9,8)),('S58（MGL移动）',(9,9,9,8)),('电签彩屏（2.4寸屏）',(4,2,4,2)),('电签黑白屏（2.4寸屏）',(2,1,2,1))]
for m,v in pos: matrix(rows,'2026-07-05','其它','POS','','POS机型号系列',m,['开机屏好','屏坏','不开机','废板-整机'],v,'元/台',img,path)
write('2026-07-05',p,rows)

# 0705 set-top box image: clearly readable tables; slash cells are skipped.
p,rows=load('2026-07-05');img='机顶盒.jpg';path='数码网报价单-0705更新/5.其它/'+img
for m,price in [('HG680-MC',50),('E900V22D',50),('HG680-LC',50),('UNT403G',50),('CM311-5',40),('MGV2000',30),('4K机顶盒大机体',30),('安卓4K机顶盒',30),('2K机顶盒',10),('MGV2000',30),('新魔百和',25)]: add(rows,'2026-07-05','其它','机顶盒','华为','机顶盒',m,'价格',price,'元/个',img,path)
for m,v in [('201-2',(30,20)),('401H',(30,15)),('E900V21E',(35,15)),('EC6108V9C',(30,None)),('E900V22E',(45,15)),('E900V22C',(45,15)),('6109-M',(30,15)),('301H',(30,15)),('680-KA',(35,15)),('6110-T',(35,15)),('6110-M',(35,15)),('6108 V9C',(30,None)),('ZXV10 B860AV2.1-A',(35,None)),('ZXV10 B860AV2.1-M',(35,None)),('ZXV10 B860AV3.2-M',(None,50)),('ZXV10 B860AV3.2-M2',(None,50)),('ZXV10 B860AV3.2-M6 PRO',(None,70)),('ZXV10 B860AV2.1',(35,None))]: matrix(rows,'2026-07-05','其它','机顶盒','华为','机顶盒',m,['点数','高变'],v,'元/个',img,path)
write('2026-07-05',p,rows)

# 0705 ID reader image: all price rows are legible.
p,rows=load('2026-07-05');img='身份证阅读器.jpg';path='数码网报价单-0705更新/5.其它/'+img
for section,items in [
('0501',[('13年身份证模块',90)]),
('0502',[('身份证模块',90)]),
('0503',[('24年身份证模块',420),('22年身份证模块',330),('23年身份证模块',350),('21年身份证模块',260),('20年身份证模块',240),('19年身份证模块',220),('18年身份证模块',200),('17年身份证模块',200),('16年身份证模块',190),('15年身份证模块',190),('13、14年及以下身份证模块',190)]),
('0513',[('0513 16年之前身份证模块',430),('0513 17-18年身份证模块',430),('0513 19年-20年身份证模块',430),('0513 21年身份证模块',430),('0513 22年身份证模块',450),('0513 23年身份证模块',480)]),
('其它',[('坏身份证阅读器',5)])]:
 for model,price in items: add(rows,'2026-07-05','其它','身份证阅读器',section,'身份证阅读器',model,'测好',price,'元/个',img,path)
write('2026-07-05',p,rows)
