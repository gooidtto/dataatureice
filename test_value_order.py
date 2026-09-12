from value_order import value_rank, sort_rows


def r(condition, category="手机"):
    return {"category": category, "condition": condition, "model": "T", "brand": "X", "series": "S", "data_date": "2026-01-01", "record_id": condition, "price": "999999"}


def test_price_never_controls_rank():
    good=r("开机靓机好"); bad=r("废板·整机")
    assert value_rank(good) > value_rank(bad)
    ordered=sort_rows([bad,good])
    assert ordered[0]["condition"] == "开机靓机好"


def test_outer_screen_damage_beats_inner_screen_failure():
    assert value_rank(r("开机屏好外屏碎")) > value_rank(r("开机屏内屏坏"))


def test_transaction_form_is_not_promoted_by_price():
    assert value_rank(r("开机屏好")) > value_rank(r("点数"))
