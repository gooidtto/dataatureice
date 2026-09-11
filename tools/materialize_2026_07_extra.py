#!/usr/bin/env python3
"""Add additional clearly readable 2026-07 image facts."""
import csv,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'data'/'2026-07-10.csv'
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
rows=list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''))) if p.exists() else []

def add_rows(img,path,items,category='其它',subtype='播放器'):
    unit='元/片' if category=='手机配件' else '元/台'
    for brand,model,conds,prices in items:
        for cond,price in zip(conds,prices):
            r={k:'' for k in FIELDS};r.update(data_date='2026-07-10',category=category,subtype=subtype,brand=brand,series=brand,model=model,condition=cond,price=str(price),unit=unit,origin='image',source_image=img,source_path=path,verified='1',confidence='1.0',verification='visual_verified_from_uploaded_image')
            r['record_id']=hashlib.sha256('|'.join(r.get(x,'') for x in ('data_date','category','subtype','brand','series','model','condition','price','unit')).encode()).hexdigest()[:16];rows.append(r)

img='小度，天猫，小爱.jpg';path='数码网报价单-0710更新/其它/'+img
add_rows(img,path,[
('小度','小度X10',['屏好','屏坏'],(110,50)),('小度','小度X9',['屏好','屏坏'],(50,20)),('小度','小度X8',['屏好','屏坏'],(35,10)),('小度','小度7寸屏',['屏好','屏坏'],(35,7)),('小度','小度5.5寸屏',['屏好','屏坏'],(15,5)),('天猫精灵','天猫精灵7寸屏',['屏好','屏坏'],(30,7)),('天猫精灵','天猫精灵10寸屏',['屏好','屏坏'],(40,7)),('小米','小米小爱触屏音响',['屏好','屏坏'],(20,8))])

img='ipad内爆屏幕.jpg';path='数码网报价单-0710更新/手机配件/'+img
add_rows(img,path,[
('苹果','IPAD PRO(12.9寸) 带小板1代/2代',['内爆'],(2,)),('苹果','IPAD PRO(12.9寸) 不带小板',['内爆'],(2,)),('苹果','IPAD PRO(11寸)',['内爆'],(2,)),('苹果','IPAD PRO(10.5寸)',['内爆'],(2,)),('苹果','IPAD(10.2寸)',['内爆'],(2,)),('苹果','IPAD(9.7寸)',['内爆'],(2,)),('苹果','IPAD7',['内爆'],(2,)),('苹果','IPAD6低配',['内爆'],(0.5,)),('苹果','IPAD6高配',['内爆'],(0.5,)),('苹果','IPAD5低配',['内爆'],(0.5,)),('苹果','IPAD5高配',['内爆'],(0.5,)),('苹果','迷你6',['内爆'],(2,)),('苹果','迷你5',['内爆'],(0.5,)),('苹果','迷你4',['内爆'],(0.5,)),('苹果','迷你2（夏普）组/迷你3（低配）',['内爆'],(0.5,)),('苹果','迷你2（夏普）原/迷你3',['内爆'],(0.5,))],category='手机配件',subtype='平板屏幕')

seen=set();out=[]
for r in rows:
 if r['record_id'] not in seen:seen.add(r['record_id']);out.append(r)
with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
print('2026-07-10 extra rows added; total=%d'%len(out))
