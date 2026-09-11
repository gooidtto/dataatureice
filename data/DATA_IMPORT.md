# Callable image-first data import

The complete verified callable data layer is stored as one compressed archive for GitHub upload:

`data/callable_release_payload.tar.xz`

Archive SHA-256:
`5787ac42bf86377c13f6f5753bc51f232bed013becd0260b3261e1f9b141a7f8`

Archive contents: 29,815 callable price-condition rows across snapshots 2026-08-25 and 2026-08-31, plus `source_image_manifest.csv`.

## 2026-07 image facts

The uploaded `0705` and `0710` image batches are processed by the staged materializers `tools/materialize_2026_07.py`, `tools/materialize_2026_07_extra.py`, `tools/materialize_2026_07_reviewed.py` and `tools/materialize_2026_07_reviewed2.py`. Only clearly readable facts are written; uncertain entries are skipped rather than guessed.

Current verified structured subset: **216 rows for 2026-07-05 and 797 rows for 2026-07-10, 1,013 rows total**. Source-image paths, SHA-256 and verification metadata are merged into `source_image_manifest.csv` during CI.

The two uploaded ZIPs contain 63 JPG images. The current pass has reviewed/structured **36 images**, with **27 images remaining for continued identification**. The remaining images are not treated as complete until their readable facts are extracted or they are explicitly marked as unreadable/skipped.

GitHub Actions automatically materializes these dates before validation/build. The Windows package copies the materialized `data/` directory next to the EXE.
