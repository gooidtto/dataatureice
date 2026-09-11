import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-10','电脑','数码网报价单-0710更新/电脑以及电脑配件/电脑主板.jpg','电脑主板.jpg','f43ea62700249c6fc311e4154f1625bb3ef3109b482bbd205f07a79acf7b3db5','321677'),
('2026-07-10','电脑','数码网报价单-0710更新/电脑以及电脑配件/电脑硬盘.jpg','电脑硬盘.jpg','cbaf11169a4c24828a3cfb17cd0dc4b9eb2d10ae0bdd3115e24b9afb9e24d1e8','243701')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('1',date,cat,'verified',path,img,sha,size,'visual_verified_from_uploaded_image','图片内容可可靠识别并已结构化入日期快照'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_SIXTH_PASS total=%d'%len(rows))
