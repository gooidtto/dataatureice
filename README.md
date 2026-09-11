# 数码回收价格秒查工具

Windows 离线查询工具。价格事实层以已审核的报价图片为唯一来源，CSV 快照负责运行时查询；无法可靠识别的图片记录不进入事实库。

## 数据库结构

图片事实价格数据库按日期独立管理：

```text
data/
├── database/
│   ├── 2026-07-05/
│   │   └── price.csv
│   ├── 2026-07-10/
│   │   └── price.csv
│   └── YYYY-MM-DD/
│       └── price.csv
├── snapshots/
│   └── YYYY-MM-DD/
│       └── part-*.csv
└── source_image_manifest.csv
```

- `database/YYYY-MM-DD/price.csv`：按日期管理的图片事实价格数据库。
- `snapshots/`：原有大规模可查询历史快照分片，继续独立保留。
- `source_image_manifest.csv`：来源图片、验证状态与纳入状态。
- 新日期只新增新的日期目录，不覆盖旧日期。
- 软件自动扫描日期数据库，新日期不需要修改搜索代码。

## 数据运行规则

- 最新日期优先显示。
- 搜索支持品牌、系列、型号、型号代码、别名与来源图片。
- 条件列动态来自原图，不假设固定数量的价格栏。
- 价格单位和备注按来源数据保留。
- 双击结果可查看完整事实记录；右键可复制/查看详情。
- `source_image_manifest.csv` 保存图片纳入、验证与放弃状态。

## 构建

构建前必须通过数据校验：

```text
python data_validator.py data
python -m pytest -q
```

Windows EXE 使用 PyInstaller 构建，并把 `data/` 作为外置数据目录随程序发布。构建阶段会把生成的非空日期 CSV 自动整理到 `data/database/YYYY-MM-DD/price.csv`。

## 数据原则

禁止用网页抓取结果覆盖图片事实库；自动化脚本只能作为独立的候选/辅助流程，不能直接写入已验证快照。
