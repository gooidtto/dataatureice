#!/usr/bin/env python3
import csv, os, re, sys
from collections import Counter

DATE_FILE=re.compile(r'^\d{4}-\d{2}-\d{2}\.csv$')
DATE_DIR=re.compile(r'^\d{4}-\d{2}-\d{2}$')
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
CATS={'手机','手机配件','平板','电脑','其它'}
TRUE={'1','true','yes','verified'}

def clean(v):
    return str(v or '').replace('\ufeff','').replace('\u200b','').replace('\xa0',' ').strip()

def read_csv(p):
    last=None
    for enc in ('utf-8-sig','utf-8','gb18030','gbk'):
        try:
            with open(p,encoding=enc,newline='') as f: return list(csv.DictReader(f))
        except Exception as e: last=e
    raise last

def discover(data_dir):
    out=[]
    if not os.path.isdir(data_dir): return out
    for n in sorted(os.listdir(data_dir)):
        p=os.path.join(data_dir,n)
        if DATE_FILE.fullmatch(n) and os.path.isfile(p): out.append(('root',n[:10],p))
    for root_name in ('snapshots','database'):
        root=os.path.join(data_dir,root_name)
        if os.path.isdir(root):
            for date in sorted(os.listdir(root)):
                dp=os.path.join(root,date)
                if DATE_DIR.fullmatch(date) and os.path.isdir(dp):
                    for n in sorted(os.listdir(dp)):
                        p=os.path.join(dp,n)
                        if n.lower().endswith('.csv') and os.path.isfile(p): out.append((root_name,date,p))
    return out

def normalize_rows(rows,date,path,errors):
    if not rows: return []
    actual=list(rows[0].keys())
    if actual != FIELDS:
        errors.append(f'{path}: schema必须严格为19字段，实际为{len(actual)}字段: {actual}')
        return []
    result=[]
    required=['record_id','data_date','category','subtype','model','condition','price','unit','source_image','source_path','verified']
    for line,r0 in enumerate(rows,2):
        r={k:clean(r0.get(k,'')) for k in FIELDS}
        if r['data_date']!=date: errors.append(f'{path}:{line}: data_date={r["data_date"]!r} 与快照 {date} 不一致')
        if r['category'] not in CATS: errors.append(f'{path}:{line}: 非标准分类 {r["category"]!r}')
        for f in required:
            if not r[f]: errors.append(f'{path}:{line}: {f}为空')
        if r['verified'].lower() not in TRUE: errors.append(f'{path}:{line}: verified={r["verified"]!r}')
        result.append(r)
    return result

def validate_unique(rows,date,label,errors):
    ids=Counter(r['record_id'] for r in rows if r['record_id'])
    dups={k:v for k,v in ids.items() if v>1}
    if dups: errors.append(f'{date}: {label} 跨分片 record_id重复 {sum(v-1 for v in dups.values())} 行 / {len(dups)} 个ID')

def row_tuple(r): return tuple(r.get(f,'') for f in FIELDS)

def validate(data_dir):
    errors=[];warnings=[];files=discover(data_dir)
    if not files: return ['未找到价格快照'],warnings,[]
    by_source_date={}
    for source,date,path in files: by_source_date.setdefault((source,date),[]).append(path)
    source_rows={}
    for (source,date),paths in sorted(by_source_date.items()):
        combined=[]
        for path in paths:
            try: rows=read_csv(path)
            except Exception as e: errors.append(f'{path}: CSV读取失败: {e}');continue
            if not rows: warnings.append(f'{path}: 空快照分片');continue
            combined.extend(normalize_rows(rows,date,path,errors))
        validate_unique(combined,date,source,errors)
        source_rows[(source,date)]=combined
    dates=sorted(set(date for _,date,_ in files));all_rows=[]
    for date in dates:
        db=source_rows.get(('database',date),[]);snapshots=source_rows.get(('snapshots',date),[]);root=source_rows.get(('root',date),[])
        canonical=db or root or snapshots
        if db and snapshots and sorted(row_tuple(r) for r in db)!=sorted(row_tuple(r) for r in snapshots): errors.append(f'{date}: database 与 snapshots 的19字段记录集不一致')
        all_rows.extend(canonical)
    mp=os.path.join(data_dir,'source_image_manifest.csv')
    if not os.path.isfile(mp): errors.append('缺失 source_image_manifest.csv')
    else:
        try: manifest=read_csv(mp)
        except Exception as e: errors.append(f'来源清单读取失败: {e}');manifest=[]
        included={(clean(r.get('data_date')),clean(r.get('source_image'))) for r in manifest if clean(r.get('include')).lower() in TRUE}
        data_sources={(r['data_date'],r['source_image']) for r in all_rows}
        for item in sorted(data_sources-included): errors.append(f'数据来源未在清单纳入: {item[0]} / {item[1]}')
        for item in sorted(included-data_sources): warnings.append(f'清单纳入但当前无价格行: {item[0]} / {item[1]}')
    return errors,warnings,all_rows

def main():
    e,w,rows=validate(sys.argv[1] if len(sys.argv)>1 else 'data');print(f'ROWS={len(rows)}');print(f'ERRORS={len(e)} WARNINGS={len(w)}')
    for x in e: print('ERROR:',x)
    for x in w: print('WARN:',x)
    return 1 if e else 0
if __name__=='__main__': raise SystemExit(main())
