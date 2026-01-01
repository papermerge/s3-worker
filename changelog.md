# Changelog

## [0.6] - 2026-01-01

### Added

- **Cloudflare R2 Support**: Worker now supports both AWS S3 and Cloudflare R2 storage backends
- New `STORAGE_BACKEND` environment variable to select backend (`aws` or `cloudflare`)
- R2-specific configuration: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ACCOUNT_ID`
- `generate_presigned_url()` function for creating presigned download URLs
- New CLI commands: `info` (show config), `presigned-url` (generate presigned URLs)
- `get_storage_backend_name()` helper function

### Changed

- `get_client()` now returns appropriate boto3 client based on storage backend
- Client instance is now cached for better performance
- AWS credentials are now optional (only required when `STORAGE_BACKEND=aws`)
- Updated CLI with better help text and storage backend info
- Improved error messages and logging
- Switch from Poetry to uv
- Use new env var names/config names e.g. `PM_DB_URL` instead of `PAPERMERGE__DATABASE__URL`

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
