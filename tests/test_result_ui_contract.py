import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(module, name):
    return next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_window_helper_signatures_are_ast_stable():
    module = _load_module(ROOT / "app_actions.py")
    assert [arg.arg for arg in _function(module, "show_compare").args.args] == [
        "self", "rows", "targets"
    ]
    assert [arg.arg for arg in _function(module, "detail_rows").args.args] == [
        "self", "rs"
    ]


def test_search_display_contract_is_block_local():
    from search_display import normalize_search_results

    rows = [
        {
            "data_date": "2026-08-31",
            "category": "手机",
            "brand": "OPPO",
            "series": "A",
            "model": "A59",
            "model_code": "",
            "condition": "开机屏好",
            "price": "70",
            "source_image": "oppo.jpg",
        },
        {
            "data_date": "2026-08-31",
            "category": "手机",
            "brand": "OPPO",
            "series": "A",
            "model": "A59",
            "model_code": "",
            "condition": "不开机",
            "price": "60",
            "source_image": "oppo.jpg",
        },
        {
            "data_date": "2026-08-25",
            "category": "手机",
            "brand": "OPPO",
            "series": "A",
            "model": "A59",
            "model_code": "",
            "condition": "开机屏好",
            "price": "65",
            "source_image": "oppo.jpg",
        },
    ]
    result = normalize_search_results(rows)
    blocks = [item for item in result if not item.get("_separator")]
    assert len(blocks) == 2
    assert all(item["_rows"] for item in blocks)
    assert all(item["_columns"] for item in blocks)
    assert blocks[0]["_period_key"] == "2026-08-31"
    assert blocks[1]["_period_key"] == "2026-08-25"
    assert set(item["_model_key"] for item in blocks) == {("手机", "OPPO", "A", "A59", "")}


def test_favorite_groups_contract_matches_show_favorites_consumer():
    import ui_bootstrap

    class FakeFavorites:
        def dedupe(self):
            return [
                {
                    "data_date": "2026-08-31",
                    "category": "手机",
                    "brand": "OPPO",
                    "series": "A",
                    "model": "A59",
                    "model_code": "",
                    "condition": "开机屏好",
                },
                {
                    "data_date": "2026-08-25",
                    "category": "手机",
                    "brand": "OPPO",
                    "series": "A",
                    "model": "A59",
                    "model_code": "",
                    "condition": "不开机",
                },
            ]

    class FakeApp:
        fav = FakeFavorites()

    groups = ui_bootstrap.favorite_groups(FakeApp())
    assert len(groups) == 1
    key, blocks = groups[0]
    assert key[:4] == ("手机", "OPPO", "A", "A59")
    assert len(blocks) == 2
    assert blocks[0][0]["data_date"] == "2026-08-31"
    assert blocks[1][0]["data_date"] == "2026-08-25"
