#!/usr/bin/env python3
import csv, os, re, sys
from collections import Counter
DATE_FILE=re.compile(r'^\d{4}-\d{2}-\d{2}\.csv$')
DATE_DIR=re.compile(r'^\d{4}-\d{2}-\d{2}$')
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
CATS={'手机','平板','电脑','其它'}
TRUE={'1','true','yes','verified'}
def clean(v): return str(v or '').replace('\ufeff','').replace('\u200b','').replace('\xa0',' ').strip()
def read_csv(p):
    last=None
    for enc in ('utf-8-sig','utf-8','gb18030','gbk'):
        try:
            with open(p,encoding=enc,newline='') as f:return list(csv.DictReader(f))
        except Exception as e:last=e
    raise last
def discover(data_dir):
    out=[]
    if not os.path.isdir(data_dir): return out
    for n in sorted(os.listdir(data_dir)):
        p=os.path.join(data_dir,n)
        if DATE_FILE.fullmatch(n) and os.path.isfile(p): out.append((n[:10],p))
    root=os.path.join(data_dir,'snapshots')
    if os.path.isdir(root):
        for date in sorted(os.listdir(root)):
            dp=os.path.join(root,date)
            if DATE_DIR.fullmatch(date) and os.path.isdir(dp):
                for n in sorted(os.listdir(dp)):
                    p=os.path.join(dp,n)
                    if n.lower().endswith('.csv') and os.path.isfile(p): out.append((date,p))
    return out
def validate(data_dir):
    errors=[];warnings=[];all_rows=[];files=discover(data_dir)
    if not files: errors.append('未找到价格快照'); return errors,warnings,all_rows
    by_date={}
    for date,path in files: by_date.setdefault(date,[]).append(path)
    for date,paths in sorted(by_date.items()):
        ids=Counter()
        for path in paths:
            try: rows=read_csv(path)
            except Exception as e: errors.append(f'{path}: CSV读取失败: {e}'); continue
            if not rows: warnings.append(f'{path}: 空快照分片'); continue
            missing=[f for f in FIELDS if f not in rows[0]]
            if missing: errors.append(f'{path}: 缺少字段 {missing}'); continue
            for line,r0 in enumerate(rows,2):
                r={k:clean(r0.get(k,'')) for k in FIELDS};all_rows.append(r)
                if r['data_date']!=date: errors.append(f'{path}:{line}: data_date={r["data_date"]!r} 与快照 {date} 不一致')
                if r['category'] not in CATS: errors.append(f'{path}:{line}: 非标准分类 {r["category"]!r}')
                for f in ('record_id','model','condition','price','unit','source_image','source_path'):
                    if not r[f]: errors.append(f'{path}:{line}: {f}为空')
                if r['verified'].lower() not in TRUE: errors.append(f'{path}:{line}: verified={r["verified"]!r}')
                if r['record_id']: ids[r['record_id']]+=1
        dups={k:v for k,v in ids.items() if v>1}
        if dups: errors.append(f'{date}: record_id重复 {sum(v-1 for v in dups.values())} 行 / {len(dups)} 个ID（跨分片合并检查）')
    mp=os.path.join(data_dir,'source_image_manifest.csv')
    if not os.path.isfile(mp): errors.append('缺失 source_image_manifest.csv')
    else:
        try: manifest=read_csv(mp)
        except Exception as e: errors.append(f'来源清单读取失败: {e}'); manifest=[]
        included={(clean(r.get('data_date')),clean(r.get('source_image'))) for r in manifest if clean(r.get('include')).lower() in TRUE}
        data_sources={(r['data_date'],r['source_image']) for r in all_rows}
        for item in sorted(data_sources-included): errors.append(f'数据来源未在清单纳入: {item[0]} / {item[1]}')
        for item in sorted(included-data_sources): warnings.append(f'清单纳入但当前无价格行: {item[0]} / {item[1]}')
    return errors,warnings,all_rows
def main():
    e,w,rows=validate(sys.argv[1] if len(sys.argv)>1 else 'data')
    print(f'ROWS={len(rows)}');print(f'ERRORS={len(e)} WARNINGS={len(w)}')
    for x in e: print('ERROR:',x)
    for x in w: print('WARN:',x)
    return 1 if e else 0
if __name__=='__main__': raise SystemExit(main())
