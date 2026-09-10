#!/usr/bin/env python3
"""Validate callable image-first snapshots, then stage them into data/."""
from pathlib import Path
import csv, shutil

ROOT=Path(__file__).resolve().parents[1]
SRC=Path('/mnt/data/callable_data')
DST=ROOT/'data'
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
DATE_FILES=('2026-08-25.csv','2026-08-31.csv')
CATS={'手机','平板','电脑','其它'}
TRUE={'1','true','yes','verified'}

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def validate():
    errors=[]
    for name in DATE_FILES:
        p=SRC/name
        if not p.exists(): errors.append(f'缺失 {name}'); continue
        rows=read(p)
        if not rows: errors.append(f'{name}: 空数据'); continue
        ids=set()
        if list(rows[0].keys())!=FIELDS: errors.append(f'{name}: 字段顺序/集合不符')
        for i,r in enumerate(rows,2):
            if r['data_date']!=name[:10]: errors.append(f'{name}:{i}: 日期不一致')
            if r['category'] not in CATS: errors.append(f'{name}:{i}: 分类无效 {r["category"]!r}')
            for f in ('record_id','model','condition','price','unit','source_image','source_path'):
                if not r[f]: errors.append(f'{name}:{i}: {f}为空')
            if r['verified'].lower() not in TRUE: errors.append(f'{name}:{i}: verified无效')
            if r['record_id'] in ids: errors.append(f'{name}:{i}: record_id重复 {r["record_id"]}')
            ids.add(r['record_id'])
    m=SRC/'source_image_manifest.csv'
    if not m.exists(): errors.append('缺失 source_image_manifest.csv')
    else:
        manifest=read(m)
        included={(r.get('data_date',''),r.get('source_image','')) for r in manifest if r.get('include') in {'1','true','yes','verified'}}
        data=set()
        for name in DATE_FILES:
            p=SRC/name
            if p.exists(): data |= {(r['data_date'],r['source_image']) for r in read(p)}
        for item in sorted(data-included): errors.append(f'数据来源未在清单纳入 {item}')
    return errors

def main():
    errors=validate()
    if errors:
        print('\n'.join('ERROR '+e for e in errors)); return 1
    DST.mkdir(parents=True,exist_ok=True)
    for name in (*DATE_FILES,'source_image_manifest.csv'): shutil.copy2(SRC/name,DST/name)
    print('CALLABLE_DATA_OK')
    return 0
if __name__=='__main__': raise SystemExit(main())
