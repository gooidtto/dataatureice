import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data'/'source_image_manifest.csv'
h=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
items=[
('2026-07-05','手机配件','数码网报价单-0705更新/2.手机配件/手机主板.jpg','手机主板.jpg','00bd31c9d90ed8e8d3d4c475198223b28dffc99bbcc83370191d5ba2b5e47276','1138785'),
('2026-07-05','其它','数码网报价单-0705更新/5.其它/对讲机.jpg','对讲机.jpg','0e85beab79a3b341a111c31cd0e3d366c168761a9617f373cedd35d33a7506f7','327843'),
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/主板.jpg','主板.jpg','d549fc1559b613029a2e7526dd3d989bf78ba6e3258b4690036be3f3cf24f921','522262'),
('2026-07-10','其它','数码网报价单-0710更新/其它/对讲机.jpg','对讲机.jpg','05833054d77b1da2728618fe982e2646e87544d42492228e813e7b25f5410e92','415878'),
('2026-07-10','其它','数码网报价单-0710更新/其它/摄像头.jpg','摄像头.jpg','d92ce8e4debb3cce01f0c7d7180f35b72481302d4860fb84b648f5274b9fa16d','481387'),
('2026-07-10','电脑','数码网报价单-0710更新/电脑以及电脑配件/显卡.jpg','显卡.jpg','eaded43f64dce2495d31eec538a973e8be05add866d846605adb5ca3e6f756ce','402909'),
('2026-07-10','手机配件','数码网报价单-0710更新/手机配件/苹果主板.jpg','苹果主板.jpg','77eb061d79b2c9853dd3297f3a5794d5c5a1e95d527147835b0151d8c9160226','354719')]
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
for date,cat,path,img,sha,size in items:
 if not any(r.get('data_date')==date and r.get('source_image')==img for r in rows):
  rows.append(dict(zip(h,('0',date,cat,'skipped_unreliable',path,img,sha,size,'manual_visual_review','图片存在且已复核；表格文字过密/过小或无法在当前可靠阈值下完整确定价格型号，按规则不猜测、不写入可调用价格行'))))
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=h);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_TENTH_PASS total=%d'%len(rows))
