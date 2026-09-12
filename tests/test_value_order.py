from value_order import value_rank, sort_rows


def row(condition, category="手机"):
    return {"category": category, "condition": condition, "model": "T", "brand": "X", "series": "S", "data_date": "2026-01-01", "record_id": condition, "price": "999999"}


def test_price_never_controls_rank():
    ordered = sort_rows([row("废板·整机"), row("开机靓机好")])
    assert ordered[0]["condition"] == "开机靓机好"
    assert value_rank(row("开机靓机好")) > value_rank(row("废板·整机"))


def test_outer_screen_damage_is_better_than_inner_screen_failure():
    assert value_rank(row("开机屏好外屏碎")) > value_rank(row("开机屏内屏坏"))


def test_transaction_form_is_not_promoted_by_price():
    assert value_rank(row("开机屏好")) > value_rank(row("点数"))
