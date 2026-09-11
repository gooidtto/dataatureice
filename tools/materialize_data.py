#!/usr/bin/env python3
"""Materialize the compressed callable image-first data layer into ./data."""
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'data' / 'callable_release_payload.tar.xz'


def safe_extract(archive: Path, root: Path) -> None:
    with tarfile.open(archive, 'r:xz') as tf:
        for member in tf.getmembers():
            target = (root / member.name).resolve()
            if target != root and root not in target.parents:
                raise RuntimeError(f'unsafe archive path: {member.name}')
        tf.extractall(root)


def main() -> int:
    if not ARCHIVE.exists():
        print('CALLABLE_DATA_ARCHIVE=missing')
        return 0
    safe_extract(ARCHIVE, ROOT)
    manifest = ROOT / 'data' / 'source_image_manifest.csv'
    snapshots = sorted((ROOT / 'data' / 'snapshots').glob('*/part-*.csv'))
    if not manifest.exists() or not snapshots:
        raise SystemExit('callable data archive extracted but snapshots/manifest are incomplete')
    print(f'CALLABLE_DATA_MATERIALIZED rows_shards={len(snapshots)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
