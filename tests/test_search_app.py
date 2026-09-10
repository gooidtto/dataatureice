import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('phone_search', HERE/'phone_search.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
def row(**kw):
    r={k:'' for k in mod.FIELDS}
    r.update({'data_date':'2026-08-31','category':'phone','subtype':'device','brand':'A','series':'S','model':'M','condition':'好','price':'100','unit':'CNY/台','verified':'1'})
    r.update(kw); return r
def test_category_canonical():
    assert mod.CAT['phone']=='手机'
    assert mod.CAT['电脑']=='电脑'
def test_num_rejects_slash_value():
    assert mod.num('/') is None
    assert mod.num('0/0') is None
    assert mod.num('12.5')==12.5
def test_search_matches_alias_and_model_code(tmp_path):
    import csv
    p=tmp_path/'2026-08-31.csv'
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=mod.FIELDS); w.writeheader(); w.writerow(row(alias='别名X',model_code='ABC123'))
    s=mod.Store(str(tmp_path)); s.load()
    assert len(s.search('别名X'))==1
    assert len(s.search('ABC123'))==1
def test_history_compare_key_distinguishes_unit_and_subtype():
    assert mod.rid(row(unit='CNY/台',subtype='device')) != mod.rid(row(unit='CNY/kg',subtype='component'))
