import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui_bootstrap.py"
ACTIONS = ROOT / "app_actions.py"

def _module(path): return ast.parse(path.read_text(encoding="utf-8"))
def _functions(module): return {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}
def _class(module, name): return next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == name)
def _methods(module, class_name): return {node.name: node for node in _class(module, class_name).body if isinstance(node, ast.FunctionDef)}
def _calls_named(node, name): return any(isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == name for child in ast.walk(node))
def _calls_attr(node, name): return any(isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == name for child in ast.walk(node))
def _arg_names(function): return [arg.arg for arg in function.args.args]
def _contains_string(node, text): return any(isinstance(child, ast.Constant) and child.value == text for child in ast.walk(node))
def _sets_attr(node, attr_name): return any(isinstance(child, ast.Assign) and any(isinstance(target, ast.Attribute) and target.attr == attr_name for target in child.targets) for child in ast.walk(node))

def test_search_app_owns_window_factory_without_global_tk_patch():
    module=_module(UI);functions=_functions(module);methods=_methods(module,"SearchApp")
    assert _arg_names(functions["_new_window"]) == ["self","title","geometry","minsize"]
    assert "_new_window" in methods
    assert any(isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=="_new_window" for target in node.targets) for node in _class(module,"SearchApp").body)
    assert _calls_attr(functions["_new_window"],"Toplevel")
    for name,function in functions.items():
        if name != "_new_window": assert not _calls_attr(function,"Toplevel"),name


def test_result_double_click_opens_detail_without_selecting_search_rows():
    method=_methods(_module(UI),"SearchApp")["_result_double_click"]
    assert not _calls_named(method,"_select_result_iid")
    assert any(isinstance(stmt,ast.Call) and isinstance(stmt.func,ast.Attribute) and stmt.func.attr=="detail_rows" for stmt in ast.walk(method))
    assert isinstance(method.body[-1],ast.Return) and isinstance(method.body[-1].value,ast.Constant) and method.body[-1].value.value=="break"


def test_app_actions_do_not_bypass_window_factory():
    module=_module(ACTIONS);functions=_functions(module)
    assert _arg_names(functions["_new_window"]) == ["self","title","geometry","minsize"]
    # The only direct Toplevel is the transient search-history suggestion popup;
    # all normal child windows route through the shared lifecycle helper.
    for name in ("sources","show_compare","detail_rows","show_favorites"):
        assert not _calls_attr(functions[name],"Toplevel"),name
    assert _calls_named(functions["sources"],"_new_window");assert _calls_named(functions["show_compare"],"_new_window");assert _calls_named(functions["detail_rows"],"_new_window")
    assert "setattr" in {node.func.id for node in ast.walk(functions["install"]) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)}


def test_favorite_popup_actions_match_app_helpers():
    actions=_functions(_module(ACTIONS));show=actions["show_favorites"]
    assert _calls_named(show,"show_favorites_matrix");assert any(isinstance(n,ast.ImportFrom) and n.module=="favorites_view" for n in ast.walk(show));assert _calls_attr(actions["_remove_favorite_rows"],"remove")

def test_favorite_action_is_installed_on_search_app():
    actions=_functions(_module(ACTIONS));assert _arg_names(actions["addToFavorites"])==["self","rows"];assert _calls_attr(actions["addToFavorites"],"add");assert _contains_string(actions["addToFavorites"],"已经收藏");assert _contains_string(actions["install"],"addToFavorites")

def test_main_window_is_withdrawn_during_app_initialization():
    actions=_functions(_module(ACTIONS));lifecycle=actions["_install_window_lifecycle"];assert _calls_attr(lifecycle,"withdraw");assert _calls_named(lifecycle,"original_init");assert _calls_attr(lifecycle,"deiconify");assert _sets_attr(lifecycle,"__init__");assert _sets_attr(lifecycle,"_window_factory");assert _sets_attr(lifecycle,"_new_window")

def test_child_window_is_hidden_until_configuration_finishes():
    actions=_functions(_module(ACTIONS));new_window=actions["_new_window"];assert _calls_attr(new_window,"withdraw");assert _calls_attr(new_window,"after_idle");assert _calls_named(new_window,"_show_window");assert _calls_attr(actions["_show_window"],"deiconify");assert _contains_string(new_window,"_window_factory")
