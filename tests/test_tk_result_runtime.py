import tkinter as tk
from tkinter import TclError
import pytest


def _sample_rows():
    return [
        {"record_id":"a59-new-good","data_date":"2026-08-31","category":"手机","brand":"OPPO","series":"A","model":"A59","model_code":"","condition":"开机屏好","price":"70","unit":"元","source_image":"oppo.jpg"},
        {"record_id":"a59-new-bad","data_date":"2026-08-31","category":"手机","brand":"OPPO","series":"A","model":"A59","model_code":"","condition":"不开机","price":"60","unit":"元","source_image":"oppo.jpg"},
        {"record_id":"a59-old-good","data_date":"2026-08-25","category":"手机","brand":"OPPO","series":"A","model":"A59","model_code":"","condition":"开机屏好","price":"65","unit":"元","source_image":"oppo.jpg"},
    ]


def test_search_app_renders_real_tk_result_blocks(monkeypatch):
    try: root=tk.Tk()
    except TclError as exc: pytest.skip(f"Tk display unavailable: {exc}")
    import phone_search
    from ui_bootstrap import SearchApp
    monkeypatch.setattr(phone_search.App,"load",lambda self:None)
    try:
        app=SearchApp(root);app.render(_sample_rows());root.update_idletasks()
        assert len(app._result_trees)==2;assert len(app._matrix_map)==2;assert all(tree.get_children() for tree in app._result_trees)
        assert app._result_trees[0]["columns"];assert app._result_trees[1]["columns"]
        assert app._result_trees[0].heading("data_date","text")=="数据日期";assert app._result_trees[0].heading("identity","text")=="手机/品牌/系列/型号/网络型号";assert app._result_trees[0].heading("source_image","text")=="来源图片"
        first_iid=app._result_order[0];app._result_double_click(first_iid)
        assert app.tree.selection()==()
    finally: root.destroy()
