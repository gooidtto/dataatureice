import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_ACTIONS = ROOT / "app_actions.py"
UI_BOOTSTRAP = ROOT / "ui_bootstrap.py"


def _module(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _functions(module):
    return {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}


def _class(module, name):
    return next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == name)


def test_optional_actions_use_window_factory():
    actions_module = _module(APP_ACTIONS)
    ui_module = _module(UI_BOOTSTRAP)
    actions = _functions(actions_module)
    ui_functions = _functions(ui_module)
    ui_methods = {node.name: node for node in _class(ui_module, "SearchApp").body if isinstance(node, ast.FunctionDef)}

    assert [arg.arg for arg in actions["_new_window"].args.args] == ["self", "title", "geometry", "minsize"]
    assert [arg.arg for arg in actions["show_compare"].args.args] == ["self", "rows", "targets"]
    assert [arg.arg for arg in actions["detail_rows"].args.args] == ["self", "rs"]
    assert "show_compare" in actions and "detail_rows" in actions
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Toplevel"
        for node in ast.walk(actions_module)
    )
    assert "_new_window" in ui_functions
    assert "_new_window" in ui_methods
