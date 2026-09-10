import csv, os, re, sys
ROOT=os.path.dirname(os.path.abspath(__file__))
DATA=os.path.join(ROOT,'data')
REQ={'record_id','data_date','category','subtype','brand','series','model','alias','condition','price','unit','source_image','source_path','verified'}
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}\.csv$')
errors=[]; files=0; rows=0
for name in sorted(os.listdir(DATA)) if os.path.isdir(DATA) else []:
    if not DATE_RE.match(name): continue
    files+=1
    path=os.path.join(DATA,name)
    with open(path,encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        missing=REQ-set(reader.fieldnames or [])
        if missing: errors.append(f'{name}: missing {sorted(missing)}'); continue
        for n,r in enumerate(reader,2):
            rows+=1
            if r.get('data_date')!=name[:10]: errors.append(f'{name}:{n}: data_date mismatch')
            if r.get('verified')!='1': errors.append(f'{name}:{n}: unverified row in runtime data')
            if not r.get('model') or not r.get('condition'): errors.append(f'{name}:{n}: model/condition empty')
            if not r.get('source_path') or not r.get('source_image'): errors.append(f'{name}:{n}: source missing')
            try: float(r.get('price',''))
            except ValueError: errors.append(f'{name}:{n}: nonnumeric price {r.get("price")!r}')
manifest=os.path.join(DATA,'source_image_manifest.csv')
if os.path.isfile(manifest):
    with open(manifest,encoding='utf-8-sig',newline='') as f: m=list(csv.DictReader(f))
    inc=sum(r.get('include')=='1' for r in m); exc=sum(r.get('include')!='1' for r in m)
    if (inc,exc)!=(103,2): errors.append(f'source manifest count expected 103/2, got {inc}/{exc}')
else: errors.append('source_image_manifest.csv missing')
print(f'price snapshot files: {files}; runtime rows: {rows}')
print(f'source images: 103 included / 2 excluded')
if errors:
    print(f'VALIDATION FAILED: {len(errors)} errors')
    for e in errors[:100]: print(' -',e)
    sys.exit(1)
print('VALIDATION OK')
