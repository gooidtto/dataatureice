import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui_bootstrap.py"
ACTIONS = ROOT / "app_actions.py"
PHONE = ROOT / "phone_search.py"


def _module(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _functions(module):
    return {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}


def _class(module, name):
    return next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == name)


def _methods(module, class_name):
    return {node.name: node for node in _class(module, class_name).body if isinstance(node, ast.FunctionDef)}


def _has_method_call(node, attr):
    return any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == attr
        for child in ast.walk(node)
    )


def test_search_app_owns_window_factory_without_global_tk_patch():
    module = _module(UI)
    functions = _functions(module)
    methods = _methods(module, "SearchApp")
    assert "_new_window" in functions
    assert [arg.arg for arg in functions["_new_window"].args.args] == ["self", "title", "geometry", "minsize"]
    assert "_new_window" in methods
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_new_window" for target in node.targets)
        for node in _class(module, "SearchApp").body
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Toplevel"
        for node in ast.walk(module)
    )


def test_result_double_click_selects_matrix_iid_before_detail():
    method = _methods(_module(UI), "SearchApp")["_result_double_click"]
    statements = method.body
    select_index = next(
        i for i, stmt in enumerate(statements)
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Name)
        and stmt.value.func.id == "_select_result_iid"
    )
    detail_index = next(
        i for i, stmt in enumerate(statements)
        if isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Call)
        and isinstance(stmt.value.func, ast.Attribute)
        and stmt.value.func.attr == "detail"
    )
    assert select_index < detail_index
    assert isinstance(statements[-1], ast.Return)
    assert isinstance(statements[-1].value, ast.Constant)
    assert statements[-1].value.value == "break"


def test_app_actions_do_not_bypass_window_factory():
    module = _module(ACTIONS)
    functions = _functions(module)
    assert [arg.arg for arg in functions["_new_window"].args.args] == ["self", "title", "geometry", "minsize"]
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Toplevel"
        for node in ast.walk(module)
    )
    assert _has_method_call(functions["sources"], "_new_window")
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
