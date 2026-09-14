from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("detail_compare_view", ROOT / "detail_compare_view.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(model="M", date="2026-08-31", condition="好", price="100", **extra):
    r = {"category": "手机", "subtype": "device", "brand": "A", "series": "S", "model": model,
         "data_date": date, "condition": condition, "price": price}
    r.update(extra)
    return r


def test_condition_detail_does_not_rank_by_price():
    rows = [row(condition="好", price="1"), row(condition="开机屏坏", price="9999")]
    ordered = mod._condition_key(rows[0]), mod._condition_key(rows[1])
    assert ordered[0] < ordered[1]


def test_condition_compare_source_uses_current_period_without_reordering_input():
    source = (ROOT / "detail_compare_view.py").read_text(encoding="utf-8")
    assert 'title = "条件比价 · 当前搜索详细信息"' in source
    assert 'current = [r for r in rows if _date_key(r) == latest] or rows' in source


def test_history_compare_source_uses_all_periods_and_preserves_canonical_order():
    source = (ROOT / "detail_compare_view.py").read_text(encoding="utf-8")
    assert 'title = "历史对比 · 当前搜索不同时期详细信息"' in source
    assert 'canonical = [r for r in getattr(app.s, "rows", []) if id(r) in allowed]' in source
    assert 'history = [r for date in dates for r in canonical if _date_key(r) == date]' in source
