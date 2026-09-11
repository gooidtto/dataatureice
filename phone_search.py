import csv,json,os,re,subprocess,sys,unicodedata,tkinter as tk
from tkinter import ttk,messagebox,filedialog
try:
 from openpyxl import Workbook
 from openpyxl.styles import Font
 from openpyxl.utils import get_column_letter
except ImportError: Workbook=None
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
class Store:
 def __init__(self,d):self.d=d;self.rows=[];self.snapshots={};self.manifest=[];self.errors=[]
 def load(self):
  self.rows=[];self.snapshots={};self.manifest=[];self.errors=[]
  db=os.path.join(self.d,'database')
  groups={}
  if os.path.isdir(db):
   for date in os.listdir(db):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):continue
    folder=os.path.join(db,date)
    if not os.path.isdir(folder):continue
    paths=[os.path.join(folder,n) for n in sorted(os.listdir(folder)) if n.lower().endswith('.csv') and os.path.isfile(os.path.join(folder,n))]
    if paths:groups.setdefault(date,[]).extend(paths)
  sd=os.path.join(self.d,'snapshots')
  if os.path.isdir(sd):
   for d in os.listdir(sd):
    dp=os.path.join(sd,d)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',d) and os.path.isdir(dp):groups.setdefault(d,[]).extend([os.path.join(dp,n) for n in sorted(os.listdir(dp)) if n.lower().endswith('.csv')])
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
 def search(self,q='',cat='全部'):
  q=key(q);return self._sort([r for r in self.rows if (cat=='全部' or r['category']==cat) and (not q or q in key(' '.join(r.get(x,'') for x in ('brand','series','model','model_code','alias','source_image'))))])
 def history(self,targets):
  def hk(r):return tuple(key(r.get(x)) for x in ('category','subtype','brand','series','model'))
  ks={hk(r) for r in targets};return self._sort([r for r in self.rows if hk(r) in ks])
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
  with open(tmp,'w',encoding='utf-8') as f:json.dump(self.items,f,ensure_ascii=False,indent=2)
  os.replace(tmp,self.p)
class App:
 def __init__(self,root):
  self.root=root;root.title('数码回收价格秒查工具 · 图片事实库版');self.fit_main_window();root.resizable(True,True);self.base=os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__));self.d=os.path.join(self.base,'data');os.makedirs(self.d,exist_ok=True);self.s=Store(self.d);self.h=JsonList(os.path.join(self.d,'search_history.json'));self.fav=Favorites(os.path.join(self.d,'favorites.json'));self.rows=[];self.map={};self.anchor=None;self.dragging=False;self.suggest_popup=None;self.setup();self.ui();self.load()
 def fit_main_window(self):
  self.root.update_idletasks();sw,sh=self.root.winfo_screenwidth(),self.root.winfo_screenheight();w=min(1720,max(1050,int(sw*0.92)));h=min(930,max(620,int(sh*0.88)));w=min(w,sw-24);h=min(h,sh-48);self.root.minsize(min(1250,w),min(720,h));x=max(12,(sw-w)//2);y=max(12,(sh-h)//2);self.root.geometry(f'{w}x{h}+{x}+{y}')
 def setup(self):
  st=ttk.Style();st.configure('T.Treeview',font=('微软雅黑',10),rowheight=32);st.configure('T.Treeview.Heading',font=('微软雅黑',11,'bold'));st.configure('TButton',font=('微软雅黑',10))
 def ui(self):
  top=ttk.Frame(self.root,padding=10);top.pack(fill='x');ttk.Label(top,text='🔍 品牌 / 系列 / 型号 / 别名',font=('微软雅黑',11,'bold')).pack(side='left');self.q=tk.StringVar();self.entry=tk.Entry(top,textvariable=self.q,font=('微软雅黑',14),width=34);self.entry.pack(side='left',padx=(10,2),ipady=4);self.entry.bind('<Return>',lambda e:self.search());self.q.trace_add('write',lambda *_:self.refresh_suggestions());self.entry.bind('<FocusIn>',lambda e:self.show_suggestions());self.entry.bind('<Escape>',lambda e:self.hide_suggestions());ttk.Button(top,text='×',width=3,command=self.clear_search).pack(side='left',padx=(0,4));ttk.Button(top,text='🔍',width=3,command=self.search).pack(side='left',padx=(0,8));self.cat=tk.StringVar(value='全部');ttk.Combobox(top,textvariable=self.cat,values=['全部','手机','平板','电脑','其它','手机配件'],state='readonly',width=8).pack(side='left',padx=4)
  for t,c in [('查询',self.search),('🔄刷新',self.load),('📁数据目录',self.open_dir),('🧾来源结构',self.sources),('⭐收藏',self.show_favorites)]:ttk.Button(top,text=t,command=c).pack(side='left',padx=4)
  self.status=ttk.Label(top,text='');self.status.pack(side='right')
  info=ttk.Frame(self.root,padding=(10,0,10,8));info.pack(fill='x');self.target=ttk.Label(info,text='搜索结果：全部日期，日期优先、同日期价格降序',font=('微软雅黑',11,'bold'));self.target.pack(side='left');self.meta=ttk.Label(info,text='');self.meta.pack(side='right')
  act=ttk.Frame(self.root,padding=(10,0,10,8));act.pack(fill='x');ttk.Button(act,text='☆ 一键收藏',command=self.add_favorite).pack(side='left',padx=4)
  for t,c in [('📋复制选中',self.copy),('📋复制整表',self.copy_all),('💾导出CSV',self.export_csv),('📗导出Excel',self.export_xlsx),('📊条件统计',self.stats),('💰批量报价',self.quote),('📈历史对比',self.compare)]:ttk.Button(act,text=t,command=c).pack(side='left',padx=4)
  ttk.Label(act,text='新日期在上；同日期价格从高到低；日期间隔两空行',foreground='#666').pack(side='right')
  f=ttk.Frame(self.root);f.pack(fill='both',expand=True,padx=10);self.tree=ttk.Treeview(f,columns=[x[0] for x in COLS]+['favorite'],show='headings',selectmode='extended')
  for c,h,w in COLS:self.tree.heading(c,text=h);self.tree.column(c,width=w,anchor='center' if c in {'data_date','category','subtype','price'} else 'w')
  self.tree.heading('favorite',text='一键收藏');self.tree.column('favorite',width=120,anchor='center')
  y=ttk.Scrollbar(f,orient='vertical',command=self.tree.yview);x=ttk.Scrollbar(f,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set);self.tree.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew');f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1);self.tree.bind('<Control-c>',self.copy);self.tree.bind('<Control-C>',self.copy);self.tree.bind('<Control-a>',self.select_all);self.tree.bind('<Control-A>',self.select_all);self.tree.bind('<Button-1>',self.on_tree_click,add='+');self.tree.bind('<B1-Motion>',self.drag_select,add='+');self.tree.bind('<ButtonRelease-1>',self.drag_end,add='+');self.tree.bind('<Button-3>',self.menu);self.tree.bind('<Double-1>',self.detail);self.root.bind('<Button-1>',self.dismiss_suggestions,add='+')
 def load(self):
  self.s.load();self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}');self.search(False);self.status.config(text='数据校验通过' if not self.s.errors else '数据校验提示：'+self.s.errors[0]);self.refresh_suggestions()
 def show_suggestions(self):
  if not self.h.items:return self.hide_suggestions()
  if self.suggest_popup is None or not self.suggest_popup.winfo_exists():self.suggest_popup=tk.Toplevel(self.root);self.suggest_popup.overrideredirect(True);self.suggest_popup.transient(self.root);self.suggest_popup.configure(bg='#d9d9d9')
  self.refresh_suggestions()
 def refresh_suggestions(self):
  if not hasattr(self,'entry'):return
  if self.suggest_popup is None or not self.suggest_popup.winfo_exists():
   if not self.h.items:return
   self.show_suggestions();return
  for w in self.suggest_popup.winfo_children():w.destroy()
  q=clean(self.q.get());items=self.h.suggestions(q,5)
  if not items:return self.hide_suggestions()
  frame=tk.Frame(self.suggest_popup,bg='white',bd=1,relief='solid');frame.pack(fill='both',expand=True)
  for text in items:tk.Button(frame,text='🔍  '+text,anchor='w',font=('微软雅黑',11),bg='white',activebackground='#f2f2f2',relief='flat',bd=0,padx=10,pady=7,command=lambda v=text:self.choose_history(v)).pack(fill='x')
  tk.Button(frame,text='☰  显示所有历史',anchor='w',font=('微软雅黑',10,'bold'),bg='white',activebackground='#f2f2f2',relief='flat',bd=0,padx=10,pady=8,command=self.show_history).pack(fill='x')
  x=self.entry.winfo_rootx();y=self.entry.winfo_rooty()+self.entry.winfo_height();w=self.entry.winfo_width()+45;frame.update_idletasks();self.suggest_popup.geometry(f'{w}x{frame.winfo_reqheight()}+{x}+{y}')
 def hide_suggestions(self):
  if self.suggest_popup is not None and self.suggest_popup.winfo_exists():self.suggest_popup.destroy()
  self.suggest_popup=None
 def dismiss_suggestions(self,event=None):
  if self.suggest_popup is None:return
  try:
   if event and event.widget in (self.entry,self.suggest_popup):return
  except Exception:pass
  self.hide_suggestions()
