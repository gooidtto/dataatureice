from pathlib import Path


UI_BOOTSTRAP = Path(__file__).resolve().parents[1] / "ui_bootstrap.py"


def test_search_ui_overrides_live_on_explicit_app_subclass():
    source = UI_BOOTSTRAP.read_text(encoding="utf-8")

    assert "class SearchApp(phone_search.App):" in source
    assert "install_app_actions(SearchApp)" in source
    assert "phone_search.App.ui=" not in source
    assert "phone_search.App.search=" not in source
    assert "phone_search.App.render=" not in source
    assert "phone_search.App.load=" not in source
    assert "phone_search.App.clear_search=" not in source
    assert "phone_search.App.on_tree_click=" not in source
    assert "phone_search.App.favorite_groups=" not in source
