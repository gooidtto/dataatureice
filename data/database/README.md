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
    └── YYYY-MM-DD/
        └── price.csv
```

## 规则

- 每个有效价格日期一个独立目录：`YYYY-MM-DD/`。
- 每个日期的主价格表统一命名为 `price.csv`。
- `data_date` 必须与目录日期完全一致。
- 新日期只新增新的日期目录，不覆盖旧日期。
- 无可靠识别结果的数据不进入价格表。
- `source_image_manifest.csv` 继续作为全局来源图片登记表。
- `snapshots/` 保留现有大规模历史快照分片，与图片事实日期数据库并行，不混用。

## 新日期加入

后续加入新日期时，只需要生成对应日期的 CSV；Windows 构建流程会自动把非空的 `YYYY-MM-DD.csv` 归档为：

`data/database/YYYY-MM-DD/price.csv`

软件会自动扫描日期目录，因此不需要为每一个新日期修改搜索代码。
