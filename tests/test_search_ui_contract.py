import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('phone_search', ROOT / 'phone_search.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(**kw):
    r = {k: '' for k in mod.FIELDS}
    r.update({'data_date':'2026-08-31','category':'手机','subtype':'device','brand':'A','series':'S','model':'M','condition':'好','price':'100','unit':'元','verified':'1'})
    r.update(kw)
    return r


def test_one_click_favorite_is_content_level_deduped():
    fav = mod.Favorites('unused')
    first = row(record_id='one')
    second = row(record_id='two')
    added, duplicate = fav.add([first, second])
    assert len(added) == 1
    assert len(duplicate) == 1
    assert len(fav.items) == 1


def test_favorite_content_key_changes_for_condition_or_price():
    fav = mod.Favorites('unused')
    a = row(condition='开机屏好', price='100')
    b = row(condition='开机屏坏', price='80')
    assert fav.identity(a) != fav.identity(b)
