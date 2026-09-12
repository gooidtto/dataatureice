import importlib.util
from pathlib import Path

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('phone_search',ROOT/'phone_search.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def row(**kw):
 r={k:'' for k in mod.FIELDS};r.update({'data_date':'2026-08-31','category':'手机','subtype':'device','brand':'A','series':'S','model':'M','condition':'好','price':'100','unit':'元','verified':'1'});r.update(kw);return r

def test_one_click_favorite_is_content_level_deduped():
 fav=mod.Favorites('unused');first=row(record_id='one');second=row(record_id='two');added,duplicate=fav.add([first,second]);assert len(added)==1;assert len(duplicate)==1;assert len(fav.items)==1

def test_favorite_content_key_changes_for_condition_or_price():
 fav=mod.Favorites('unused');a=row(condition='开机屏好',price='100');b=row(condition='开机屏坏',price='80');assert fav.identity(a)!=fav.identity(b)

def test_favorite_groups_keep_same_model_together_and_dates_descending():
 spec2=importlib.util.spec_from_file_location('ui_bootstrap',ROOT/'ui_bootstrap.py');ui=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(ui)
 app=object.__new__(mod.App);app.fav=mod.Favorites('unused');app.fav.items=[row(record_id='m2-old',model='M2',data_date='2026-08-20',price='80'),row(record_id='m1-old',model='M1',data_date='2026-08-20',price='70'),row(record_id='m1-new',model='M1',data_date='2026-08-31',price='100'),row(record_id='m2-new',model='M2',data_date='2026-08-31',price='110')]
 display=ui.favorite_groups(app)
 display=[item for item in display if not item.get('_separator')]
 # Both models have identical condition/value ranks, so canonical tie-breaking
 # orders the model name lexically. Historical price must not determine order.
 assert [item['identity'].split()[-1] for item in display]==['M1','M1','M2','M2']
 assert [item['data_date'] for item in display]==['2026-08-31','2026-08-20','2026-08-31','2026-08-20']
