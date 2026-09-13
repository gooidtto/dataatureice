"""SQLite storage engine with an FTS5 search index."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Sequence

DEFAULT_FIELDS=("record_id","data_date","category","subtype","brand","series","model","model_code","alias","condition","price","unit","note","origin","source_image","source_path","verified","confidence","verification")

class SQLiteFTSEngine:
    def __init__(self,path:str|Path,fields:Sequence[str]=DEFAULT_FIELDS):
        self.path=Path(path); self.fields=tuple(fields)
        if "record_id" not in self.fields: raise ValueError("fields must contain record_id")
    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(str(self.path)); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
    def initialize(self,conn=None):
        own=conn is None; conn=conn or self.connect()
        try:
            cols=", ".join(f'"{f}" TEXT' for f in self.fields)
            conn.execute(f"CREATE TABLE IF NOT EXISTS records ({cols}, PRIMARY KEY (record_id))")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_records_date ON records(data_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_records_identity ON records(category,subtype,brand,series,model,model_code)")
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(record_id UNINDEXED,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image,content='records',content_rowid='rowid')")
            conn.execute("CREATE TRIGGER IF NOT EXISTS records_ai AFTER INSERT ON records BEGIN INSERT INTO records_fts(rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) VALUES(new.rowid,new.record_id,new.category,new.subtype,new.brand,new.series,new.model,new.model_code,new.alias,new.condition,new.note,new.origin,new.source_image); END")
            conn.execute("CREATE TRIGGER IF NOT EXISTS records_ad AFTER DELETE ON records BEGIN INSERT INTO records_fts(records_fts,rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) VALUES('delete',old.rowid,old.record_id,old.category,old.subtype,old.brand,old.series,old.model,old.model_code,old.alias,old.condition,old.note,old.origin,old.source_image); END")
            conn.execute("CREATE TRIGGER IF NOT EXISTS records_au AFTER UPDATE ON records BEGIN INSERT INTO records_fts(records_fts,rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) VALUES('delete',old.rowid,old.record_id,old.category,old.subtype,old.brand,old.series,old.model,old.model_code,old.alias,old.condition,old.note,old.origin,old.source_image); INSERT INTO records_fts(rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) VALUES(new.rowid,new.record_id,new.category,new.subtype,new.brand,new.series,new.model,new.model_code,new.alias,new.condition,new.note,new.origin,new.source_image); END")
            conn.commit()
        finally:
            if own: conn.close()
    def replace_rows(self,rows:Iterable[Mapping[str,object]])->int:
        rows=[dict(r) for r in rows]
        with self.connect() as c:
            self.initialize(c); c.execute("DELETE FROM records")
            sql=f"INSERT OR REPLACE INTO records ({','.join(self.fields)}) VALUES ({','.join('?' for _ in self.fields)})"
            c.executemany(sql,[tuple(str(r.get(f,"") or "") for f in self.fields) for r in rows]); c.execute("INSERT INTO records_fts(records_fts) VALUES('rebuild')"); c.commit()
        return len(rows)
    def count(self):
        with self.connect() as c: self.initialize(c); return int(c.execute("SELECT COUNT(*) FROM records").fetchone()[0])
    def all_rows(self):
        with self.connect() as c: self.initialize(c); return [dict(r) for r in c.execute("SELECT * FROM records")]
    def fts_search(self,query:str,limit:int=1000):
        q=(query or "").strip()
        if not q:return self.all_rows()[:limit]
        match=" AND ".join(f'"{t.replace(chr(34),chr(34)*2)}"' for t in q.split() if t)
        with self.connect() as c:
            self.initialize(c)
            return [dict(r) for r in c.execute("SELECT r.* FROM records_fts f JOIN records r ON r.rowid=f.rowid WHERE records_fts MATCH ? LIMIT ?",(match,limit))]
    def rebuild_fts(self):
        with self.connect() as c:self.initialize(c); c.execute("INSERT INTO records_fts(records_fts) VALUES('rebuild')"); c.commit()
