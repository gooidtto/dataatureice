#!/usr/bin/env python3
"""Merge the verified 2026-07 source-image ledger into the callable manifest."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; p=ROOT/'data'/'source_image_manifest.csv'
ADD=[
('2026-07-05','其它','EVD 唱戏机.jpg','数码网报价单-0705更新/5.其它/EVD 唱戏机.jpg','22aaf61853c4844f9a66b9a628475d09bd25cb985fc9d733c0fb7cd2997f2f39','254277'),
('2026-07-05','其它','内存卡.jpg','数码网报价单-0705更新/5.其它/内存卡.jpg','b35d6cbbc9652d464556416585618c574c1c96ca5f1201bdfd0a6c91eed5ace1','101522'),
('2026-07-05','其它','汽车导航模块.jpg','数码网报价单-0705更新/5.其它/汽车导航模块.jpg','d8aabc68b493d2e09142d48209da8741f56b40a20015543a1e592dd9f546748d','99269'),
('2026-07-05','电脑','AMD一体机.jpg','数码网报价单-0705更新/3.电脑以及电脑配件/AMD一体机.jpg','70f90f8b1d454e8ea8676210add4cda4d7e251574d7243213d544ccb9bd5b8f','185187'),
('2026-07-05','电脑','点数CPU.jpg','数码网报价单-0705更新/3.电脑以及电脑配件/点数CPU.jpg','06d6e30493fe79086da572d316b8c72c76880e5639142c8f80956e7a586df257','109900'),
('2026-07-10','其它','内存卡.jpg','数码网报价单-0710更新/其它/内存卡.jpg','4ac9b4bede2975000745ed77f4879ee57a577e363e92041af3dab64fa754e2d7','101436'),
('2026-07-10','其它','儿童手表.jpg','数码网报价单-0710更新/其它/儿童手表.jpg','eccfcb3166b4aff2e60e09820e6c6320238c71cf8dbe470de1d33f88d70e8c8e','130902'),
('2026-07-10','其它','小米音响.jpg','数码网报价单-0710更新/其它/小米音响.jpg','45872e3b8a32e8edff05e4b285fa49b98b64689faa455dcf48ab959c539f9e3d','109241'),
('2026-07-10','其它','ipod.jpg','数码网报价单-0710更新/其它/ipod.jpg','78c9d8046415812cda311264e14935c7e486ecd97e48897e5419e54c1b19c255','169995'),
('2026-07-10','其它','POS机.jpg','数码网报价单-0710更新/其它/POS机.jpg','dbb5324d21efea3d46be14c562c2c0034936e6c28e3f009d801d5e593d24478','167333'),
('2026-07-10','其它','机顶盒.jpg','数码网报价单-0710更新/其它/机顶盒.jpg','89023ae305282cca69ad010e8f2b1279631f2a635c91e6e4bf79b5a457560707','285179'),
('2026-07-10','电脑','苹果笔记本.jpg','数码网报价单-0710更新/电脑以及电脑配件/苹果笔记本.jpg','8ca35d775919258bae00f1e90738e76ef5b4807d8e756574a3d23703f3f91f53','161958'),
('2026-07-10','其它','小度，天猫，小爱.jpg','数码网报价单-0710更新/其它/小度，天猫，小爱.jpg','5530c65bc6f538322cfe021e6e9c45c1a5eb5c8129f12eb9b775ac4dd9a39617','112614'),
('2026-07-10','手机配件','ipad内爆屏幕.jpg','数码网报价单-0710更新/手机配件/ipad内爆屏幕.jpg','0bbc20542df9d62d3e0ebaba15b12c4ab66a795f1ddbeae3f303d8f48577e09c','88426'),
]
headers=['include','data_date','category','status','source_path','source_image','sha256','bytes','verification','verification_note']
rows=[]
if p.exists():
 with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
seen={(r.get('data_date',''),r.get('source_image','')) for r in rows}
added=0
for date,cat,img,path,sha,size in ADD:
 if (date,img) not in seen:
  rows.append({'include':'1','data_date':date,'category':cat,'status':'verified','source_path':path,'source_image':img,'sha256':sha,'bytes':size,'verification':'visual_verified_from_uploaded_image','verification_note':'图片内容可可靠识别并已结构化入日期快照'});added+=1
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(rows)
print('SOURCE_MANIFEST_MERGED added=%d total=%d'%(added,len(rows)))
