import csv,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
def add(d,img,path,cat,sub,b,m,rows,u='元/台'):
 p=R/'data'/(d+'.csv');old=list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''))) if p.exists() else [];seen={x['record_id'] for x in old}
 for c,v in rows:
  x={k:'' for k in F};x.update(data_date=d,category=cat,subtype=sub,brand=b,series=b,model=m,condition=c,price=str(v),unit=u,origin='image',source_image=img,source_path=path,verified='1',confidence='1.0',verification='visual_verified_from_uploaded_image');x['record_id']=hashlib.sha256('|'.join(x.get(k,'') for k in ('data_date','category','subtype','brand','series','model','condition','price','unit')).encode()).hexdigest()[:16]
  if x['record_id'] not in seen:seen.add(x['record_id']);old.append(x)
 with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=F);w.writeheader();w.writerows(old)
d='2026-07-05';img='光猫.jpg';path='数码网报价单-0705更新/5.其它/光猫.jpg'
for m,v in [('华为8346x6',80),('华为8546V',50),('华为HS8546V2 GPON',50),('华为8145V GPON',13),('华为8145V EPON',13),('HG8546V',13),('hs8545m',15),('HS8346R5',15),('HS8545M5 GPON',13),('HS8545M GPON',13),('HS8145C5 GPON',13),('8546M GPON',13),('HS8145C5 EPON',13),('HG8010',5),('吉比特HG8310M',13),('F677V2',8),('F6979AV',10),('中兴F673A V3a',12),('中兴F673A V2 GPON',10),('6821M',10),('中兴F650双天线',4),('HN8346X6-C',17),('H2-2',11),('中国移动ZN-M142G',6),('中国移动H61G',6),('HG6145D',5),('光纤猫',8),('光纤猫芯片',6)]:add(d,img,path,'其它','光猫','通用',m,[('点数',v)])
d='2026-07-10';img='光纤猫.jpg';path='数码网报价单-0710更新/其它/光纤猫.jpg'
for m,v in [('华为8346x6',80),('华为8546V',50),('华为HS8546V2 GPON',50),('华为8145V GPON',13),('华为8145V EPON',13),('HG8546V',13),('hs8545m',15),('HS8346R5',15),('HS8545M5 GPON',13),('HS8545M GPON',13),('HS8145C5 GPON',13),('HS8145C5 EPON',13),('8546M GPON',13),('HG8010',5),('吉比特HG8310M',13),('F677V2',8),('F6979AV',10),('中兴F673A V3a',12),('中兴F673A V2 GPON',10),('6821M',10),('中兴F650双天线',4),('HN8346X6-C',7),('H2-2',11),('中国移动ZN-M142G',6),('中国移动H61G',6),('HG6145D',5)]:add(d,img,path,'其它','光猫','通用',m,[('点数',v)])
d='2026-07-10';img='EVD和唱戏机.jpg';path='数码网报价单-0710更新/其它/EVD和唱戏机.jpg'
for m,a,b in [('7-8寸屏',5,3),('9-10寸屏',13,3),('12寸/14寸以上',13,3),('进口原装7寸屏以上',6,3),('8.9寸唱戏机',3,3),('4.3寸唱戏机',5,3),('7寸唱戏机',9,3),('9寸唱戏机',13,3),('10.1寸唱戏机',13,3),('佳佳机9寸',12,3),('佳佳机7寸',10,3)]:add(d,img,path,'其它','EVD/唱戏机','通用',m,[('屏好',a),('屏坏',b)])
d='2026-07-10';img='身份证阅读器.jpg';path='数码网报价单-0710更新/其它/身份证阅读器.jpg'
for m,v in [('13年身份证模块',80),('身份证模块',80),('24年身份证模块',420),('19年身份证模块',220),('18年身份证模块',200),('13、14年以下身份证模块',190),('0513 24年身份证模块',1),('0503 2011-2012年身份证模块',0),('0513 17年-18年身份证模块',430),('0513 19年-20年身份证模块',430),('0513 23年身份证模块',480),('坏身份证阅读器',5)]:add(d,img,path,'其它','身份证阅读器','通用',m,[('正常',v)],'元/个')
d='2026-07-05';img='电池.jpg';path='数码网报价单-0705更新/5.其它/电池.jpg'
for m,v,u in [('原装品牌电池',44,'元/个'),('品牌电池',15,'元/个'),('杂牌电池',15,'元/个'),('软电池双排线双电芯',52,'元/斤'),('vivo Y31电池',8,'元/个'),('非品牌智能机电池',20,'元/个'),('老年机电池',1,'元/个'),('14系列苹果电池',6,'元/斤'),('7系列苹果电池',1.8,'元/斤'),('6系列苹果电池',1.8,'元/斤'),('ipad电池',13,'元/斤'),('汽车动力电池18650',1.5,'元/个'),('汽车动力电池18650废电池',3,'元/斤'),('铁锂电池',3,'元/斤'),('充电宝',5,'元/斤')]:add(d,img,path,'其它','电池','通用',m,[('正常',v)],u)
