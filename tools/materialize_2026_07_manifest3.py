import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-05','其它','数码网报价单-0705更新/其它/扫描枪.jpg','扫描枪.jpg','8d3095b5e4808f20e3e437e5cde7026af9586db7b5b841d30b68e99446f7ae7a','373086'),
('2026-07-10','电脑','数码网报价单-0710更新/电脑以及电脑配件/台式机主板.jpg','台式机主板.jpg','8cf5719419201033e5aa13f1479708b38a725f26a4ab635dd5432a221635c8ee','275156'),
('2026-07-10','电脑','数码网报价单-0710更新/电脑以及电脑配件/老款一体机.jpg','老款一体机.jpg','db964f8958278c6c9813879fb675bf92f2aa53ecb96c15cc172d221e35e20d79','122394')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('1',date,cat,'verified',path,img,sha,size,'visual_verified_from_uploaded_image','图片内容可可靠识别并已结构化入日期快照'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_THIRD_PASS total=%d'%len(rows))
