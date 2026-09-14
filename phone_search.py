import csv,json,os,re,subprocess,sys,unicodedata,tkinter as tk
from tkinter import ttk,messagebox,filedialog
try:
 from openpyxl import Workbook
 from openpyxl.styles import Font
 from openpyxl.utils import get_column_letter
except ImportError: Workbook=None
from search_service import SearchService
from storage.csv_repository import CsvRepository
from storage.sqlite_repository import SQLiteRepository
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
COLS=[('data_date','数据日期',105),('category','分类',70),('subtype','子类型',75),('brand','品牌',110),('series','系列',110),('model','型号',250),('condition','价格条件',175),('price','价格',85),('unit','单位',85),('note','备注',260),('source_image','来源图片',150)]
TRUE={'1','true','yes','verified'};CAT={'phone':'手机','tablet':'平板','computer':'电脑','other':'其它','手机':'手机','平板':'平板','电脑':'电脑','其它':'其它','手机配件':'手机配件'}
def clean(v):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC','' if v is None else str(v)).replace('\ufeff','').replace('\u200b','').replace('\xa0',' ')).strip()
def key(v):return re.sub(r'[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+','',clean(v).casefold())
def num(v):
 s=clean(v)
 if not s or '/' in s or s in {'-','—','/'}:return None
 m=re.search(r'[-+]?(?:\d+(?:\.\d+)?|\.\d+)',s)
 try:return float(m.group(0)) if m else None
 except:return None
def read_csv(p):
 last=None
 for e in ('utf-8-sig','utf-8','gb18030','gbk'):
  try:
   with open(p,encoding=e,newline='') as f:return list(csv.DictReader(f))
  except Exception as x:last=x
 raise last
def rid(r):return tuple(key(r.get(x)) for x in ('category','subtype','brand','series','model','model_code'))
def valid(r):return bool(r.get('model') and r.get('condition') and r.get('price') and clean(r.get('verified')).lower() in TRUE)
def normalizeContent(r):
 fields=('category','subtype','brand','series','model','model_code','condition','price','unit');return {f:key(r.get(f,'')) for f in fields}
def generateContentKey(r):return '|'.join(normalizeContent(r)[f] for f in ('category','subtype','brand','series','model','model_code','condition','price','unit'))
class LegacyCsvStore:
 def __init__(self,d):self.d=d;self.rows=[];self.snapshots={};self.manifest=[];self.errors=[]
 def load(self):
  self.rows=[];self.snapshots={};self.manifest=[];self.errors=[];files=[]
  if os.path.isdir(self.d):
   for n in os.listdir(self.d):
    p=os.path.join(self.d,n)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}\.csv',n,re.I) and os.path.isfile(p):files.append((n[:10],p))
  sd=os.path.join(self.d,'snapshots')
  if os.path.isdir(sd):
   for d in os.listdir(sd):
    dp=os.path.join(sd,d)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',d) and os.path.isdir(dp):files += [(d,os.path.join(dp,n)) for n in sorted(os.listdir(dp)) if n.lower().endswith('.csv')]
  groups={}
  for d,p in files:groups.setdefault(d,[]).append(p)
  for d,paths in groups.items():
   data=[];seen=set()
   for p in paths:
    try:rows=read_csv(p)
    except Exception as e:self.errors.append(f'{d}: {e}');continue
    for raw in rows:
     r={k:clean(raw.get(k,'')) for k in FIELDS};r['category']=CAT.get(r['category'],r['category'])
     if r['data_date']!=d:self.errors.append(f'{d}: data_date不一致')
     if r['category'] not in CAT.values():self.errors.append(f'{d}: 非标准分类 {r["category"]}')
     if not valid(r):continue
     if r['record_id'] in seen:self.errors.append(f'{d}: 重复 record_id {r["record_id"]}');continue
     seen.add(r['record_id']);data.append(r)
   self.snapshots[d]=data;self.rows.extend(data)
  mp=os.path.join(self.d,'source_image_manifest.csv')
  if os.path.isfile(mp):
   try:self.manifest=read_csv(mp)
   except Exception as e:self.errors.append(f'来源清单: {e}')
 @property
 def dates(self):return sorted(self.snapshots)
 @property
 def latest(self):return self.dates[-1] if self.dates else ''
 def _sort(self,rs):
  def p(r):
   n=num(r['price']);return -n if n is not None else float('inf')
  return sorted(rs,key=lambda r:(-int(r['data_date'].replace('-','')),p(r),r['brand'],r['series'],r['model'],r['condition'],r['record_id']))
 def search(self,q='',cat='全部'):return self._sort([r for r in self.rows if (cat=='全部' or r['category']==cat) and (not key(q) or key(q) in key(' '.join(r.get(x,'') for x in ('brand','series','model','model_code','alias','source_image'))))])
 def history(self,targets):return self._sort([r for r in self.rows if tuple(key(r.get(x)) for x in ('category','subtype','brand','series','model')) in {tuple(key(t.get(x)) for x in ('category','subtype','brand','series','model')) for t in targets}])
class JsonList:
 MAX_ITEMS=50
 def __init__(self,p):self.p=p;self.items=[];self.load()
 def load(self):
  try:
   with open(self.p,encoding='utf-8') as f:x=json.load(f)
   self.items=x if isinstance(x,list) else []
  except Exception:self.items=[]
  self.items=self.dedupe()
 def dedupe(self):
  out=[];seen=set()
  for x in self.items:
   if isinstance(x,str):
    x=clean(x);k=key(x)
    if k and k not in seen:seen.add(k);out.append(x)
  return out[:self.MAX_ITEMS]
 def add(self,q):
  q=clean(q)
  if not q:return
  k=key(q);self.items=[x for x in self.dedupe() if key(x)!=k];self.items.insert(0,q);self.items=self.items[:self.MAX_ITEMS];self.save()
 def suggestions(self,q='',limit=5):
  qk=key(q);out=[]
  for x in self.dedupe():
   if not qk or qk in key(x):out.append(x)
   if len(out)>=max(0,limit):break
  return out
 def save(self):
  parent=os.path.dirname(self.p)
  if parent:os.makedirs(parent,exist_ok=True)
  tmp=self.p+'.tmp'
  with open(tmp,'w',encoding='utf-8') as f:json.dump(self.items,f,ensure_ascii=False,indent=2)
  os.replace(tmp,self.p)
 def clear(self):
  self.items=[]
  try:os.remove(self.p)
  except FileNotFoundError:pass
class Favorites:
 MAX_ITEMS=200
 def __init__(self,p):self.p=p;self.items=[];self.load()
 def identity(self,r):return generateContentKey(r)
 def load(self):
  try:
   with open(self.p,encoding='utf-8') as f:x=json.load(f)
   self.items=x if isinstance(x,list) else []
  except Exception:self.items=[]
  self.items=self.dedupe()
 def dedupe(self):
  out=[];seen=set()
  for r in self.items:
   if not isinstance(r,dict) or not r.get('model'):continue
   k=self.identity(r)
   if k not in seen:seen.add(k);out.append(r)
  return out[:self.MAX_ITEMS]
 def has(self,r):return any(self.identity(x)==self.identity(r) for x in self.items)
 def add(self,rows):
  added=[];duplicate=[];cur=self.dedupe();seen={self.identity(r) for r in cur}
  for r in rows:
   k=self.identity(r)
   if k in seen:duplicate.append(r);continue
   cur.insert(0,dict(r));seen.add(k);added.append(r)
  self.items=cur[:self.MAX_ITEMS]
  if added:self.save()
  return added,duplicate
 def remove(self,rows):
  ks={self.identity(r) for r in rows};self.items=[r for r in self.dedupe() if self.identity(r) not in ks];self.save()
 def save(self):
  parent=os.path.dirname(self.p)
  if parent:os.makedirs(parent,exist_ok=True)
  tmp=self.p+'.tmp'
  with open(tmp,'w',encoding='utf-8') as f:json.dump(self.items, f, ensure_ascii=False, indent=2)
  os.replace(tmp,self.p)
