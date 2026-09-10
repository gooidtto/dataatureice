#!/usr/bin/env python3
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
SRC=Path('/mnt/data/callable_data')
DST=ROOT/'data'
for name in ('2026-08-25.csv','2026-08-31.csv','source_image_manifest.csv'):
    src=SRC/name
    if not src.exists(): raise SystemExit(f'missing source: {src}')
    shutil.copy2(src,DST/name)
print('copied callable snapshots')
