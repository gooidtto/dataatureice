import csv,os,re,sys,subprocess,unicodedata,tkinter as tk
from pathlib import Path
from tkinter import ttk,messagebox,filedialog
try:
 from openpyxl import Workbook
 from openpyxl.styles import Font
 from openpyxl.utils import get_column_letter
except ImportError: Workbook=None
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}\.csv$',re.I)
SHARD_RE=re.compile(r'^\d{4}-\d{2}-\d{2}$')
FIELDS=['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']
COLS=[('data_date','数据日期',105),('category','分类',70),('subtype','子类型',75),('brand','品牌',110),('series','系列',110),('model','型号',250),('condition','价格条件',175),('price','价格',85),('unit','单位',85),('note','备注',260),('source_image','来源图片',150)]
CATEGORY_CANONICAL={'手机':'手机','平板':'平板','电脑':'电脑','其它':'其它','phone':'手机','tablet':'平板','computer':'电脑','other':'其它'}
TRUE={'1','true','yes','verified'}
def clean(v): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC','' if v is None else str(v)).replace('\ufeff','').replace('\u200b','').replace('\xa0',' ')).strip()
def key(v): return re.sub(r'[\s_\-—–·•/\\（）()【】\[\],，.;；:：|、]+','',clean(v).casefold())
def num(v):
 s=clean(v)
 if not s or '/' in s or s in {'-','—','/'}: return None
 m=re.search(r'[-+]?(?:\d+(?:\.\d+)?|\.\d+)',s)
 if not m:return None
 try:return float(m.group(0))
 except:return None
def read_csv(p):
 last=None
 for enc in ('utf-8-sig','utf-8','gb18030','gbk'):
  try:
   with open(p,encoding=enc,newline='') as f:return list(csv.DictReader(f))
  except Exception as e:last=e
 raise last or ValueError('CSV无法读取')
def verified(r): return clean(r.get('verified')).lower() in TRUE
def canonical_category(v): return CATEGORY_CANONICAL.get(clean(v),clean(v))
def row_valid(r): return bool(r.get('model') and r.get('condition') and r.get('price') and verified(r))
class Store:
 def __init__(self,d): self.d=d;self.rows=[];self.snapshots={};self.manifest=[];self.errors=[]
 def load(self):
  self.rows=[];self.snapshots={};self.errors=[];self.manifest=[];files=[]
  if not os.path.isdir(self.d): return
  for n in os.listdir(self.d):
   p=os.path.join(self.d,n)
   if DATE_RE.match(n) and os.path.isfile(p): files.append((n[:10],p))
  sr=os.path.join(self.d,'snapshots')
  if os.path.isdir(sr):
   for date in os.listdir(sr):
    dp=os.path.join(sr,date)
    if SHARD_RE.match(date) and os.path.isdir(dp):
     for n in sorted(os.listdir(dp)):
      p=os.path.join(dp,n)
      if n.lower().endswith('.csv') and os.path.isfile(p): files.append((date,p))
  grouped={}
  for date,p in files: grouped.setdefault(date,[]).append(p)
  for date,paths in grouped.items():
   try:
    data=[]
    for p in paths:
     for raw in read_csv(p):
      r={k:clean(raw.get(k,'')) for k in FIELDS};r['category']=canonical_category(r['category'])
      if r['data_date']!=date: self.errors.append(f'{date}: data_date不一致')
      if r['category'] not in {'手机','平板','电脑','其它'}: self.errors.append(f'{date}: 非标准分类 {r["category"]!r}')
      if row_valid(r): data.append(r)
    ids={}
    for r in data: ids[r['record_id']]=ids.get(r['record_id'],0)+1
    dup=sum(v-1 for v in ids.values() if v>1)
    if dup:self.errors.append(f'{date}: 重复 record_id {dup} 条')
    self.snapshots[date]=data;self.rows+=data
   except Exception as e:self.errors.append(f'{date}: {e}')
  mp=os.path.join(self.d,'source_image_manifest.csv')
  if os.path.isfile(mp):
   try:self.manifest=read_csv(mp)
   except Exception as e:self.errors.append(f'来源清单: {e}')
 @property
 def dates(self): return sorted(self.snapshots)
 @property
 def latest(self): return self.dates[-1] if self.dates else ''
 def search(self,q='',cat='全部',history=False):
  q=key(q);dates=set(self.dates) if history else ({self.latest} if self.latest else set());out=[]
  for r in self.rows:
   if r['data_date'] not in dates or (cat!='全部' and r['category']!=cat):continue
   if q and q not in key(' '.join(r.get(x,'') for x in ('brand','series','model','model_code','alias','source_image'))):continue
   out.append(r)
  return sorted(out,key=lambda r:(r['data_date'],r['brand'],r['series'],r['model'],r['condition']))
class App:
 def __init__(self,root):
  self.root=root;root.title('数码回收价格秒查工具 · 图片事实库版');root.geometry('1720x930');root.minsize(1250,720)
  self.base=os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else os.path.dirname(os.path.abspath(__file__));self.d=os.path.join(self.base,'data');os.makedirs(self.d,exist_ok=True);self.s=Store(self.d);self.rows=[]
  st=ttk.Style()
  try:st.theme_use('clam')
  except:pass
  st.configure('T.Treeview',font=('微软雅黑',10),rowheight=32);st.configure('T.Treeview.Heading',font=('微软雅黑',11,'bold'));self.ui();self.load()
 def ui(self):
  top=ttk.Frame(self.root,padding=10);top.pack(fill='x');ttk.Label(top,text='🔎 品牌 / 系列 / 型号 / 别名',font=('微软雅黑',11,'bold')).pack(side='left')
  self.q=tk.StringVar();e=tk.Entry(top,textvariable=self.q,font=('微软雅黑',14),width=30);e.pack(side='left',padx=10,ipady=4);e.bind('<Return>',lambda _:self.search())
  self.cat=tk.StringVar(value='全部');ttk.Combobox(top,textvariable=self.cat,values=['全部','手机','平板','电脑','其它'],state='readonly',width=8).pack(side='left',padx=4)
  self.hist=tk.BooleanVar();ttk.Checkbutton(top,text='包含历史',variable=self.hist,command=self.search).pack(side='left',padx=8)
  for t,c in [('查询',self.search),('🔄刷新',self.load),('📁数据目录',self.open_dir),('🧾来源结构',self.sources)]:ttk.Button(top,text=t,command=c).pack(side='left',padx=3)
  self.status=ttk.Label(top,text='');self.status.pack(side='right')
  info=ttk.Frame(self.root,padding=(10,0,10,8));info.pack(fill='x');self.target=ttk.Label(info,text='搜索结果按图片原始价格条件逐行显示',font=('微软雅黑',11,'bold'));self.target.pack(side='left');self.meta=ttk.Label(info,text='',foreground='#666');self.meta.pack(side='right')
  act=ttk.Frame(self.root,padding=(10,0,10,8));act.pack(fill='x')
  for t,c in [('📋复制选中',self.copy),('📋复制整表',self.copy_all),('💾导出CSV',self.export_csv),('📗导出Excel',self.export_xlsx),('📊条件统计',self.stats),('💰批量报价',self.quote),('📈历史对比',self.compare)]:ttk.Button(act,text=t,command=c).pack(side='left',padx=3)
  ttk.Label(act,text='结果包含日期、条件、单位、备注、来源图片',foreground='#666').pack(side='right')
  f=ttk.Frame(self.root);f.pack(fill='both',expand=True,padx=10);self.tree=ttk.Treeview(f,columns=[x[0] for x in COLS],show='headings',selectmode='extended')
  for c,h,w in COLS:self.tree.heading(c,text=h);self.tree.column(c,width=w,anchor='center' if c in {'data_date','category','subtype','price'} else 'w')
  y=ttk.Scrollbar(f,orient='vertical',command=self.tree.yview);x=ttk.Scrollbar(f,orient='horizontal',command=self.tree.xview);self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set);self.tree.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew');f.grid_rowconfigure(0,weight=1);f.grid_columnconfigure(0,weight=1)
  self.tree.bind('<Control-c>',self.copy);self.tree.bind('<Control-C>',self.copy);self.tree.bind('<Control-a>',lambda e:(self.tree.selection_set(self.tree.get_children()),'break')[1]);self.tree.bind('<Control-A>',lambda e:(self.tree.selection_set(self.tree.get_children()),'break')[1]);self.tree.bind('<Button-3>',self.menu);self.tree.bind('<Double-1>',self.detail)
 def load(self):
  self.s.load();self.meta.config(text=f'最新：{self.s.latest or "无"} · 快照 {len(self.s.dates)} · 已验证价格行 {len(self.s.rows)} · 图片 {sum(clean(r.get("include")) in TRUE for r in self.s.manifest)}');self.search()
  self.status.config(text=('数据校验提示：'+self.s.errors[0] if self.s.errors else '数据校验通过'))
 def search(self):
  self.rows=self.s.search(self.q.get(),self.cat.get(),self.hist.get());self.tree.delete(*self.tree.get_children())
  for i,r in enumerate(self.rows):self.tree.insert('', 'end',iid=str(i),values=tuple(r.get(c,'') for c,_,_ in COLS),tags=('odd' if i%2 else ''))
  if clean(self.q.get()):self.target.config(text=f'搜索目标：{clean(self.q.get())} · {len({(r["brand"],r["series"],r["model"]) for r in self.rows})} 个目标 · {len(self.rows)} 条价格条件')
  else:self.target.config(text='当前快照：按图片原始价格条件逐行显示')
  self.status.config(text=f'结果 {len(self.rows)} 条' + (f' · 数据问题 {len(self.s.errors)}' if self.s.errors else ''))
 def selected(self): return [self.rows[int(i)] for i in self.tree.selection() if i.isdigit() and int(i)<len(self.rows)]
 def table(self,rows,header=True):
  lines=['\t'.join(h for _,h,_ in COLS)] if header else [];lines += ['\t'.join(str(r.get(c,'') if isinstance(r,dict) else r[i]) for i,(c,_,_) in enumerate(COLS)) for r in rows];return '\r\n'.join(lines)
 def copy(self,event=None):
  rows=self.selected()
  if rows:self.root.clipboard_clear();self.root.clipboard_append(self.table(rows));self.root.update();self.status.config(text=f'已复制 {len(rows)} 条')
  return 'break' if event else None
 def copy_all(self):
  if self.rows:self.root.clipboard_clear();self.root.clipboard_append(self.table(self.rows));self.root.update();self.status.config(text=f'已复制 {len(self.rows)} 条')
 def export_csv(self):
  rows=self.selected() or self.rows
  if not rows:return messagebox.showinfo('导出','没有结果')
  p=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='数码价格查询结果.csv')
  if p:
   with open(p,'w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows([tuple(h for _,h,_ in COLS)]+[[r.get(c,'') for c,_,_ in COLS] for r in rows])
 def export_xlsx(self):
  if Workbook is None:return messagebox.showerror('依赖','需要 openpyxl')
  rows=self.selected() or self.rows
  if not rows:return messagebox.showinfo('导出','没有结果')
  p=filedialog.asksaveasfilename(defaultextension='.xlsx',initialfile='数码价格查询.xlsx')
  if not p:return
  wb=Workbook();ws=wb.active;ws.title='查询结果';ws.append([h for _,h,_ in COLS]);[ws.append([r.get(c,'') for c,_,_ in COLS]) for r in rows]
  for c in ws[1]:c.font=Font(bold=True)
  for i,(_,_,w) in enumerate(COLS,1):ws.column_dimensions[get_column_letter(i)].width=max(12,min(42,w/8))
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions;wb.save(p)
 def stats(self):
  rs=self.selected() or self.rows
  if not rs:return messagebox.showinfo('统计','没有结果')
  g={}
  for r in rs:
   n=num(r['price'])
   if n is not None:g.setdefault(r['condition'],[]).append(n)
  text='\n'.join(f'{k}：{min(v):g}～{max(v):g}，平均 {sum(v)/len(v):.2f}' for k,v in g.items());messagebox.showinfo('动态价格条件统计',f'记录 {len(rs)} 条\n条件 {len(g)} 种\n\n{text}')
 def quote(self):
  rs=self.selected()
  if not rs:return messagebox.showinfo('批量报价','请先选择结果')
  cs=[]
  for r in rs:
   if r['condition'] not in cs:cs.append(r['condition'])
  w=tk.Toplevel(self.root);w.title('批量报价 · 动态条件');w.geometry('560x300');ttk.Label(w,text=f'已选择 {len(rs)} 条价格记录',font=('微软雅黑',14,'bold')).pack(anchor='w',padx=20,pady=18);f=ttk.Frame(w);f.pack(fill='x',padx=20);ttk.Label(f,text='条件').grid(row=0,column=0,pady=8);cv=tk.StringVar(value=cs[0]);ttk.Combobox(f,textvariable=cv,values=cs,state='readonly',width=25).grid(row=0,column=1);ttk.Label(f,text='数量').grid(row=1,column=0,pady=8);q=tk.StringVar(value='1');ttk.Spinbox(f,from_=1,to=99999,textvariable=q,width=10).grid(row=1,column=1);out=ttk.Label(w,text='');out.pack(anchor='w',padx=20,pady=15)
  def calc():
   try:n=int(q.get());assert n>0
   except:return messagebox.showerror('数量','必须为正整数',parent=w)
   a=[r for r in rs if r['condition']==cv.get() and num(r['price']) is not None];out.config(text=f'条件：{cv.get()}\n有效：{len(a)}/{len(rs)}\n数量：{n}\n合计：{sum(num(r["price"])*n for r in a):g} 元')
  ttk.Button(w,text='计算',command=calc).pack(side='left',padx=20);ttk.Button(w,text='关闭',command=w.destroy).pack(side='right',padx=20);calc()
 def compare(self):
  if len(self.s.dates)<2:return messagebox.showinfo('历史对比','当前只有一个日期快照；增加新的 YYYY-MM-DD.csv 后自动按同型号+同价格条件对齐')
  ds=self.s.dates;w=tk.Toplevel(self.root);w.title('历史价格对比 · 同条件');w.geometry('1300x700');lb=tk.Listbox(w,selectmode='extended',height=min(6,len(ds)),exportselection=False);[lb.insert('end',d) for d in ds];lb.pack(fill='x',padx=15,pady=10);lb.selection_set(max(0,len(ds)-2),len(ds)-1);ct=ttk.Treeview(w,show='headings');ct.pack(fill='both',expand=True,padx=15)
  def run():
   picks=[ds[i] for i in lb.curselection()]
   if len(picks)<2:return
   maps=[{(key(r['brand']),key(r['series']),key(r['model']),key(r['condition']),key(r['subtype']),key(r['unit'])):r for r in self.s.snapshots[d]} for d in picks];common=set.intersection(*(set(m) for m in maps));heads=['品牌','系列','型号','价格条件']+picks+['差价'];ct['columns']=[str(i) for i in range(len(heads))];[ct.heading(str(i),text=h) for i,h in enumerate(heads)];ct.delete(*ct.get_children())
   for k in sorted(common):
    a=[maps[i][k] for i in range(len(picks))];ps=[num(r['price']) for r in a];diff='-' if ps[0] is None or ps[-1] is None else f'{ps[-1]-ps[0]:g}';ct.insert('','end',values=[a[0]['brand'],a[0]['series'],a[0]['model'],a[0]['condition']]+[r['price'] for r in a]+[diff])
  ttk.Button(w,text='重新对比',command=run).pack(pady=8);run()
 def sources(self):
  w=tk.Toplevel(self.root);w.title('图片来源文件结构');w.geometry('1250x720');t=ttk.Treeview(w,columns=('date','cat','status','img','rows'),show='headings');t.pack(fill='both',expand=True,padx=10,pady=10)
  for c,h in [('date','日期'),('cat','分类'),('status','状态'),('img','来源图片'),('rows','已入库行数')]:t.heading(c,text=h)
  counts={}
  for r in self.s.rows:counts[(r['data_date'],r['source_image'])]=counts.get((r['data_date'],r['source_image']),0)+1
  for r in sorted(self.s.manifest,key=lambda x:(x.get('data_date',''),x.get('source_image',''))): t.insert('','end',values=(r.get('data_date',''),r.get('category',''),r.get('status',''),r.get('source_image',''),counts.get((r.get('data_date',''),r.get('source_image','')),0)))
 def _picked_one(self):
  rows=self.selected();return rows[0] if rows else None
 def detail(self,event=None):
  r=self._picked_one()
  if not r:return
  w=tk.Toplevel(self.root);w.title('图片事实记录详情');w.geometry('760x620');txt=tk.Text(w,font=('微软雅黑',11));txt.pack(fill='both',expand=True,padx=12,pady=12)
  txt.insert('1.0','\n'.join(f'{k}: {r.get(k,"")}' for k in FIELDS));txt.config(state='disabled')
 def menu(self,event):
  row=self.tree.identify_row(event.y)
  if row:self.tree.selection_set(row)
  m=tk.Menu(self.root,tearoff=0);m.add_command(label='复制选中',command=self.copy);m.add_command(label='查看详情',command=self.detail);m.tk_popup(event.x_root,event.y_root)
 def open_dir(self):
  try:
   if os.name=='nt':os.startfile(self.d)
   elif sys.platform=='darwin':subprocess.Popen(['open',self.d])
   else:subprocess.Popen(['xdg-open',self.d])
  except Exception as e:messagebox.showerror('数据目录',str(e))
def main():
 root=tk.Tk();App(root);root.mainloop()
if __name__=='__main__':main()
