import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-05','其它','数码网报价单-0705更新/5.其它/POS机.jpg','POS机.jpg','a68b35ea0cb9f801a2ce6e37433e901aaaa15ff4db68fce744ddf775ead70be4','246738'),
('2026-07-05','其它','数码网报价单-0705更新/5.其它/机顶盒.jpg','机顶盒.jpg','7971327be6adc479a89bbda5cff66b80ecfb8e295344c94ee7dfd909f555421f','263318'),
('2026-07-05','其它','数码网报价单-0705更新/5.其它/身份证阅读器.jpg','身份证阅读器.jpg','c32cfab3d66fbed73f5580ecb705590256164841ee0ccc63e4266a4bf10b86e6','212628')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('1',date,cat,'verified',path,img,sha,size,'visual_verified_from_uploaded_image','图片内容可可靠识别并已结构化入日期快照'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_FOURTH_PASS total=%d'%len(rows))
