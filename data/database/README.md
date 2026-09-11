# 日期数据库结构

运行时价格数据库按日期独立存放，目录规范固定为：

```text
data/
└── database/
    ├── 2026-07-05/
    │   └── price.csv
    ├── 2026-07-10/
    │   └── price.csv
    ├── 2026-08-25/
    │   └── price.csv
    ├── 2026-08-31/
    │   └── price.csv
    └── YYYY-MM-DD/
        └── price.csv
```

## 固定规则

- 所有日期数据库统一放在 `data/database/` 下。
- 每个日期一个独立目录：`YYYY-MM-DD/`。
- 每个日期的主价格表统一命名为 `price.csv`。
- `data/` 根目录不再保留日期命名的 CSV 数据文件。
- `data_date` 必须与所属目录日期完全一致。
- 新日期只新增新的日期目录，不覆盖旧日期。
- `price.csv` 保留完整事实字段：`record_id,data_date,category,subtype,brand,series,model,model_code,alias,condition,price,unit,note,origin,source_image,source_path,verified,confidence,verification`，不得因归档而丢失型号代码、来源、验证等字段。
- 当前恢复基线的准确行数固定为：2026-07-05 = 503，2026-07-10 = 1,128，2026-08-25 = 15,400，2026-08-31 = 14,415，总计 31,446 行。
- 无可靠识别结果的数据不进入价格表。
- `source_image_manifest.csv` 继续作为全局来源图片登记表。
- `snapshots/` 保留现有大规模历史快照分片，作为恢复校验源；运行时优先读取 `data/database/`，不将同一日期重复加载两次。

## 新日期加入

后续加入新日期时，统一生成对应日期的完整字段 CSV；Windows 构建流程会自动将根目录的 `YYYY-MM-DD.csv` 归档为：

`data/database/YYYY-MM-DD/price.csv`

归档过程会校验行数、`record_id` 唯一性、日期一致性和必填事实字段，避免静默丢行或丢字段。

软件统一扫描 `data/database/YYYY-MM-DD/price.csv`，建立搜索索引，因此不需要为每一个新日期修改搜索代码。
