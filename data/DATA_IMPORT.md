# Callable image-first data import

The complete verified callable data layer is stored as one compressed archive for GitHub upload:

`data/callable_release_payload.tar.xz`

Archive SHA-256:
`5787ac42bf86377c13f6f5753bc51f232bed013becd0260b3261e1f9b141a7f8`

Archive contents: 29,815 callable price-condition rows across snapshots 2026-08-25 and 2026-08-31, plus `source_image_manifest.csv`.

GitHub Actions automatically materializes this archive before validation/build. The Windows package copies the materialized `data/` directory next to the EXE.
