import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/手机屏幕.jpg','手机屏幕.jpg','91f84fbd4563d8af4bbf62917893f1ca0fecb8b3e56f99a131c23ff1737881f4','113443'),
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/手机摄像头.jpg','手机摄像头.jpg','0b725c4ab437b5266e92caab2f1d5d10532e41a4e534efc99829704c63ca10c0','45114'),
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/废手机主板.jpg','废手机主板.jpg','830ad2954d487c58de0134c8fa624949c10cf1cf5ede7724a56680c81a592f0f','115387'),
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/手机配件.jpg','手机配件.jpg','04d859235e4e9d64fbe7af8eaf8e4afe96eaab769f57edacf50956be98f8b139','84435')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('1',date,cat,'verified',path,img,sha,size,'visual_verified_from_uploaded_image','图片内容可可靠识别；手机配件.jpg与废手机主板.jpg为同表内容，避免重复计价记录'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_NINTH_PASS total=%d'%len(rows))
