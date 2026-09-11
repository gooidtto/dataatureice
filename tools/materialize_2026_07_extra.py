#!/usr/bin/env python3
"""Add additional clearly readable 2026-07-10 image facts."""
import csv,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'data'/'2026-07-10.csv'
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
rows=list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''))) if p.exists() else []
img='小度，天猫，小爱.jpg';path='数码网报价单-0710更新/其它/'+img
for brand,model,v in [('小度','小度X10',(110,50)),('小度','小度X9',(50,20)),('小度','小度X8',(35,10)),('小度','小度7寸屏',(35,7)),('小度','小度5.5寸屏',(15,5)),('天猫精灵','天猫精灵7寸屏',(30,7)),('天猫精灵','天猫精灵10寸屏',(40,7)),('小米','小米小爱触屏音响',(20,8))]:
 for cond,price in zip(['屏好','屏坏'],v):
  r={k:'' for k in FIELDS};r.update(data_date='2026-07-10',category='其它',subtype='播放器',brand=brand,series=brand,model=model,condition=cond,price=str(price),unit='元/台',origin='image',source_image=img,source_path=path,verified='1',confidence='1.0',verification='visual_verified_from_uploaded_image')
  r['record_id']=hashlib.sha256('|'.join(r.get(x,'') for x in ('data_date','category','subtype','brand','series','model','condition','price','unit')).encode()).hexdigest()[:16];rows.append(r)
seen=set();out=[]
for r in rows:
 if r['record_id'] not in seen:seen.add(r['record_id']);out.append(r)
with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
print('2026-07-10 extra rows added; total=%d'%len(out))
