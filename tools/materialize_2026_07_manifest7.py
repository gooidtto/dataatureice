import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-05','手机配件','数码网报价单-0705更新/2.手机配件/手机屏幕2.jpg','手机屏幕2.jpg','183df19f6f80f5fbb2fb98dfbe23d981c343c17cad133a0a3683e71b4f578024','111742'),
('2026-07-05','手机配件','数码网报价单-0705更新/2.手机配件/老年机.jpg','老年机.jpg','1c61a94b679fdb3e699e5a927c726494b0a3af39d97b47c9cfdef390d775c098','302697'),
('2026-07-05','手机配件','数码网报价单-0705更新/2.手机配件/苹果手机屏幕.jpg','苹果手机屏幕.jpg','9a24c1ad1dc914019325af6f6a5aa06920464aaf477bc185c7edea315f1ab716','121432')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('1',date,cat,'verified',path,img,sha,size,'visual_verified_from_uploaded_image','图片内容可可靠识别并已结构化入日期快照'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_SEVENTH_PASS total=%d'%len(rows))
