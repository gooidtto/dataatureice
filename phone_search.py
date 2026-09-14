import csv,json,os,re,subprocess,sys,unicodedata,tkinter as tk
from tkinter import ttk,messagebox,filedialog
try:
 from openpyxl import Workbook
except ImportError: Workbook=None
from search_service import SearchService
from storage.csv_repository import CsvRepository
from storage.sqlite_repository import SQLiteRepository
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
COLS=[('data_date','数据日期',105),('category','分类',70),('subtype','子类型',75),('brand','品牌',110),('series','系列',110),('model','型号',250),('condition','价格条件',175),('price','价格',85),('unit','单位',85),('note','备注',260),('source_image','来源图片',150)]
TRUE={'1','true','yes','verified'}
CAT={'phone':'手机','tablet':'平板','computer':'电脑','other':'其它','手机':'手机','平板':'平板','电脑':'电脑','其它':'其它','手机配件':'手机配件'}
def clean(v): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC','' if v is None else str(v)).replace('\ufeff','').replace('\u200b','').replace('\xa0',' ')).strip()
def key(v): return re.sub(r'[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+','',clean(v).casefold())
def num(v):
 s=clean(v)
 if not s or '/' in s or s in {'-','—','/'}: return None
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
def rid(r): return tuple(key(r.get(x)) for x in ('category','subtype','brand','series','model','model_code'))
def valid(r): return bool(r.get('model') and r.get('condition') and r.get('price') and clean(r.get('verified')).lower() in TRUE)
def normalizeContent(r):
 fields=('category','subtype','brand','series','model','model_code','condition','price','unit')
 return {f:key(r.get(f,'')) for f in fields}
def generateContentKey(r): return '|'.join(normalizeContent(r)[f] for f in ('category','subtype','brand','series','model','model_code','condition','price','unit'))
class LegacyCsvStore:
 def __init__(self,d): self.d=d;self.rows=[];self.snapshots={};self.manifest=[];self.errors=[]
 def load(self):
  repo=CsvRepository(self.d,fields=tuple(FIELDS),category_map=CAT,clean=clean,read_csv=read_csv,valid=valid)
  self.rows,self.snapshots,self.errors=repo.load();self.manifest=list(repo.manifest or [])
class JsonList:
 MAX_ITEMS=50
 def __init__(self,p): self.p=p;self.items=[];self.load()
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
  self.items=[x for x in self.dedupe() if key(x)!=key(q)];self.items.insert(0,q);self.items=self.items[:self.MAX_ITEMS];self.save()
 def suggestions(self,q='',limit=5):
  qk=key(q);return [x for x in self.dedupe() if not qk or qk in key(x)][:limit]
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
   cur.append(dict(r));seen.add(k);added.append(r)
  self.items=cur[:self.MAX_ITEMS]
  if added:self.save()
  return added,duplicate
 def remove(self,rows):
  ks={self.identity(r) for r in rows};self.items=[r for r in self.dedupe() if self.identity(r) not in ks];self.save()
 def save(self):
  parent=os.path.dirname(self.p)
  if parent:os.makedirs(parent,exist_ok=True)
  tmp=self.p+'.tmp'
  with open(tmp,'w',encoding='utf-8') as f:json.dump(self.items,f,ensure_ascii=False,indent=2)
  os.replace(tmp,self.p)
class Store:
 def __init__(self,d,repository=None,search_service=None):
  self.d=d
  if repository is not None:self.repository=repository
  elif os.path.isfile(os.path.join(d,'search.sqlite3')):self.repository=SQLiteRepository(os.path.join(d,'search.sqlite3'))
  else:self.repository=LegacyCsvStore(d)
  self.search_service=search_service or SearchService([]);self.rows=[];self.snapshots={};self.manifest=[];self.errors=[]
 def load(self):
  result=self.repository.load()
  if result is not None:self.rows,self.snapshots,self.errors=result
  else:
   self.rows=list(getattr(self.repository,'rows',getattr(self.repository,'_rows',[])));self.snapshots=dict(getattr(self.repository,'snapshots',getattr(self.repository,'_snapshots',{})));self.errors=list(getattr(self.repository,'errors',getattr(self.repository,'_errors',[])))
  self.rows=[dict(r) for r in self.rows];self.snapshots={k:[dict(r) for r in v] for k,v in self.snapshots.items()};self.manifest=list(getattr(self.repository,'manifest',[]) or []);self.search_service.replace_rows(self.rows)
 @property
 def dates(self):return sorted(self.snapshots)
 @property
 def latest(self):return self.dates[-1] if self.dates else ''
 def search(self,q='',cat='全部'):return self.search_service.search(q,cat)
 def history(self,targets):
  targets=list(targets or []);base={tuple(key(t.get(x)) for x in ('category','subtype','brand','series','model')) for t in targets};target_by_date={}
  for t in targets:
   b=tuple(key(t.get(x)) for x in ('category','subtype','brand','series','model'));d=clean(t.get('data_date'));c=key(t.get('model_code'))
   if c:target_by_date.setdefault((b,d),set()).add(c)
  out=[]
  for r in self.rows:
   b=tuple(key(r.get(x)) for x in ('category','subtype','brand','series','model'))
   if b not in base:continue
   d=clean(r.get('data_date'));c=key(r.get('model_code'));allowed=target_by_date.get((b,d))
   if allowed and c not in allowed:continue
   out.append(r)
  return sorted(out,key=lambda r:(-int(str(r.get('data_date','0000-00-00')).replace('-','') or 0),-(num(r.get('price')) or float('-inf')),r.get('brand',''),r.get('series',''),r.get('model',''),r.get('condition',''),r.get('record_id','')))
class App:
 def __init__(self,root):
  self.root=root;root.title('数码回收价格秒查工具 · 图片事实库版');self.fit_main_window();root.resizable(True,True);self.base=os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__));self.d=os.path.join(self.base,'data');os.makedirs(self.d,exist_ok=True);self.s=Store(self.d);self.h=JsonList(os.path.join(self.d,'search_history.json'));self.fav=Favorites(os.path.join(self.d,'favorites.json'));self.rows=[];self.map={};self.suggest_popup=None;self.setup();self.ui();self.load()
 def fit_main_window(self):
  self.root.update_idletasks();sw,sh=self.root.winfo_screenwidth(),self.root.winfo_screenheight();w=min(1720,max(1050,int(sw*.92)));h=min(930,max(620,int(sh*.88)));w=min(w,sw-24);h=min(h,sh-48);self.root.minsize(min(1250,w),min(720,h));self.root.geometry(f'{w}x{h}+{max(12,(sw-w)//2)}+{max(12,(sh-h)//2)}')
 def setup(self):
  st=ttk.Style(self.root);st.configure('T.Treeview',font=('微软雅黑',10),rowheight=32);st.configure('T.Treeview.Heading',font=('微软雅黑',11,'bold'));st.configure('TButton',font=('微软雅黑',10))
 def ui(self):
  top=ttk.Frame(self.root,padding=10);top.pack(fill='x');ttk.Label(top,text='🔍 品牌 / 系列 / 型号 / 别名',font=('微软雅黑',11,'bold')).pack(side='left');self.q=tk.StringVar();self.entry=tk.Entry(top,textvariable=self.q,font=('微软雅黑',14),width=34);self.entry.pack(side='left',padx=(10,2),ipady=4);self.entry.bind('<Return>',lambda e:self.search());self.cat=tk.StringVar(value='全部');ttk.Combobox(top,textvariable=self.cat,values=['全部','手机','平板','电脑','其它','手机配件'],state='readonly',width=8).pack(side='left',padx=4)
  for t,c in [('×',self.clear_search),('🔍',self.search),('查询',self.search),('🔄刷新',self.load),('📁数据目录',self.open_dir),('🧾来源结构',self.sources),('⭐收藏',self.show_favorites)]:ttk.Button(top,text=t,command=c).pack(side='left',padx=4)
  self.status=ttk.Label(top,text='');self.status.pack(side='right');info=ttk.Frame(self.root,padding=(10,0,10,8));info.pack(fill='x');self.target=ttk.Label(info,text='输入品牌、系列、型号开始查询',font=('微软雅黑',11,'bold'));self.target.pack(side='left');self.meta=ttk.Label(info,text='');self.meta.pack(side='right');act=ttk.Frame(self.root,padding=(10,0,10,8));act.pack(fill='x');ttk.Button(act,text='☆ 一键收藏',command=self.add_favorite).pack(side='left',padx=4);ttk.Label(act,text='搜索区只展示；收藏区负责选择与操作').pack(side='right');f=ttk.Frame(self.root);f.pack(fill='both',expand=True,padx=10);self.tree=ttk.Treeview(f,columns=[x[0] for x in COLS]+['favorite'],show='headings',selectmode='none');[self.tree.heading(c,text=h) or self.tree.column(c,width=w) for c,h,w in COLS];self.tree.heading('favorite',text='收藏');self.tree.grid(row=0,column=0,sticky='nsew');f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1)
 def load(self):
  self.s.load();self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}');self.status.config(text='数据校验通过' if not self.s.errors else '数据校验提示：'+self.s.errors[0])
 def search(self,record_history=True):
  q=clean(self.q.get())
  if not q:return []
  self.rows=list(self.s.search(q,self.cat.get()));return self.rows
 def clear_search(self):self.q.set('');self.rows=[];self.map={};self.target.config(text='输入品牌、系列、型号开始查询')
 def selected(self):return []
 def copy(self,*a,**k):return None
 def copy_all(self,*a,**k):return None
 def export_csv(self,*a,**k):return None
 def export_xlsx(self,*a,**k):return None
 def stats(self,*a,**k):return None
 def quote(self,*a,**k):return None
 def compare(self,*a,**k):return None
 def detail_rows(self,rs):return None
 def toast(self,text):self.status.config(text=text)
 def open_dir(self):
  try:
   if os.name=='nt':os.startfile(self.d)
   elif sys.platform=='darwin':subprocess.Popen(['open',self.d])
   else:subprocess.Popen(['xdg-open',self.d])
  except Exception as e:messagebox.showerror('数据目录',str(e),parent=self.root)
 def sources(self):return None
 def show_favorites(self):
  from favorites_view import show_favorites_matrix
  return show_favorites_matrix(self)
 def addToFavorites(self,rows):return self.fav.add(list(rows or []))
 def refresh_suggestions(self):return None
 def show_suggestions(self):return None
 def hide_suggestions(self):return None
