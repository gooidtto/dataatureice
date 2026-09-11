# Callable image-first data import

The complete verified callable data layer is stored as one compressed archive for GitHub upload:

`data/callable_release_payload.tar.xz`

Archive SHA-256:
`5787ac42bf86377c13f6f5753bc51f232bed013becd0260b3261e1f9b141a7f8`

Archive contents: 29,815 callable price-condition rows across snapshots 2026-08-25 and 2026-08-31, plus `source_image_manifest.csv`.

## 2026-07 image facts

The uploaded `0705` and `0710` image batches are processed by staged materializers `tools/materialize_2026_07.py`, `tools/materialize_2026_07_safe.py`, `tools/materialize_2026_07_extra.py`, `tools/materialize_2026_07_reviewed.py`, `tools/materialize_2026_07_reviewed2.py`, `tools/materialize_2026_07_reviewed3.py`, `tools/materialize_2026_07_reviewed4.py`, `tools/materialize_2026_07_reviewed5.py`, `tools/materialize_2026_07_reviewed6.py`, `tools/materialize_2026_07_reviewed7.py`, `tools/materialize_2026_07_reviewed8.py` and `tools/materialize_2026_07_reviewed9.py`. Only clearly readable facts are written; uncertain entries are skipped rather than guessed.

The final Windows CI materialization verified **503 rows for 2026-07-05 and 1,128 rows for 2026-07-10, 1,631 rows total**. The generated package also contains the merged source-image manifest with SHA-256, source paths and verification metadata.

The two uploaded ZIPs contain **63 JPG images**. All **63/63 images have now been reviewed**: **55 images produced reliable structured price rows**, **1 image (`0710/手机配件.jpg`) was verified as duplicate table content and registered without duplicating price rows**, and **7 images were explicitly marked `skipped_unreliable`** because their dense/small tables could not be completely determined to the required reliability threshold. No uncertain values were guessed or written. The seven skipped images are 0705 `手机主板.jpg`, `对讲机.jpg`; 0710 `主板.jpg`, `对讲机.jpg`, `摄像头.jpg`, `显卡.jpg`, `苹果主板.jpg`.

GitHub Actions run 111 completed successfully through data validation, pytest, Windows EXE build, package data inclusion, package smoke-check, ZIP creation and artifact upload. The image-review completion condition is satisfied, so the automatic image-processing task has been stopped and will not repeat this completed batch.
