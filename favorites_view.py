"""Favorites window with canonical model/date grouping and export spacing."""
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from search_display import build_result_blocks

COLS=(('data_date','数据日期',105),('category','分类',70),('subtype','子类型',75),('brand','品牌',110),('series','系列',110),('model','型号',250),('condition','价格条件',175),('price','价格',85),('unit','单位',85),('note','备注',260),('source_image','来源图片',150))

def _ordered_blocks(rows):
    return build_result_blocks(list(rows or []))

def _copy_grouped(self,rows):
    rows=list(rows or [])
    if not rows:return
    lines=['\t'.join(h for _,h,_ in COLS)];last_model=last_date=None
    for b in _ordered_blocks(rows):
        model,date=b.get('_model_key'),b.get('_period_key')
        if last_model is not None and model!=last_model:lines += ['\t'*(len(COLS)-1)]*2
        elif last_date is not None and date!=last_date:lines.append('\t'*(len(COLS)-1))
        for r in b.get('_rows',[]):lines.append('\t'.join(str(r.get(c,'')) for c,_,_ in COLS))
        last_model,last_date=model,date
    self.root.clipboard_clear();self.root.clipboard_append('\r\n'.join(lines));self.root.update();self.status.config(text=f'已复制 {len(rows)} 条收藏，保留分组与间隔')

def _export_grouped(self,rows,xlsx):
    rows=list(rows or [])
    if not rows:return
    ext='.xlsx' if xlsx else '.csv';initial='数码价格收藏.xlsx' if xlsx else '数码价格收藏结果.csv'
    types=[('Excel 文件','*.xlsx')] if xlsx else [('CSV 文件','*.csv'),('所有文件','*.*')]
    path=filedialog.asksaveasfilename(parent=self.root,title='导出收藏结果',defaultextension=ext,filetypes=types,initialfile=initial)
    if not path:return
    if not path.lower().endswith(ext):path+=ext
    try:
        blocks=_ordered_blocks(rows)
        if xlsx:
            wb=Workbook();ws=wb.active;ws.title='收藏结果'
            for col,(_,title,_) in enumerate(COLS,1):ws.cell(1,col,title).font=Font(bold=True)
            ri=2;last_model=last_date=None
            for b in blocks:
                model,date=b.get('_model_key'),b.get('_period_key')
                if last_model is not None and model!=last_model:ri+=2
                elif last_date is not None and date!=last_date:ri+=1
                for r in b.get('_rows',[]):
                    for col,(field,_,_) in enumerate(COLS,1):ws.cell(ri,col,r.get(field,''))
                    ri+=1
                last_model,last_date=model,date
            for col,(_,_,width) in enumerate(COLS,1):ws.column_dimensions[get_column_letter(col)].width=max(12,min(42,width/8))
            ws.freeze_panes='A2';wb.save(path)
        else:
            with open(path,'w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f);w.writerow([h for _,h,_ in COLS]);last_model=last_date=None
                for b in blocks:
                    model,date=b.get('_model_key'),b.get('_period_key')
                    if last_model is not None and model!=last_model:w.writerow([]);w.writerow([])
                    elif last_date is not None and date!=last_date:w.writerow([])
                    for r in b.get('_rows',[]):w.writerow([r.get(c,'') for c,_,_ in COLS])
                    last_model,last_date=model,date
        messagebox.showinfo('导出成功',f'已导出 {len(rows)} 条收藏\n{path}',parent=self.root);self.status.config(text=f'已导出收藏 {len(rows)} 条，保留分组与间隔')
    except Exception as exc:messagebox.showerror('导出失败',f'无法写入文件：\n{path}\n\n{exc}',parent=self.root)

def show_favorites_matrix(self):
    rows=list(self.fav.dedupe());w=self._new_window('⭐ 我的收藏','1650x760',(1150,560))
    ttk.Label(w,text=f'我的收藏 · {len(rows)} 条 · 保持收藏顺序与搜索分组规则',font=('微软雅黑',12,'bold')).pack(anchor='w',padx=12,pady=10)
    host=ttk.Frame(w,padding=(12,0,12,10));host.pack(fill='both',expand=True);canvas=tk.Canvas(host,highlightthickness=0,bd=0);bar=ttk.Scrollbar(host,orient='vertical',command=canvas.yview);canvas.configure(yscrollcommand=bar.set);canvas.grid(row=0,column=0,sticky='nsew');bar.grid(row=0,column=1,sticky='ns');host.grid_rowconfigure(0,weight=1);host.grid_columnconfigure(0,weight=1);inner=tk.Frame(canvas);wid=canvas.create_window((0,0),window=inner,anchor='nw');inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(wid,width=e.width))
    blocks=_ordered_blocks(rows);mapping={};trees=[]
    for i,b in enumerate(blocks):
        if i:tk.Frame(inner,height=8 if b['_model_index']==blocks[i-1]['_model_index'] else 16).pack(fill='x')
        cols=tuple(b.get('_columns') or ());tree=ttk.Treeview(inner,columns=[c[0] for c in cols]+['favorite'],show='headings',height=1,selectmode='browse')
        for field,title,width in cols:tree.heading(field,text=title);tree.column(field,width=width,minwidth=60,anchor='center' if field=='data_date' or field.startswith('condition_') else 'w',stretch=False)
        tree.heading('favorite',text='收藏');tree.column('favorite',width=110,anchor='center',stretch=False);iid=f'favorite-{i}';tree.insert('','end',iid=iid,values=[b.get(field,'') for field,_,_ in cols]+['★ 已收藏']);tree.bind('<Double-1>',lambda e,bb=b:self.detail_rows(bb.get('_rows',[])));tree.bind('<Button-3>',lambda e,bb=b,tt=tree:_favorite_menu(self,e,tt,bb,w));tree.pack(fill='x',expand=True);trees.append(tree);mapping[iid]=b
    def selected_blocks():
        return [mapping[i] for t in trees for i in t.selection() if mapping.get(i)]
    def selected_rows():return [r for b in selected_blocks() for r in b.get('_rows',[])]
    def all_rows():return [r for b in blocks for r in b.get('_rows',[])]
    def remove_selected():
        picked=selected_rows()
        if not picked:return messagebox.showinfo('我的收藏','请先选择要移除的收藏',parent=w)
        self.fav.remove(picked);w.destroy();self.show_favorites();self.status.config(text=f'已移除收藏 {len(picked)} 条')
    bar=ttk.Frame(w,padding=(12,0,12,10));bar.pack(fill='x');ttk.Button(bar,text='查看详情',command=lambda:self.detail_rows(selected_rows() or all_rows())).pack(side='left',padx=4);ttk.Button(bar,text='移除收藏',command=remove_selected).pack(side='left',padx=4);ttk.Button(bar,text='复制',command=lambda:_copy_grouped(self,selected_rows() or all_rows())).pack(side='left',padx=4);ttk.Button(bar,text='导出CSV',command=lambda:_export_grouped(self,selected_rows() or all_rows(),False)).pack(side='left',padx=4);ttk.Button(bar,text='导出Excel',command=lambda:_export_grouped(self,selected_rows() or all_rows(),True)).pack(side='left',padx=4);ttk.Button(bar,text='关闭',command=w.destroy).pack(side='right',padx=4);w.bind('<Escape>',lambda e:w.destroy());return w

def _favorite_menu(self,event,tree,block,window):
    iid=tree.identify_row(event.y)
    if not iid:return
    tree.selection_set(iid);rows=list(block.get('_rows',[]));m=tk.Menu(tree,tearoff=False);m.add_command(label='查看详情',command=lambda:self.detail_rows(rows));m.add_command(label='移除收藏',command=lambda:_remove_block(self,window,rows));m.add_command(label='复制',command=lambda:_copy_grouped(self,rows));m.add_command(label='导出CSV',command=lambda:_export_grouped(self,rows,False));m.add_command(label='导出Excel',command=lambda:_export_grouped(self,rows,True));m.tk_popup(event.x_root,event.y_root)

def _remove_block(self,window,rows):
    if not rows:return
    self.fav.remove(rows);window.destroy();self.show_favorites();self.status.config(text=f'已移除收藏 {len(rows)} 条')
