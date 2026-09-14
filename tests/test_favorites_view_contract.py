import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]
VIEW = ROOT / "favorites_view.py"
ACTIONS = ROOT / "app_actions.py"


def _module(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(module, name):
    return next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)


def _calls_named(node, name):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name for n in ast.walk(node))


def _calls_attr(node, name):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == name for n in ast.walk(node))


def test_favorites_uses_same_canonical_matrix_builder_and_sorting():
    fn = _function(_module(VIEW), "show_favorites_matrix")
    assert _calls_named(fn, "build_result_blocks")
    assert _calls_named(fn, "sort_rows")
    assert _calls_named(fn, "_favorite_menu")
    assert _calls_attr(fn, "create_window") is False
    assert _calls_attr(fn, "_new_window")


def test_favorites_preserves_search_result_palette_and_horizontal_tree_surface():
    text = VIEW.read_text(encoding="utf-8")
    assert "#eef7ff" in text
    assert "#f5efff" in text
    assert "#eefaf2" in text
    assert 'show="headings"' in text
    assert 'tree.column(' in text
    assert 'stretch=False' in text


def test_app_actions_routes_favorites_through_shared_matrix_renderer():
    fn = _function(_module(ACTIONS), "show_favorites")
    assert any(isinstance(n, ast.ImportFrom) and n.module == "favorites_view" for n in ast.walk(fn))
    assert _calls_named(fn, "show_favorites_matrix")
