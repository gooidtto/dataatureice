from pathlib import Path


APP_ACTIONS = Path(__file__).resolve().parents[1] / "app_actions.py"
UI_BOOTSTRAP = Path(__file__).resolve().parents[1] / "ui_bootstrap.py"


def test_optional_actions_use_window_factory():
    source = APP_ACTIONS.read_text(encoding="utf-8")
    bootstrap = UI_BOOTSTRAP.read_text(encoding="utf-8")

    assert "def _new_window(self, title, geometry=None, minsize=None):" in source
    assert "def show_compare(self, rows, targets=None):" in source
    assert "def detail_rows(self, rs):" in source
    assert '"show_compare":show_compare' in source
    assert '"detail_rows":detail_rows' in source
    assert "tk.Toplevel(" not in source
    assert "phone_search.tk.Toplevel" not in bootstrap
    assert "def _new_window(self,title,geometry=None,minsize=None):" in bootstrap
