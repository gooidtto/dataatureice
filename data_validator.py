#!/usr/bin/env python3
"""Validate image-first price snapshots before packaging/building."""
import csv, os, re, sys
from collections import Counter
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}\.csv$')
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
CATS={'手机','平板','电脑','其它'}
TRUE={'1','true','yes','verified'}
def clean(v): return str(v or '').replace('\ufeff','').strip()
def read_csv(path):
    last=None
    for enc in ('utf-8-sig','utf-8','gb18030','gbk'):
        try:
            with open(path,encoding=enc,newline='') as f: return list(csv.DictReader(f))
        except Exception as e: last=e
    raise last
def validate(data_dir):
    errors=[]; warnings=[]; all_rows=[]; files=[]
    for n in os.listdir(data_dir) if os.path.isdir(data_dir) else []:
        p=os.path.join(data_dir,n)
        if DATE_RE.match(n) and os.path.isfile(p): files.append((n[:10],p))
    shard_root=os.path.join(data_dir,'snapshots')
    if os.path.isdir(shard_root):
        for date in os.listdir(shard_root):
            dp=os.path.join(shard_root,date)
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}',date) and os.path.isdir(dp):
                for n in os.listdir(dp):
                    if n.lower().endswith('.csv') and os.path.isfile(os.path.join(dp,n)): files.append((date,os.path.join(dp,n)))
    if not files: errors.append('未找到 YYYY-MM-DD.csv 或 snapshots/YYYY-MM-DD/*.csv')
    for date,path in sorted(files):
        try: rows=read_csv(path)
        except Exception as e: errors.append(f'{date}: CSV读取失败: {e}'); continue
        missing=[f for f in FIELDS if f not in (rows[0].keys() if rows else [])]
        if missing: errors.append(f'{date}: 缺少字段 {missing}'); continue
        ids=Counter(); exact=Counter()
        for i,r in enumerate(rows,2):
            r={k:clean(r.get(k,'')) for k in FIELDS}; all_rows.append(r); ids[r['record_id']]+=1; exact[tuple(r[k] for k in FIELDS)]+=1
            if r['data_date'] != date: errors.append(f'{date}:{i}: data_date与快照日期不一致')
            if r['category'] not in CATS: errors.append(f'{date}:{i}: 非标准分类 {r["category"]!r}')
            for f in ('model','condition','price','unit','source_image','source_path'):
                if not r[f]: errors.append(f'{date}:{i}: {f}为空')
            if r['verified'].lower() not in TRUE: errors.append(f'{date}:{i}: verified={r["verified"]!r}')
        dups={k:v for k,v in ids.items() if k and v>1}
        if dups: errors.append(f'{date}: record_id重复 {sum(v-1 for v in dups.values())} 行 / {len(dups)} 个ID')
        exact_dups=sum(v-1 for v in exact.values() if v>1)
        if exact_dups: warnings.append(f'{date}: 完全重复数据行 {exact_dups} 行')
    mp=os.path.join(data_dir,'source_image_manifest.csv')
    if os.path.isfile(mp):
        manifest=read_csv(mp); included=[r for r in manifest if clean(r.get('include')).lower() in TRUE]
        inc={(clean(r.get('data_date')),clean(r.get('source_image'))) for r in included}; data={(r['data_date'],r['source_image']) for r in all_rows}
        for r in included:
            if not clean(r.get('data_date')) or not clean(r.get('source_image')): errors.append('来源清单: 纳入项缺少日期或图片名')
        for k in sorted(data-inc): errors.append(f'数据来源未在清单纳入: {k[0]} / {k[1]}')
        for r in included:
            k=(clean(r.get('data_date')),clean(r.get('source_image')))
            if clean(r.get('status')).lower()=='verified' and k not in data: errors.append(f'清单标记verified但无数据: {k[0]} / {k[1]}')
    else: warnings.append('未找到 source_image_manifest.csv；跳过图片来源覆盖检查')
    return errors,warnings,all_rows
def main():
    e,w,rows=validate(sys.argv[1] if len(sys.argv)>1 else 'data')
    print(f'ROWS={len(rows)}'); print(f'ERRORS={len(e)} WARNINGS={len(w)}')
    for x in e: print('ERROR:',x)
    for x in w: print('WARN:',x)
    return 1 if e else 0
if __name__=='__main__': raise SystemExit(main())
