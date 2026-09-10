import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from data_validator import validate
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
def base(**kw):
    r={k:'' for k in FIELDS}; r.update(record_id='id1',data_date='2026-08-31',category='手机',subtype='device',brand='A',series='S',model='M',condition='屏好',price='100',unit='CNY/台',source_image='手机.jpg',source_path='x/手机.jpg',verified='1'); r.update(kw); return r
def write_snapshot(root,rows):
    root.mkdir(parents=True,exist_ok=True)
    with open(root/'2026-08-31.csv','w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    with open(root/'source_image_manifest.csv','w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['include','data_date','category','status','source_path','source_image']); w.writeheader(); w.writerow({'include':'1','data_date':'2026-08-31','category':'手机','status':'verified','source_path':'x/手机.jpg','source_image':'手机.jpg'})
def test_valid(tmp_path):
    write_snapshot(tmp_path,[base()]); e,w,_=validate(str(tmp_path)); assert not e, (e,w)
def test_duplicate_id_fails(tmp_path):
    write_snapshot(tmp_path,[base(),base(condition='屏坏',price='80')]); e,_,_=validate(str(tmp_path)); assert any('record_id重复' in x for x in e)
def test_snapshot_date_mismatch_fails(tmp_path):
    write_snapshot(tmp_path,[base(data_date='2026-08-25')]); e,_,_=validate(str(tmp_path)); assert any('快照日期不一致' in x for x in e)
