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
    assert "def _new_window(self, title, geometry=None,minsize=None):" in actions or "def _new_window(self, title, geometry=None, minsize=None):" in actions
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


def test_favorite_action_is_installed_on_search_app():
    actions = ACTIONS.read_text(encoding="utf-8")
    assert "def addToFavorites(self, rows):" in actions
    assert '"addToFavorites":addToFavorites' in actions
    assert "added, duplicate = self.fav.add(rows)" in actions
    assert "已经收藏" in actions


def test_main_window_is_withdrawn_during_app_initialization():
    actions = ACTIONS.read_text(encoding="utf-8")
    assert "def _install_window_lifecycle(App):" in actions
    assert "root.withdraw()" in actions
    assert "original_init(self, root, *args, **kwargs)" in actions
    assert "root.deiconify()" in actions
    assert "App.__init__ = _init" in actions


def test_child_window_is_hidden_until_configuration_finishes():
    actions = ACTIONS.read_text(encoding="utf-8")
    assert "w.withdraw()" in actions
    assert "self.root.after_idle(lambda: _show_window(w))" in actions
    assert "w.deiconify()" in actions
    assert "App._window_factory = base_factory" in actions
