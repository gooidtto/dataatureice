#!/usr/bin/env python3
"""Add a conservative sixth pass of clearly readable 2026-07 image facts."""
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

# 0710 desktop mainboard image: top desktop-machine rows plus all clearly legible board tables.
p,rows=load('2026-07-10');img='电脑主板.jpg';path='数码网报价单-0710更新/电脑以及电脑配件/'+img
for model,price,note in [('最老款电脑主板 无桥',70,'主机主板'),('最老款电脑主板 单桥',80,'主机主板'),('主机桥皮',1.5,'主机主板'),('最老款电脑主板 双桥',125,'无硬盘')]: add(rows,'2026-07-10','电脑','台式机主板','', '台式机主机',model,'价格',price,'元/块',img,path,note)
for model,price in [('h610',75),('H510',75),('H410',55),('H110',80),('B150',80),('B250',75),('B360',70),('B365',70),('B460',70),('B560',70),('B660',70),('z370',70),('Z490',70),('Z590',70),('Z690',70),('H61',15),('H81',20),('B85',20),('B75',15),('J1900',30),('H55',10),('P55',10),('A55',10)]: add(rows,'2026-07-10','电脑','台式机主板','','台式机主板',model,'点数',price,'元/块',img,path,'方芯片50' if model in {'B360','B365','B460','B560','B660','z370','Z490','Z590','Z690'} else '')
for model,price in [('无桥主板',16),('单桥主板',33),('双桥主板',67)]: add(rows,'2026-07-10','电脑','台式机主板','','桥系列',model,'称斤',price,'元/斤',img,path)
for model,price,note in [('hm55',5,'带显卡'),('m65',10,'不带显卡'),('hm65',10,'带显卡'),('hm86',20,'不带显卡'),('d525',2,'带显卡'),('h55',5,'不带显卡')]: add(rows,'2026-07-10','电脑','笔记本主板','','笔记本主板',model,'点数',price,'元/块',img,path,note)
write('2026-07-10',p,rows)

# 0710 computer hard-disk image: all table rows are legible.
p,rows=load('2026-07-10');img='电脑硬盘.jpg';path='数码网报价单-0710更新/电脑以及电脑配件/'+img
for model,v in [('20T',(1600,500,12)),('18T',(1500,450,12)),('16T',(1400,400,12)),('14T',(1200,360,12)),('12T',(1200,320,12)),('10T',(1150,300,12)),('8T',(1100,280,12)),('6T',(580,200,12)),('4T',(380,160,12)),('3T',(200,90,12)),('2T',(190,80,12)),('1T',(120,50,12)),('老款1T',(80,20,12)),('500G',(20,12,12)),('老款500G',(12,12,12)),('320G',(12,12,12)),('160G以下',(12,12,12)),('老款4T',(320,80,12)),('老款3T',(160,60,12)),('老款2T',(150,50,12))]:
 conds=['测好','坏道','坏']; matrix(rows,'2026-07-10','电脑','台式机硬盘','','台式机硬盘',model,conds,v,'元/个',img,path)
for model,v in [('4T',(300,40,3)),('3T',(200,35,3)),('2T',(160,30,3)),('1T',(110,15,3)),('500G',(35,3,3)),('320G',(15,3,3)),('250G',(3,3,3)),('160G',(3,3,3))]: matrix(rows,'2026-07-10','电脑','笔记本硬盘','','笔记本硬盘',model,['测好','坏道','坏'],v,'元/个',img,path)
for model,v in [('2T',(240,240,150)),('1T',(140,140,100)),('480G-512G',(100,100,70)),('240G-256G',(45,45,30)),('160G-180G',(25,25,15)),('120G-128G',(25,25,15)),('60G-64G',(10,10,10)),('30G-32G',(10,10,5)),('16G',(2,2,2)),('8G',(2,2,2)),('4G',(2,2,2))]: matrix(rows,'2026-07-10','电脑','固态硬盘','','固态硬盘',model,['测好','WiFi版','坏'],v,'元/个',img,path)
write('2026-07-10',p,rows)
