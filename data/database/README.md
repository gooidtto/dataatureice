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
- 即使某日期当前没有可查询价格行，也保留该日期目录和标准 `price.csv` 表头，保证数据层级稳定、可识别。
- 无可靠识别结果的数据不进入价格表。
- `source_image_manifest.csv` 继续作为全局来源图片登记表。
- `snapshots/` 保留现有大规模历史快照分片，与图片事实日期数据库并行，不混用。

## 新日期加入

后续加入新日期时，只需要生成对应日期的 CSV；Windows 构建流程会自动将根目录的 `YYYY-MM-DD.csv` 统一归档为：

`data/database/YYYY-MM-DD/price.csv`

软件统一扫描 `data/database/YYYY-MM-DD/price.csv`，建立搜索索引，因此不需要为每一个新日期修改搜索代码。
