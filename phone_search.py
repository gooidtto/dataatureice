import csv,json,os,re,subprocess,sys,unicodedata,tkinter as tk
from tkinter import ttk,messagebox,filedialog
try:
 from openpyxl import Workbook
 from openpyxl.styles import Font
 from openpyxl.utils import get_column_letter
except ImportError: Workbook=None
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
COLS=[('data_date','数据日期',105),('category','分类',70),('subtype','子类型',75),('brand','品牌',110),('series','系列',110),('model','型号',250),('condition','价格条件',175),('price','价格',85),('unit','单位',85),('note','备注',260),('source_image','来源图片',150)]
TRUE={'1','true','yes','verified'};CAT={'phone':'手机','tablet':'平板','computer':'电脑','other':'其它','手机':'手机','平板':'平板','电脑':'电脑','其它':'其它'}
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
class Store:
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
 def save(self):
  os.makedirs(os.path.dirname(self.p),exist_ok=True);tmp=self.p+'.tmp'
  with open(tmp,'w',encoding='utf-8') as f:json.dump(self.items,f,ensure_ascii=False,indent=2)
  os.replace(tmp,self.p)
 def clear(self):
  self.items=[]
  try:os.remove(self.p)
  except FileNotFoundError:pass
class Favorites:
 MAX_ITEMS=200
 def __init__(self,p):self.p=p;self.items=[];self.load()
 def identity(self,r):return '|'.join(str(x) for x in rid(r))+'|'+key(r.get('condition'))+'|'+clean(r.get('data_date'))+'|'+clean(r.get('price'))+'|'+clean(r.get('unit'))
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
 def add(self,rows):
  cur=self.dedupe();seen={self.identity(r) for r in cur}
  for r in rows:
   k=self.identity(r)
   if k not in seen:cur.insert(0,dict(r));seen.add(k)
  self.items=cur[:self.MAX_ITEMS];self.save()
 def remove(self,rows):
  ks={self.identity(r) for r in rows};self.items=[r for r in self.dedupe() if self.identity(r) not in ks];self.save()
 def save(self):
  os.makedirs(os.path.dirname(self.p),exist_ok=True);tmp=self.p+'.tmp'
  with open(tmp,'w',encoding='utf-8') as f:json.dump(self.items,f,ensure_ascii=False,indent=2)
  os.replace(tmp,self.p)
class App:
 def __init__(self,root):
  self.root=root;root.title('数码回收价格秒查工具 · 图片事实库版');root.geometry('1720x930');root.minsize(1250,720);self.base=os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__));self.d=os.path.join(self.base,'data');os.makedirs(self.d,exist_ok=True);self.s=Store(self.d);self.h=JsonList(os.path.join(self.d,'search_history.json'));self.fav=Favorites(os.path.join(self.d,'favorites.json'));self.rows=[];self.map={};self.anchor=None;self.dragging=False;self.setup();self.ui();self.load()
 def setup(self):
  st=ttk.Style();st.configure('T.Treeview',font=('微软雅黑',10),rowheight=32);st.configure('T.Treeview.Heading',font=('微软雅黑',11,'bold'));st.configure('TButton',font=('微软雅黑',10))
 def ui(self):
  top=ttk.Frame(self.root,padding=10);top.pack(fill='x');ttk.Label(top,text='🔎 品牌 / 系列 / 型号 / 别名',font=('微软雅黑',11,'bold')).pack(side='left');self.q=tk.StringVar();self.entry=tk.Entry(top,textvariable=self.q,font=('微软雅黑',14),width=30);self.entry.pack(side='left',padx=(10,2),ipady=4);self.entry.bind('<Return>',lambda e:self.search());ttk.Button(top,text='✕',width=3,command=self.clear_search).pack(side='left',padx=(0,8));self.cat=tk.StringVar(value='全部');ttk.Combobox(top,textvariable=self.cat,values=['全部','手机','平板','电脑','其它'],state='readonly',width=8).pack(side='left',padx=4)
  for t,c in [('查询',self.search),('🔄刷新',self.load),('📁数据目录',self.open_dir),('🧾来源结构',self.sources),('⭐收藏',self.show_favorites)]:ttk.Button(top,text=t,command=c).pack(side='left',padx=4)
  self.status=ttk.Label(top,text='');self.status.pack(side='right')
  hb=ttk.Frame(self.root,padding=(10,0,10,8));hb.pack(fill='x');ttk.Label(hb,text='搜索历史',font=('微软雅黑',10,'bold')).pack(side='left');self.hl=tk.Listbox(hb,height=3,font=('微软雅黑',10),selectmode='browse',exportselection=False);self.hl.pack(side='left',fill='x',expand=True,padx=6);self.hl.bind('<Double-Button-1>',self.use_history);ttk.Button(hb,text='清空历史',command=self.clear_history).pack(side='left',padx=4);self.refresh_history()
  info=ttk.Frame(self.root,padding=(10,0,10,8));info.pack(fill='x');self.target=ttk.Label(info,text='搜索结果：全部日期，日期优先、同日期价格降序',font=('微软雅黑',11,'bold'));self.target.pack(side='left');self.meta=ttk.Label(info,text='');self.meta.pack(side='right')
  act=ttk.Frame(self.root,padding=(10,0,10,8));act.pack(fill='x');
  for t,c in [('📋复制选中',self.copy),('📋复制整表',self.copy_all),('💾导出CSV',self.export_csv),('📗导出Excel',self.export_xlsx),('📊条件统计',self.stats),('💰批量报价',self.quote),('📈历史对比',self.compare)]:ttk.Button(act,text=t,command=c).pack(side='left',padx=4)
  ttk.Label(act,text='新日期在上；同日期价格从高到低；日期间隔两空行',foreground='#666').pack(side='right')
  f=ttk.Frame(self.root);f.pack(fill='both',expand=True,padx=10);self.tree=ttk.Treeview(f,columns=[x[0] for x in COLS],show='headings',selectmode='extended')
  for c,h,w in COLS:self.tree.heading(c,text=h);self.tree.column(c,width=w,anchor='center' if c in {'data_date','category','subtype','price'} else 'w')
  y=ttk.Scrollbar(f,orient='vertical',command=self.tree.yview);x=ttk.Scrollbar(f,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set);self.tree.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew');f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1);self.tree.bind('<Control-c>',self.copy);self.tree.bind('<Control-C>',self.copy);self.tree.bind('<Control-a>',self.select_all);self.tree.bind('<Control-A>',self.select_all);self.tree.bind('<Button-1>',self.drag_start,add='+');self.tree.bind('<B1-Motion>',self.drag_select,add='+');self.tree.bind('<ButtonRelease-1>',self.drag_end,add='+');self.tree.bind('<Button-3>',self.menu);self.tree.bind('<Double-1>',self.detail)
 def load(self):
  self.s.load();self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)}');self.refresh_history();self.search(False);self.status.config(text='数据校验通过' if not self.s.errors else '数据校验提示：'+self.s.errors[0])
 def refresh_history(self):
  if not hasattr(self,'hl'):return
  self.hl.delete(0,'end');[self.hl.insert('end',x) for x in self.h.items]
 def use_history(self,e=None):
  s=self.hl.curselection()
  if s:self.q.set(self.hl.get(s[0]));self.search()
 def clear_history(self):
  if not self.h.items:return
  if messagebox.askyesno('清除搜索历史','确定清除全部搜索历史吗？'):self.h.clear();self.refresh_history();self.status.config(text='搜索历史已清除')
 def clear_search(self):
  self.q.set('');self.rows=[];self.map={};self.tree.delete(*self.tree.get_children());self.target.config(text='已清空搜索框');self.status.config(text='搜索框已清空');self.entry.focus_set()
 def search(self,record_history=True):
  q=clean(self.q.get())
  if record_history and q:self.h.add(q);self.refresh_history()
  self.rows=self.s.search(q,self.cat.get());self.render(self.rows);n=len({rid(r) for r in self.rows});self.target.config(text=f'搜索：{q} · {n} 个型号目标 · {len(self.rows)} 条价格记录 · 全部日期' if q else '搜索结果：全部日期，日期优先、同日期价格降序');self.status.config(text=f'结果 {len(self.rows)} 条'+(f' · 数据问题 {len(self.s.errors)}' if self.s.errors else ''))
 def render(self,rows):
  self.tree.delete(*self.tree.get_children());self.map={};last=None;i=0
  for r in rows:
   if last and r['data_date']!=last:
    for _ in range(2):gid=f'g{i}';i+=1;self.tree.insert('', 'end',iid=gid,values=('',)*len(COLS));self.map[gid]=None
   iid=f'r{i}';i+=1;self.tree.insert('', 'end',iid=iid,values=tuple(r.get(c,'') for c,_,_ in COLS));self.map[iid]=r;last=r['data_date']
 def select_all(self,e=None):self.tree.selection_set([i for i,r in self.map.items() if r]);return 'break'
 def drag_start(self,e):
  iid=self.tree.identify_row(e.y)
  if not iid or self.map.get(iid) is None:self.anchor=None;self.dragging=False;return
  self.anchor=iid;self.dragging=True;self.tree.selection_set(iid)
 def drag_select(self,e):
  if not self.dragging or not self.anchor:return
  iid=self.tree.identify_row(e.y)
  if not iid:return
  ch=list(self.tree.get_children())
  if iid not in ch or self.anchor not in ch:return
  a,b=ch.index(self.anchor),ch.index(iid);lo,hi=sorted((a,b));self.tree.selection_set([x for x in ch[lo:hi+1] if self.map.get(x)]);self.tree.see(iid)
 def drag_end(self,e):self.dragging=False
 def selected(self):return [self.map[i] for i in self.tree.selection() if self.map.get(i)]
 def table(self,rows):
  lines=['\t'.join(h for _,h,_ in COLS)];last=None
  for r in rows:
   if last and r['data_date']!=last:lines += ['\t'.join(['']*len(COLS))]*2
   lines.append('\t'.join(str(r.get(c,'')) for c,_,_ in COLS));last=r['data_date']
  return '\r\n'.join(lines)
 def copy(self,e=None):
  rs=self.selected()
  if rs:self.root.clipboard_clear();self.root.clipboard_append(self.table(rs));self.root.update();self.status.config(text=f'已复制 {len(rs)} 条')
  return 'break' if e else None
 def copy_all(self):
  if self.rows:self.root.clipboard_clear();self.root.clipboard_append(self.table(self.rows));self.root.update();self.status.config(text=f'已复制整表 {len(self.rows)} 条')
 def export_csv(self):self.export(False,self.selected() or self.rows)
 def export_xlsx(self):self.export(True,self.selected() or self.rows)
 def export(self,xlsx,rs):
  if not rs:return messagebox.showinfo('导出','没有可导出的结果')
  ext='.xlsx' if xlsx else '.csv';initial='数码价格查询.xlsx' if xlsx else '数码价格查询结果.csv';types=[('Excel 文件','*.xlsx')] if xlsx else [('CSV 文件','*.csv'),('所有文件','*.*')]
  p=filedialog.asksaveasfilename(title='导出查询结果',defaultextension=ext,filetypes=types,initialfile=initial)
  if not p:return
  if not p.lower().endswith(ext):p+=ext
  try:
   if xlsx:
    if Workbook is None:raise RuntimeError('需要 openpyxl')
    wb=Workbook();ws=wb.active;ws.title='查询结果';ws.append([h for _,h,_ in COLS]);last=None
    for r in rs:
     if last and r['data_date']!=last:ws.append([]);ws.append([])
     ws.append([r.get(c,'') for c,_,_ in COLS]);last=r['data_date']
    for c in ws[1]:c.font=Font(bold=True)
    for i,(_,_,w) in enumerate(COLS,1):ws.column_dimensions[get_column_letter(i)].width=max(12,min(42,w/8))
    ws.freeze_panes='A2';wb.save(p)
   else:
    with open(p,'w',encoding='utf-8-sig',newline='') as f:
     w=csv.writer(f);w.writerow([h for _,h,_ in COLS]);last=None
     for r in rs:
      if last and r['data_date']!=last:w.writerow([]);w.writerow([])
      w.writerow([r.get(c,'') for c,_,_ in COLS]);last=r['data_date']
   messagebox.showinfo('导出成功',f'已导出 {len(rs)} 条记录\n{p}');self.status.config(text=f'导出成功：{len(rs)} 条');return True
  except Exception as e:messagebox.showerror('导出失败',f'无法写入文件：\n{p}\n\n{e}');return False
 def add_favorite(self):
  rs=self.selected()
  if not rs:return messagebox.showinfo('收藏','请先选择一个或多个搜索结果')
  before={self.fav.identity(r) for r in self.fav.items};self.fav.add(rs);added=sum(1 for r in self.fav.items if self.fav.identity(r) not in before);self.status.config(text=f'已收藏 {added} 条 · 收藏总数 {len(self.fav.items)}')
 def show_favorites(self):
  w=tk.Toplevel(self.root);w.title('⭐ 我的收藏');w.geometry('1500x760');w.minsize(1050,560);ttk.Label(w,text=f'收藏内容 · {len(self.fav.items)} 条',font=('微软雅黑',12,'bold')).pack(anchor='w',padx=10,pady=8)
  f=ttk.Frame(w,padding=10);f.pack(fill='both',expand=True);tr=ttk.Treeview(f,columns=[x[0] for x in COLS],show='headings',selectmode='extended')
  for c,h,ww in COLS:tr.heading(c,text=h);tr.column(c,width=ww,anchor='center' if c in {'data_date','category','subtype','price'} else 'w')
  y=ttk.Scrollbar(f,orient='vertical',command=tr.yview);tr.configure(yscrollcommand=y.set);tr.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1);mp={};last=None;i=0
  for r in self.s._sort(self.fav.items):
   if last and r['data_date']!=last:
    for _ in range(2):gid=f'g{i}';i+=1;tr.insert('', 'end',iid=gid,values=('',)*len(COLS));mp[gid]=None
   iid=f'r{i}';i+=1;tr.insert('', 'end',iid=iid,values=tuple(r.get(c,'') for c,_,_ in COLS));mp[iid]=r;last=r['data_date']
  def sel():return [mp[i] for i in tr.selection() if mp.get(i)]
  bar=ttk.Frame(w,padding=8);bar.pack(fill='x');ttk.Button(bar,text='查看详情',command=lambda:self.detail_rows(sel() or self._all(mp))).pack(side='left',padx=4);ttk.Button(bar,text='移除收藏',command=lambda:self.remove_favorites(w,tr,mp)).pack(side='left',padx=4);ttk.Button(bar,text='复制',command=lambda:self.copy_popup(sel() or self._all(mp))).pack(side='left',padx=4);ttk.Button(bar,text='导出CSV',command=lambda:self.export_popup(sel() or self._all(mp),False)).pack(side='left',padx=4);ttk.Button(bar,text='导出Excel',command=lambda:self.export_popup(sel() or self._all(mp),True)).pack(side='left',padx=4);ttk.Button(bar,text='关闭',command=w.destroy).pack(side='right',padx=4);tr.bind('<Double-1>',lambda e:self.detail_rows(sel()));tr.bind('<Button-3>',lambda e:self.favorite_menu(e,tr,mp))
 def _all(self,mp):return [r for r in mp.values() if r]
 def favorite_menu(self,e,tr,mp):
  iid=tr.identify_row(e.y)
  if iid and mp.get(iid):tr.selection_set(iid)
  m=tk.Menu(self.root,tearoff=0);m.add_command(label='移除收藏',command=lambda:self.remove_favorites(tr.winfo_toplevel(),tr,mp));m.tk_popup(e.x_root,e.y_root)
 def remove_favorites(self,w,tr,mp):
  rs=[mp[i] for i in tr.selection() if mp.get(i)]
  if not rs:return
  self.fav.remove(rs);w.destroy();self.show_favorites();self.status.config(text=f'已移除收藏 {len(rs)} 条')
 def copy_popup(self,rs):
  if rs:self.root.clipboard_clear();self.root.clipboard_append(self.table(rs));self.root.update()
 def export_popup(self,rs,xlsx):self.export(xlsx,rs)
 def detail_rows(self,rs):
  if not rs:return
  r=rs[0];w=tk.Toplevel(self.root);w.title('记录详情');w.geometry('760x560');t=tk.Text(w,font=('微软雅黑',11));t.pack(fill='both',expand=True,padx=12,pady=12);t.insert('1.0','\n'.join(f'{k}：{r.get(k,"")}' for k in FIELDS if r.get(k,'')));t.config(state='disabled')
 def detail(self,e=None):self.detail_rows(self.selected())
 def menu(self,e):
  iid=self.tree.identify_row(e.y)
  if iid and self.map.get(iid) is not None:self.tree.selection_set(iid)
  m=tk.Menu(self.root,tearoff=0);m.add_command(label='查看详情',command=self.detail);m.add_command(label='⭐ 添加收藏',command=self.add_favorite);m.add_command(label='复制选中',command=self.copy);m.add_separator();m.add_command(label='历史对比',command=self.compare);m.tk_popup(e.x_root,e.y_root)
 def stats(self):
  rs=self.selected() or self.rows;g={}
  for r in rs:
   n=num(r['price'])
   if n is not None:g.setdefault(r['condition'],[]).append(n)
  if rs:messagebox.showinfo('动态价格条件统计','\n'.join(f'{k}：{min(v):g}～{max(v):g}，平均 {sum(v)/len(v):.2f}' for k,v in g.items()))
 def quote(self):
  if self.selected():messagebox.showinfo('批量报价','批量报价按当前选中记录执行。')
 def compare(self):
  rs=self.selected()
  if not rs:return messagebox.showinfo('历史对比','请先选择一个或多个型号结果')
  targets=[];seen=set()
  for r in rs:
   k=rid(r)
   if k not in seen:seen.add(k);targets.append(r)
  self.show_compare(self.s.history(targets),targets)
 def show_compare(self,rows,targets):
  w=tk.Toplevel(self.root);w.title('历史价格对比 · 同型号跨日期');w.geometry('1650x760');w.minsize(1100,600);ttk.Label(w,text='历史对比：'+'；'.join(' '.join(x for x in (r['brand'],r['series'],r['model']) if x) for r in targets[:8]),font=('微软雅黑',12,'bold')).pack(anchor='w',padx=10,pady=8)
  f=ttk.Frame(w);f.pack(fill='both',expand=True,padx=10);tree=ttk.Treeview(f,columns=[x[0] for x in COLS],show='headings',selectmode='extended')
  for c,h,ww in COLS:tree.heading(c,text=h);tree.column(c,width=ww,anchor='center' if c in {'data_date','category','subtype','price'} else 'w')
  tree.grid(row=0,column=0,sticky='nsew');y=ttk.Scrollbar(f,orient='vertical',command=tree.yview);y.grid(row=0,column=1,sticky='ns');tree.configure(yscrollcommand=y.set);f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1);mp={};last=None;i=0
  for r in rows:
   if last and r['data_date']!=last:
    for _ in range(2):gid=f'g{i}';i+=1;tree.insert('', 'end',iid=gid,values=('',)*len(COLS));mp[gid]=None
   iid=f'r{i}';i+=1;tree.insert('', 'end',iid=iid,values=tuple(r.get(c,'') for c,_,_ in COLS));mp[iid]=r;last=r['data_date']
  bar=ttk.Frame(w,padding=8);bar.pack(fill='x');sel=lambda:[mp[i] for i in tree.selection() if mp.get(i)];ttk.Button(bar,text='复制选中',command=lambda:self.copy_popup(sel() or rows)).pack(side='left',padx=4);ttk.Button(bar,text='复制整表',command=lambda:self.copy_popup(rows)).pack(side='left',padx=4);ttk.Button(bar,text='导出CSV',command=lambda:self.export_popup(sel() or rows,False)).pack(side='left',padx=4);ttk.Button(bar,text='导出Excel',command=lambda:self.export_popup(sel() or rows,True)).pack(side='left',padx=4);ttk.Button(bar,text='关闭',command=w.destroy).pack(side='right',padx=4)
 def open_dir(self):
  try:
   if os.name=='nt':os.startfile(self.d)
   elif sys.platform=='darwin':subprocess.Popen(['open',self.d])
   else:subprocess.Popen(['xdg-open',self.d])
  except Exception as e:messagebox.showerror('数据目录',str(e))
 def sources(self):
  if not self.s.manifest:return messagebox.showinfo('来源结构','未找到 source_image_manifest.csv')
  w=tk.Toplevel(self.root);w.title('来源图片结构');w.geometry('1100x620');f=ttk.Frame(w,padding=10);f.pack(fill='both',expand=True);cols=['include','data_date','category','status','source_image','verification','verification_note'];tr=ttk.Treeview(f,columns=cols,show='headings');heads={'include':'纳入','data_date':'日期','category':'分类','status':'状态','source_image':'来源图片','verification':'验证','verification_note':'说明'}
  for c in cols:tr.heading(c,text=heads[c]);tr.column(c,width=130 if c!='verification_note' else 360)
  for r in self.s.manifest:tr.insert('', 'end',values=tuple(r.get(c,'') for c in cols))
  tr.pack(fill='both',expand=True)
if __name__=='__main__':root=tk.Tk();App(root);root.mainloop()
