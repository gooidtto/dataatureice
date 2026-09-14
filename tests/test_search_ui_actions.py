from types import SimpleNamespace
import app_actions
from app_actions import _install_search_behavior, _reliable_search

class _Var:
    def __init__(self,value): self.value=value
    def get(self): return self.value
class _TraceVar(_Var):
    def __init__(self,value): super().__init__(value);self.traces=[];self.removed=[]
    def trace_info(self): return [("write","legacy-write")]
    def trace_remove(self,mode,callback): self.removed.append((mode,callback))
    def trace_add(self,mode,callback): self.traces.append((mode,callback));return "new-write"
class _Widget:
    def __init__(self): self.value=""
    def config(self,**kwargs): self.value=kwargs.get("text",self.value)
    def place(self,**kwargs): self.value=kwargs
    def place_forget(self): self.value=None
class _Root:
    def after_cancel(self,_ident): pass

def test_confirmed_search_renders_results_without_async_queue():
    row={"record_id":"a59","model":"A59","brand":"OPPO"};rendered=[]
    app=SimpleNamespace(q=_Var("OPPO A59"),cat=_Var("全部"),s=SimpleNamespace(search=lambda q,cat:[row]),h=SimpleNamespace(add=lambda q:None),root=_Root(),status=_Widget(),target=_Widget(),empty_hint=_Widget(),_matrix_map={"result_0":row},render=lambda rows:rendered.extend(rows),refresh_suggestions=lambda:None,_search_query_id=0,_search_after_id=None,_sync_search_after_id=None)
    result=_reliable_search(app,False);assert result==[row];assert rendered==[row];assert app.status.value=="找到 1 个结果块";assert app.target.value=="搜索结果：OPPO A59 · 1 个结果块"

def test_typing_only_refreshes_suggestions_and_does_not_schedule_search(monkeypatch):
    q=_TraceVar("OPPO A59");refreshed=[];after_calls=[];root=SimpleNamespace(after=lambda *args:after_calls.append(args));app=SimpleNamespace(q=q,root=root)
    monkeypatch.setattr(app_actions,"_refresh_suggestions",lambda self:refreshed.append(True))
    _install_search_behavior(app);assert q.removed==[("write","legacy-write")];assert len(q.traces)==1;assert q.traces[0][0]=="write"
    q.traces[0][1]();assert refreshed==[True];assert after_calls==[];assert app._sync_search_after_id is None
