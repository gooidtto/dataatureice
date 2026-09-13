from types import SimpleNamespace
from app_actions import _reliable_search

class _Var:
    def __init__(self, value): self.value = value
    def get(self): return self.value

class _Widget:
    def __init__(self): self.value = ""
    def config(self, **kwargs): self.value = kwargs.get("text", self.value)
    def place(self, **kwargs): self.value = kwargs
    def place_forget(self): self.value = None

class _Root:
    def after_cancel(self, _ident): pass

def test_confirmed_search_renders_results_without_async_queue():
    row = {"record_id": "a59", "model": "A59", "brand": "OPPO"}
    rendered = []
    app = SimpleNamespace(q=_Var("OPPO A59"), cat=_Var("全部"), s=SimpleNamespace(search=lambda q, cat: [row]), h=SimpleNamespace(add=lambda q: None), root=_Root(), status=_Widget(), target=_Widget(), empty_hint=_Widget(), _matrix_map={"result_0": row}, render=lambda rows: rendered.extend(rows), refresh_suggestions=lambda: None, _search_query_id=0, _search_after_id=None, _sync_search_after_id=None)
    result = _reliable_search(app, False)
    assert result == [row]
    assert rendered == [row]
    assert app.status.value == "找到 1 个结果块"
    assert app.target.value == "搜索结果：OPPO A59 · 1 个结果块"
