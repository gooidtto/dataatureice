import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv';h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note'];x=('1','2026-07-05','其它','verified','数码网报价单-0705更新/5.其它/电池.jpg','电池.jpg','e813d40224db68527d8c861853a2e35abfd44dba6beb793588b8b60b7c2c101f','278409','visual_verified_from_uploaded_image','图片内容可可靠识别并已结构化入日期快照');rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
if not any(r.get('data_date')=='2026-07-05' and r.get('source_image')=='电池.jpg' for r in rows):rows.append(dict(zip(h,x)))
with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_EXTRA total=%d'%len(rows))
