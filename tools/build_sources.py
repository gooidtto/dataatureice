#!/usr/bin/env python3
"""Stage an image-first callable data directory after validation.

Usage: python tools/build_sources.py [SOURCE_DIR] [DEST_DIR]
SOURCE_DIR defaults to CALLABLE_DATA_SOURCE or ./callable_data.
DEST_DIR defaults to ./data.
"""
from pathlib import Path
import os, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
SRC=Path(sys.argv[1] if len(sys.argv)>1 else os.environ.get('CALLABLE_DATA_SOURCE', ROOT/'callable_data'))
DST=Path(sys.argv[2] if len(sys.argv)>2 else ROOT/'data')
if not SRC.exists(): raise SystemExit(f'missing source directory: {SRC}')
sys.path.insert(0,str(ROOT))
from data_validator import validate
errors,warnings,rows=validate(str(SRC))
if errors:
    print('\n'.join('ERROR '+x for x in errors)); raise SystemExit(1)
print(f'validated {len(rows)} callable rows; warnings={len(warnings)}')
for w in warnings: print('WARN '+w)
DST.mkdir(parents=True,exist_ok=True)
for child in DST.iterdir():
    if child.is_dir(): shutil.rmtree(child)
    else: child.unlink()
for child in SRC.iterdir():
    target=DST/child.name
    if child.is_dir(): shutil.copytree(child,target)
    else: shutil.copy2(child,target)
print(f'CALLABLE_DATA_OK {DST}')
