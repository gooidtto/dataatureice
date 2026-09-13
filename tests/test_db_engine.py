from storage.db_engine import SQLiteFTSEngine


def row(record_id, model="OPPO A59", **extra):
    r={"record_id":record_id,"data_date":"2026-08-31","category":"手机","subtype":"手机","brand":"OPPO","series":"A","model":model,"model_code":"","alias":"","condition":"开机好屏","price":"500","unit":"元","note":"","origin":"","source_image":"img-a","source_path":"","verified":"1","confidence":"","verification":""}
    r.update(extra); return r


def test_sqlite_schema_and_fts_roundtrip(tmp_path):
    db=SQLiteFTSEngine(tmp_path/"prices.sqlite3")
    rows=[row("r1", model="OPPO A59"), row("r2", model="Huawei P30", brand="华为")]
    assert db.replace_rows(rows)==2
    assert db.count()==2
    assert [r["record_id"] for r in db.fts_search("A59")]==["r1"]
    assert [r["record_id"] for r in db.fts_search("华为 P30")]==["r2"]


def test_fts_is_rebuilt_after_replace(tmp_path):
    db=SQLiteFTSEngine(tmp_path/"prices.sqlite3")
    db.replace_rows([row("r1", model="A59")])
    db.replace_rows([row("r2", model="X7", brand="Realme")])
    assert db.fts_search("A59")==[]
    assert [r["record_id"] for r in db.fts_search("X7")]==["r2"]


def test_same_record_id_can_exist_in_multiple_dates(tmp_path):
    db=SQLiteFTSEngine(tmp_path/"prices.sqlite3")
    db.replace_rows([
        row("same", model="A59", data_date="2026-08-30"),
        row("same", model="A59", data_date="2026-08-31"),
    ])
    assert db.count()==2
    assert [r["data_date"] for r in db.all_rows()]==["2026-08-30","2026-08-31"]
