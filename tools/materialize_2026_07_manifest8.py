import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/苹果内爆屏幕.jpg','苹果内爆屏幕.jpg','dc0ad9ac7f5baa07bf036ca9b2f38b2dffac5fa02d45bd2d78361d418514efbc','121368'),
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/电池.jpg','电池.jpg','39933701950b1920061472e3be32b437ae94ea9790eb0296e301c52c1ec14c1f','138382')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('1',date,cat,'verified',path,img,sha,size,'visual_verified_from_uploaded_image','图片内容可可靠识别并已结构化入日期快照'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_EIGHTH_PASS total=%d'%len(rows))
