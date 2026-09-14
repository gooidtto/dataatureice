import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]
ACTIONS = ROOT / "app_actions.py"
UI = ROOT / "ui_bootstrap.py"


def _module(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _functions(module):
    return {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}


def _arg_names(node):
    return [arg.arg for arg in node.args.args]


def _calls_named(node, name):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name for n in ast.walk(node))


def _calls_attr(node, name):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == name for n in ast.walk(node))


def _contains_string(node, value):
    return any(isinstance(n, ast.Constant) and n.value == value for n in ast.walk(node))


def test_app_actions_do_not_bypass_window_factory():
    module = _module(ACTIONS)
    functions = _functions(module)
    assert _arg_names(functions["_new_window"]) == ["self", "title", "geometry", "minsize"]
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "Toplevel" for node in ast.walk(module))
    assert _calls_named(functions["sources"], "_new_window")
    assert _calls_named(functions["show_compare"], "_new_window")
    assert _calls_named(functions["detail_rows"], "_new_window")
    assert "setattr" in {node.func.id for node in ast.walk(functions["install"]) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}


def test_favorite_popup_actions_match_app_helpers():
    actions = _functions(_module(ACTIONS))
    show = actions["show_favorites"]
    # Favorites now delegate to the dedicated matrix renderer, which owns
    # its window creation and reuses the same search-result surface.
    assert _calls_named(show, "show_favorites_matrix")
    assert any(isinstance(n, ast.ImportFrom) and n.module == "favorites_view" for n in ast.walk(show))
    assert _calls_attr(actions["_remove_favorite_rows"], "remove")


def test_favorite_action_is_installed_on_search_app():
    actions = _functions(_module(ACTIONS))
    assert _arg_names(actions["addToFavorites"]) == ["self", "rows"]
    assert _calls_attr(actions["addToFavorites"], "add")
    assert _contains_string(actions["addToFavorites"], "已经收藏")
