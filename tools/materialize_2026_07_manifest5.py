import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-10','其它','数码网报价单-0710更新/其它/方盒子路由器.jpg','方盒子路由器.jpg','884eab57529174fed2fd5441c2d4d460a00ac2fe2ef047f82f076b3675f80fef','191959'),
('2026-07-10','电脑','数码网报价单-0710更新/电脑以及电脑配件/台式机光驱.jpg','台式机光驱.jpg','36bb208b6db2da0505f158286628d05abd4fb5ab5a13d07f54cc1d154197c9f6','85070'),
('2026-07-10','电脑','数码网报价单-0710更新/电脑以及电脑配件/显示器.jpg','显示器.jpg','40e5966deff7123815afccd20b3ddbe114b8d3e60d1599f7c1d05f85d040257f','136949')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('1',date,cat,'verified',path,img,sha,size,'visual_verified_from_uploaded_image','图片内容可可靠识别并已结构化入日期快照'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_FIFTH_PASS total=%d'%len(rows))
