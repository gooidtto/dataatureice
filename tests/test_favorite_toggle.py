import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('phone_search', ROOT / 'phone_search.py')
phone_search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phone_search)

toggle_spec = importlib.util.spec_from_file_location('favorite_toggle', ROOT / 'favorite_toggle.py')
toggle_mod = importlib.util.module_from_spec(toggle_spec)
toggle_spec.loader.exec_module(toggle_mod)


def row(**kw):
    r = {k: '' for k in phone_search.FIELDS}
    r.update({
        'data_date': '2026-08-31',
        'category': '手机',
        'subtype': 'device',
        'brand': 'A',
        'series': 'S',
        'model': 'M',
        'condition': '好',
        'price': '100',
        'unit': '元',
        'verified': '1',
    })
    r.update(kw)
    return r


def test_one_click_favorite_toggles_remove_and_add(tmp_path):
    fav = phone_search.Favorites(str(tmp_path / 'favorites.json'))
    target = row(record_id='toggle-1')
    fav.add([target])

    rendered = []
    messages = []
    app = SimpleNamespace(
        fav=fav,
        rows=[target],
        render=lambda rows: rendered.append(rows),
        toast=lambda text: messages.append(text),
    )

    assert toggle_mod.toggle_favorite(app, target) is False
    assert not fav.has(target)
    assert messages[-1] == '已移除收藏'
    assert rendered

    added = []
    app.addToFavorites = lambda rows: (added.append(rows), fav.add(rows))[1]
    assert toggle_mod.toggle_favorite(app, target) is True
    assert fav.has(target)
    assert added == [[target]]


def test_one_click_uses_content_identity_not_record_id(tmp_path):
    fav = phone_search.Favorites(str(tmp_path / 'favorites.json'))
    saved = row(record_id='old-id')
    same_content = row(record_id='new-id')
    fav.add([saved])

    rendered = []
    messages = []
    app = SimpleNamespace(
        fav=fav,
        rows=[same_content],
        render=lambda rows: rendered.append(rows),
        toast=lambda text: messages.append(text),
    )

    assert toggle_mod.toggle_favorite(app, same_content) is False
    assert not fav.items
    assert messages[-1] == '已移除收藏'
