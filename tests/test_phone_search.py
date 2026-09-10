import csv
import importlib.util
from pathlib import Path

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('phone_search',ROOT/'phone_search.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def test_num_rejects_range_or_slash_price():
    assert mod.num('12/15') is None
    assert mod.num('/') is None
    assert mod.num('12.5') == 12.5

def test_key_normalizes_model_spelling():
    assert mod.key('iPhone 6-SP') == mod.key('iphone6sp')

def _row(rid,date,model,price,condition='开机屏好'):
    r={k:'' for k in mod.FIELDS}
    r.update(record_id=rid,data_date=date,category='手机',subtype='',brand='Realme',series='X系列',model=model,condition=condition,price=str(price),unit='元',verified='1')
    return r

def test_search_is_all_dates_newest_first_then_price(tmp_path):
    d=tmp_path/'data'; (d/'snapshots'/'2026-08-25').mkdir(parents=True); (d/'snapshots'/'2026-08-31').mkdir(parents=True)
    for date, rows in {
        '2026-08-31':[_row('1','2026-08-31','Realme X7',160),_row('2','2026-08-31','Realme X7 Pro',170),_row('3','2026-08-31','Realme X7',170)],
        '2026-08-25':[_row('4','2026-08-25','Realme X7',150),_row('5','2026-08-25','Realme X7',140)]}.items():
        p=d/'snapshots'/date/'part-01.csv'
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=mod.FIELDS);w.writeheader();w.writerows(rows)
    s=mod.Store(str(d));s.load(); got=s.search('Realme X7')
    assert [x['data_date'] for x in got]==['2026-08-31']*3+['2026-08-25']*2
    assert [x['price'] for x in got[:3]]==['170','170','160']

def test_history_matches_same_model_across_dates():
    s=mod.Store('unused');s.rows=[_row('1','2026-08-31','Realme X7',170),_row('2','2026-08-25','Realme X7',150),_row('3','2026-08-31','Realme X8',200)]
    got=s.history([s.rows[0]])
    assert [(x['data_date'],x['model']) for x in got]==[('2026-08-31','Realme X7'),('2026-08-25','Realme X7')]

def test_search_history_deduplicates(tmp_path):
    h=mod.Hist(str(tmp_path/'search_history.json'))
    h.add('Realme X7');h.add('iPhone 15');h.add('realme-x7')
    assert len(h.items)==2
    assert mod.key(h.items[0])==mod.key('Realme X7')
