# Callable image-first data import

The complete verified callable data layer is stored as one compressed archive for GitHub upload:

`data/callable_release_payload.tar.xz`

Archive SHA-256:
`5787ac42bf86377c13f6f5753bc51f232bed013becd0260b3261e1f9b141a7f8`

Archive contents: 29,815 callable price-condition rows across snapshots 2026-08-25 and 2026-08-31, plus `source_image_manifest.csv`.

## 2026-07 image facts

The uploaded `0705` and `0710` image batches are materialized by:

- `tools/materialize_2026_07.py`
- `tools/materialize_2026_07_extra.py`
- `tools/materialize_2026_07_manifest.py`

Current verified subset: 109 rows for `2026-07-05` and 407 rows for `2026-07-10` (516 rows total). These rows come only from clearly readable/visually verified images. Images or entries that could not be reliably identified were skipped rather than guessed. Source-image paths, SHA-256 and verification metadata are merged into `source_image_manifest.csv` during CI.

GitHub Actions automatically materializes these dates before validation/build. The Windows package copies the materialized `data/` directory next to the EXE.
