"""DEPRECATED: legacy fixed-six-column/web-OCR updater.

The image-first price fact layer is authoritative. This legacy updater is intentionally
blocked so it cannot overwrite verified snapshot data with guessed or OCR-inferred
columns.
"""

raise SystemExit(
    "已停用：旧版固定六价位/网页 OCR 更新器不能写入事实数据。"
    "请使用 data/snapshots/YYYY-MM-DD/*.csv 的图像核验数据流程。"
)
