import csv
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('phone_search',HERE/'phone_search.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def row(**kw):
 r={k:'' for k in mod.FIELDS};r.update({'data_date':'2026-08-31','category':'手机','subtype':'device','brand':'A','series':'S','model':'M','condition':'好','price':'100','unit':'CNY/台','verified':'1'});r.update(kw);return r
def test_category_canonical():
 assert mod.CAT['phone']=='手机';assert mod.CAT['电脑']=='电脑'
def test_num_rejects_slash_value():
 assert mod.num('/') is None;assert mod.num('0/0') is None;assert mod.num('12.5')==12.5
def test_search_matches_alias_and_model_code(tmp_path):
 p=tmp_path/'2026-08-31.csv'
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=mod.FIELDS);w.writeheader();w.writerow(row(alias='别名X',model_code='ABC123'))
 s=mod.Store(str(tmp_path));s.load();assert len(s.search('别名X'))==1;assert len(s.search('ABC123'))==1
def test_history_compare_key_distinguishes_subtype():
 assert mod.rid(row(subtype='device'))!=mod.rid(row(subtype='component'))
def test_search_order_is_new_date_then_high_price(tmp_path):
 for d,prices in [('2026-08-25',['300','200']),('2026-08-31',['150','500'])]:
  p=tmp_path/f'{d}.csv'
  with p.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=mod.FIELDS);w.writeheader()
   for i,price in enumerate(prices):w.writerow(row(data_date=d,price=price,record_id=f'{d}-{i}'))
 s=mod.Store(str(tmp_path));s.load();rs=s.search('M');assert [r['data_date'] for r in rs]==['2026-08-31','2026-08-31','2026-08-25','2026-08-25'];assert [r['price'] for r in rs[:2]]==['500','150']
def test_history_matches_same_model_across_model_code_changes(tmp_path):
 rows=[row(data_date='2026-08-25',record_id='old',model_code='OLD',price='100'),row(data_date='2026-08-31',record_id='new',model_code='NEW',price='120')]
 for r in rows:
  p=tmp_path/f'{r["data_date"]}.csv'
  with p.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=mod.FIELDS);w.writeheader();w.writerow(r)
 s=mod.Store(str(tmp_path));s.load();rs=s.history([rows[1]]);assert {r['record_id'] for r in rs}=={'old','new'}
def test_history_persists_deduped_at_least_twenty_capacity(tmp_path):
 h=mod.JsonList(str(tmp_path/'history.json'))
 for i in range(25):h.add(f'query-{i}')
 h.add('QUERY-10');h.load();assert len(h.items)==25;assert h.items[0]=='QUERY-10';assert len({mod.key(x) for x in h.items})==25
 h.clear();assert not (tmp_path/'history.json').exists();h.load();assert h.items==[]
def test_favorites_persist_and_dedupe(tmp_path):
 f=mod.Favorites(str(tmp_path/'favorites.json'));r=row(record_id='r1',condition='好',price='100');f.add([r,r]);assert len(f.items)==1;f2=mod.Favorites(str(tmp_path/'favorites.json'));assert len(f2.items)==1;f2.remove([r]);assert f2.items==[]
