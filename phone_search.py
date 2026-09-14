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
class Store:
 def __init__(self,d,repository=None,search_service=None):
  self.d=d
  if repository is not None:self.repository=repository
  elif os.path.isfile(os.path.join(d,'search.sqlite3')):self.repository=SQLiteRepository(os.path.join(d,'search.sqlite3'))
  else:self.repository=CsvRepository(d,fields=tuple(FIELDS),category_map=CAT,clean=clean,read_csv=read_csv,valid=valid)
  self.search_service=search_service or SearchService([]);self.rows=[];self.snapshots={};self.manifest=[];self.errors=[]
 def load(self):self.rows,self.snapshots,self.errors=self.repository.load();self.manifest=list(getattr(self.repository,'manifest',[]) or []);self.search_service.replace_rows(self.rows)
 @property
 def dates(self):return sorted(self.snapshots)
 @property
 def latest(self):return self.dates[-1] if self.dates else ''
 def search(self,q='',cat='全部'):return self.search_service.search(q,cat)
 def history(self,targets):
  bases={tuple(key(r.get(x)) for x in ('category','subtype','brand','series','model')) for r in targets};return [r for r in self.rows if tuple(key(r.get(x)) for x in ('category','subtype','brand','series','model')) in bases]
class History:
 MAX_ITEMS=50
 def __init__(self,p):self.p=p;self.items=[];self.load()
 def load(self):
  try:
   with open(self.p,encoding='utf-8') as f:x=json.load(f)
   self.items=x if isinstance(x,list) else []
  except Exception:self.items=[]
  self.items=[clean(x) for x in self.items if clean(x)][:self.MAX_ITEMS]
 def add(self,q):
  q=clean(q)
  if not q:return
  self.items=[x for x in self.items if key(x)!=key(q)];self.items.insert(0,q);self.items=self.items[:self.MAX_ITEMS];self.save()
 def save(self):
  parent=os.path.dirname(self.p)
  if parent:os.makedirs(parent,exist_ok=True)
  with open(self.p,'w',encoding='utf-8') as f:json.dump(self.items,f,ensure_ascii=False,indent=2)
 def suggestions(self,q='',limit=5):
  q=key(q);return [x for x in self.items if not q or q in key(x)][:limit]
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
  added=[];duplicate=[];cur=self.dedupe();seen={self.identity(r) for r in cur};new=[]
  for r in rows:
   k=self.identity(r)
   if k in seen:duplicate.append(r);continue
   new.append(dict(r));seen.add(k);added.append(r)
  if new:cur.extend(new)
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
  self.root=root;root.title('数码回收价格秒查工具 · 图片事实库版');self.fit_main_window();root.resizable(True,True);self.base=os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__));self.d=os.path.join(self.base,'data');os.makedirs(self.d,exist_ok=True);self.s=Store(self.d);self.h=History(os.path.join(self.d,'search_history.json'));self.fav=Favorites(os.path.join(self.d,'favorites.json'));self.rows=[];self.map={};self.suggest_popup=None;self.setup();self.ui();self.load()
 def fit_main_window(self):
  self.root.update_idletasks();sw,sh=self.root.winfo_screenwidth(),self.root.winfo_screenheight();w=min(1720,max(1050,int(sw*.92)));h=min(930,max(620,int(sh*.88)));self.root.geometry(f'{w}x{h}');self.root.minsize(min(1250,w),min(720,h))
 def setup(self):
  st=ttk.Style();st.configure('T.Treeview',font=('微软雅黑',10),rowheight=32);st.configure('T.Treeview.Heading',font=('微软雅黑',11,'bold'));st.configure('TButton',font=('微软雅黑',10))
 def ui(self):
  top=ttk.Frame(self.root,padding=10);top.pack(fill='x');ttk.Label(top,text='🔍 品牌 / 系列 / 型号 / 别名',font=('微软雅黑',11,'bold')).pack(side='left');self.q=tk.StringVar();self.entry=tk.Entry(top,textvariable=self.q,font=('微软雅黑',14),width=34);self.entry.pack(side='left',padx=10,ipady=4);self.entry.bind('<Return>',lambda e:self.search());ttk.Button(top,text='×',width=3,command=self.clear_search).pack(side='left');ttk.Button(top,text='🔍',width=3,command=self.search).pack(side='left',padx=4);self.cat=tk.StringVar(value='全部');ttk.Combobox(top,textvariable=self.cat,values=['全部','手机','平板','电脑','其它','手机配件'],state='readonly',width=8).pack(side='left',padx=4);ttk.Button(top,text='查询',command=self.search).pack(side='left',padx=4);ttk.Button(top,text='🔄刷新',command=self.load).pack(side='left',padx=4);ttk.Button(top,text='📁数据目录',command=self.open_dir).pack(side='left',padx=4);ttk.Button(top,text='🧾来源结构',command=self.sources).pack(side='left',padx=4);ttk.Button(top,text='⭐收藏',command=self.show_favorites).pack(side='left',padx=4);self.status=ttk.Label(top,text='');self.status.pack(side='right');info=ttk.Frame(self.root,padding=(10,0,10,8));info.pack(fill='x');self.target=ttk.Label(info,text='输入品牌、系列、型号开始查询',font=('微软雅黑',11,'bold'));self.target.pack(side='left');self.meta=ttk.Label(info,text='');self.meta.pack(side='right');act=ttk.Frame(self.root,padding=(10,0,10,8));act.pack(fill='x');ttk.Button(act,text='☆ 一键收藏',command=self.add_favorite).pack(side='left',padx=4);ttk.Button(act,text='📋复制整表',command=self.copy_all).pack(side='left',padx=4);ttk.Button(act,text='💾导出CSV',command=self.export_csv).pack(side='left',padx=4);ttk.Button(act,text='📗导出Excel',command=self.export_xlsx).pack(side='left',padx=4);ttk.Label(act,text='搜索区只展示；复制/导出保持分组与间隔',foreground='#666').pack(side='right');host=ttk.Frame(self.root);host.pack(fill='both',expand=True,padx=10);self.tree=ttk.Treeview(host,columns=[x[0] for x in COLS],show='headings',selectmode='none');
  for c,h,w in COLS:self.tree.heading(c,text=h);self.tree.column(c,width=w,anchor='center' if c in {'data_date','category','subtype','price'} else 'w')
  self.tree.grid(row=0,column=0,sticky='nsew');host.grid_rowconfigure(0,weight=1);host.grid_columnconfigure(0,weight=1)
 def load(self):
  self.s.load();self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}');self.search(False) if self.q.get().strip() else None;self.status.config(text='数据校验通过' if not self.s.errors else '数据校验提示：'+self.s.errors[0])
 def search(self,record_history=True):
  q=clean(self.q.get())
  if not q:return []
  self.rows=list(self.s.search(q,self.cat.get()));return self.rows
 def clear_search(self):self.q.set('');self.rows=[];self.map={};self.tree.delete(*self.tree.get_children());self.target.config(text='输入品牌、系列、型号开始查询')
 def _export_rows(self):
  from search_display import build_result_blocks
  return build_result_blocks(self.rows)
 def copy_all(self):
  if not self.rows:return self.toast('当前没有搜索结果')
  blocks=self._export_rows();lines=['\t'.join(h for _,h,_ in COLS)];lm=ld=None
  for b in blocks:
   m,d=b.get('_model_key'),b.get('_period_key')
   if lm is not None and m!=lm:lines += ['\t'*(len(COLS)-1)]*2
   elif ld is not None and d!=ld:lines.append('\t'*(len(COLS)-1))
   for r in b.get('_rows',[]):lines.append('\t'.join(str(r.get(c,'')) for c,_,_ in COLS))
   lm,ld=m,d
  self.root.clipboard_clear();self.root.clipboard_append('\r\n'.join(lines));self.root.update();self.status.config(text=f'已复制搜索结果 {len(self.rows)} 条，保留分组与间隔')
 def export_csv(self):return self._export(False)
 def export_xlsx(self):return self._export(True)
 def _export(self,xlsx):
  if not self.rows:return self.toast('当前没有搜索结果')
  ext='.xlsx' if xlsx else '.csv';p=filedialog.asksaveasfilename(parent=self.root,title='导出搜索结果',defaultextension=ext,filetypes=[('Excel 文件','*.xlsx')] if xlsx else [('CSV 文件','*.csv')])
  if not p:return
  from search_display import build_result_blocks
  blocks=build_result_blocks(self.rows)
  try:
   if xlsx:
    if Workbook is None:raise RuntimeError('需要 openpyxl')
    wb=Workbook();ws=wb.active;ws.title='搜索结果';ws.append([h for _,h,_ in COLS]);ri=2;lm=ld=None
    for b in blocks:
     m,d=b.get('_model_key'),b.get('_period_key')
     if lm is not None and m!=lm:ri+=2
     elif ld is not None and d!=ld:ri+=1
     for r in b.get('_rows',[]):ws.append([r.get(c,'') for c,_,_ in COLS]);ri+=1
     lm,ld=m,d
    for c,(_,_,w) in enumerate(COLS,1):ws.column_dimensions[get_column_letter(c)].width=max(12,min(42,w/8))
    ws.freeze_panes='A2';wb.save(p)
   else:
    with open(p,'w',encoding='utf-8-sig',newline='') as f:
     w=csv.writer(f);w.writerow([h for _,h,_ in COLS]);lm=ld=None
     for b in blocks:
      m,d=b.get('_model_key'),b.get('_period_key')
      if lm is not None and m!=lm:w.writerow([]);w.writerow([])
      elif ld is not None and d!=ld:w.writerow([])
      for r in b.get('_rows',[]):w.writerow([r.get(c,'') for c,_,_ in COLS])
      lm,ld=m,d
   self.status.config(text=f'已导出搜索结果 {len(self.rows)} 条，保留分组与间隔')
  except Exception as e:messagebox.showerror('导出失败',str(e),parent=self.root)
 def selected(self):return []
 def detail(self,e=None):return None
 def detail_rows(self,rs):return None
 def toast(self,text):self.status.config(text=text)
 def open_dir(self):
  try:
   if os.name=='nt':os.startfile(self.d)
   elif sys.platform=='darwin':subprocess.Popen(['open',self.d])
   else:subprocess.Popen(['xdg-open',self.d])
  except Exception as e:messagebox.showerror('数据目录',str(e))
 def sources(self):return None
 def show_favorites(self):
  from favorites_view import show_favorites_matrix
  return show_favorites_matrix(self)
 def addToFavorites(self,rows):
  rows=list(rows or []);added,dup=self.fav.add(rows);self.status.config(text=f'已收藏 {len(added)} 条' if added else '已经收藏');return added,dup
