# Changelog

## [0.5.1] - 2025-08-18

### Changes

- Updates dependencies
- Use psycopg v3 driver. Drop sqlite dependency.

## [0.5] - not yet released

### Changes

- add `generate_doc_thumbnail_task` to generate document thumbnails. It also updates documents `preview_status` attribute (None, PENDING, READY, FAILED).
- add unit tests to s3worker project
- add CI tests pipeline to the project
- adopt poetry 2.1 format for pyproject.toml file
