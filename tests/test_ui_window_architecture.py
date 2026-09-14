import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui_bootstrap.py"
ACTIONS = ROOT / "app_actions.py"
PHONE = ROOT / "phone_search.py"


def _module(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _functions(module):
    return {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _methods(module, class_name):
    cls = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}


def _call_names(node):
    return {
        child.func.attr if isinstance(child.func, ast.Attribute) else child.func.id
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, (ast.Attribute, ast.Name))
    }


def test_search_app_owns_window_factory_without_global_tk_patch():
    module = _module(UI)
    functions = _functions(module)
    methods = _methods(module, "SearchApp")
    assert "_new_window" in functions
    assert [arg.arg for arg in functions["_new_window"].args.args] == [
        "self", "title", "geometry", "minsize"
    ]
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_new_window" for target in node.targets)
        for node in ast.walk(next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "SearchApp"))
    )
    assert "_new_window" in methods
    assert not any(
        isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "Toplevel"
        for node in ast.walk(module)
    )


def test_result_double_click_selects_matrix_iid_before_detail():
    methods = _methods(_module(UI), "SearchApp")
    method = methods["_result_double_click"]
    calls = [
        node.func.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert calls.index("detail") > calls.index("_select_result_iid") if "_select_result_iid" in calls else False
    assert isinstance(method.body[-1], ast.Return)


def test_app_actions_do_not_bypass_window_factory():
    module = _module(ACTIONS)
    functions = _functions(module)
    assert "_new_window" in functions
    assert [arg.arg for arg in functions["_new_window"].args.args] == [
        "self", "title", "geometry", "minsize"
    ]
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Toplevel"
        for node in ast.walk(module)
    )
    assert "_new_window" in _call_names(functions["sources"])
    install = functions["install"]
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setattr"
        for node in ast.walk(install)
    )


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
