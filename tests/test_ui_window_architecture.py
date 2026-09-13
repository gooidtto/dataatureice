from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui_bootstrap.py"
ACTIONS = ROOT / "app_actions.py"
PHONE = ROOT / "phone_search.py"


def test_search_app_owns_window_factory_without_global_tk_patch():
    ui = UI.read_text(encoding="utf-8")
    assert "def _new_window(self,title,geometry=None,minsize=None):" in ui
    assert "_new_window=_new_window" in ui
    assert "phone_search.tk.Toplevel=standardized_toplevel" not in ui
    assert "_real_toplevel" not in ui


def test_result_double_click_selects_matrix_iid_before_detail():
    ui = UI.read_text(encoding="utf-8")
    assert "_select_result_iid(self,iid);self.detail();return 'break'" in ui


def test_app_actions_do_not_bypass_window_factory():
    actions = ACTIONS.read_text(encoding="utf-8")
    assert "def _new_window(self, title, geometry=None, minsize=None):" in actions
    assert "w = tk.Toplevel(self.root)" not in actions
    assert "_new_window(self," in actions
    assert "setattr(App,name,fn)" in actions


def test_favorite_popup_actions_match_app_helpers():
    actions = ACTIONS.read_text(encoding="utf-8")
    phone = PHONE.read_text(encoding="utf-8")
    assert "self.copy_popup(selected_rows() or all_rows())" in actions
    assert "self.export_popup(selected_rows() or all_rows(),False)" in actions
    assert "def copy_popup(self,rs):" in phone
    assert "def export_popup(self,rs,xlsx):" in phone
    assert "self.fav.remove(rows)" in actions
    assert "def remove(self,rows):" in phone
