#!/usr/bin/env python3
"""Add a conservative third pass of clearly readable 2026-07 image facts."""
import csv, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']

def load(date):
 p=ROOT/'data'/f'{date}.csv'
 return p,list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''))) if p.exists() else []

def add(rows,date,cat,sub,brand,series,model,cond,price,unit,img,path,note=''):
 r={k:'' for k in FIELDS};r.update(data_date=date,category=cat,subtype=sub,brand=brand,series=series,model=model,condition=cond,price=str(price),unit=unit,note=note,origin='image',source_image=img,source_path=path,verified='1',confidence='1.0',verification='visual_verified_from_uploaded_image')
 r['record_id']=hashlib.sha256('|'.join(r.get(x,'') for x in ('data_date','category','subtype','brand','series','model','condition','price','unit')).encode()).hexdigest()[:16];rows.append(r)

def matrix(rows,date,cat,sub,brand,series,model,conds,vals,unit,img,path,note=''):
 for c,v in zip(conds,vals):
  if v not in (None,'/'): add(rows,date,cat,sub,brand,series,model,c,v,unit,img,path,note)

def write(date,p,rows):
 seen=set();out=[]
 for r in rows:
  if r['record_id'] not in seen:seen.add(r['record_id']);out.append(r)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
 print(date,len(out))

# 0705 scanning-gun image: only rows legible enough for deterministic entry.
p,rows=load('2026-07-05');img='扫描枪.jpg';path='数码网报价单-0705更新/其它/'+img
scan=[
('东大集成','小马哥5G版',(360,170,25,25)),('德邦','DPK3BP',(240,110,25,25)),('凯立','K7',(20,20,20,20)),('智联天地','N5S高版本',(20,20,20,20)),('智联天地','N5S低版本',(20,20,20,20)),('','st327v6a337',(180,80,15,15)),('识米','M2',(20,20,20,20)),('优博讯','i6310a 64G',(70,60,40,40)),('优博讯','i6310a 16G',(50,25,20,20)),('商米','L2S无扫描头',(20,20,20,20)),('商米','L2',(30,20,20,20)),('中通极客','X9',(30,20,20,20)),('肖邦','X8AT',(10,10,10,10)),('智联天地','N7e',(10,10,10,10)),('盒马生鲜','M1',(10,10,10,10))]
for brand,model,v in scan: matrix(rows,'2026-07-05','其它','扫描枪',brand,'扫描枪',model,['开机屏好','开机屏坏','不开机','进水生锈'],v,'元/个',img,path,'来源图表可辨识；仅录入清晰行')
add(rows,'2026-07-05','其它','扫描枪','','点数系列','杂牌扫描枪','点数',13,'元/个',img,path)
write('2026-07-05',p,rows)

# 0710 desktop mainboard image.
p,rows=load('2026-07-10');img='台式机主板.jpg';path='数码网报价单-0710更新/电脑以及电脑配件/'+img
for model,price in [('h610',65),('H510',65),('H410',55),('H110',70),('B150',70),('B250',70),('B360',55),('B365',55),('B460',55),('B560',55),('B660',55),('z370',55),('Z490',55),('Z590',55),('Z690',55),('H61',15),('H81',20),('B85',20),('B75',15),('J1900',30),('H55',10),('P55',10),('A55',10)]:
 add(rows,'2026-07-10','电脑','台式机主板','','台式机主板',model,'点数',price,'元/块',img,path)
for model,price in [('无桥主板',16),('单桥主板',36),('双桥主板',73)]: add(rows,'2026-07-10','电脑','台式机主板','','桥系列',model,'点数',price,'元/块',img,path)
for model,price,note in [('hm55',5,'带显卡'),('m65',10,'不带显卡'),('hm65',10,'带显卡'),('hm86',20,'不带显卡'),('d525',2,'带显卡'),('h55',5,'不带显卡')]: add(rows,'2026-07-10','电脑','笔记本主板','','笔记本主板',model,'点数',price,'元/块',img,path,note)
write('2026-07-10',p,rows)

# 0710 old all-in-one image repeats the clearly visible table.
p,rows=load('2026-07-10');img='老款一体机.jpg';path='数码网报价单-0710更新/电脑以及电脑配件/'+img
for model,v in [('18.5',(50,55,55,35)),('19',(50,55,60,35)),('20',(50,55,60,35)),('20.5',(50,55,60,35)),('21.5',(65,70,80,40)),('22',(65,70,75,40)),('23',(65,70,75,40)),('23.6',(65,70,75,40)),('24',(65,70,75,40)),('27',(65,70,75,40))]:
 matrix(rows,'2026-07-10','电脑','一体机','','AMD一体机',model,['AMD屏好','奔腾屏好','赛扬屏好','屏坏'],v,'元/台',img,path)
matrix(rows,'2026-07-10','电脑','一体机','苹果','','假苹果一体机',['屏好','屏坏'],(80,40),'元/台',img,path)
write('2026-07-10',p,rows)
