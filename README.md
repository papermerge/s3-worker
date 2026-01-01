# S3 Worker

Celery worker for syncing Papermerge media files with S3-compatible storage.

## Overview

S3 Worker is a background service that handles file synchronization between Papermerge's local media storage and cloud object storage. It supports:

- **AWS S3** - Amazon's Simple Storage Service
- **Cloudflare R2** - Cloudflare's S3-compatible object storage

The worker processes Celery tasks for:

- Uploading document versions to storage
- Removing document versions from storage
- Generating and uploading document thumbnails
- Managing page preview images

## Configuration

S3 Worker is configured via environment variables.

### Storage Backend Selection

| Variable | Description | Default |
|----------|-------------|---------|
| `STORAGE_BACKEND` | Storage backend: `aws` or `cloudflare` | `aws` |
| `PM_S3_BUCKET_NAME` | Bucket name (used for both S3 and R2) | - |

### AWS S3 Configuration

When `STORAGE_BACKEND=aws`:

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key |
| `AWS_REGION_NAME` | AWS region (optional) |

### Cloudflare R2 Configuration

When `STORAGE_BACKEND=cloudflare`:

| Variable | Description |
|----------|-------------|
| `R2_ACCESS_KEY_ID` | R2 access key ID |
| `R2_SECRET_ACCESS_KEY` | R2 secret access key |
| `R2_ACCOUNT_ID` | Cloudflare account ID |

### Common Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `PM_DB_URL` | PostgreSQL database URL | - |
| `PM_REDIS_URL` | Redis URL for Celery broker | - |
| `PM_MEDIA_ROOT` | Path to local media storage | - |
| `PM_PREFIX` | Prefix for storage keys (multi-tenant) | `''` |
| `PM_LOG_CONFIG` | Path to logging config file | `/app/log_config.yaml` |
| `PRESIGNED_URL_EXPIRES` | Presigned URL expiration (seconds) | `3600` |

## Usage

### Running with Docker

```bash
# Build
docker build -t s3worker -f docker/Dockerfile .

# Run with AWS S3
docker run \
  -e STORAGE_BACKEND=aws \
  -e AWS_ACCESS_KEY_ID=... \
  -e AWS_SECRET_ACCESS_KEY=... \
  -e PM_S3_BUCKET_NAME=my-bucket \
  -e PM_DB_URL=postgresql://... \
  -e PM_REDIS_URL=redis://... \
  -e PM_MEDIA_ROOT=/app/media \
  s3worker

# Run with Cloudflare R2
docker run \
  -e STORAGE_BACKEND=cloudflare \
  -e R2_ACCESS_KEY_ID=... \
  -e R2_SECRET_ACCESS_KEY=... \
  -e R2_ACCOUNT_ID=... \
  -e PM_S3_BUCKET_NAME=my-bucket \
  -e PM_DB_URL=postgresql://... \
  -e PM_REDIS_URL=redis://... \
  -e PM_MEDIA_ROOT=/app/media \
  s3worker
```

### Running locally

```bash
# Install dependencies
uv sync

# Start the worker
uv run celery -A s3worker.celery_app worker --loglevel=info

# Or with specific queues
uv run celery -A s3worker.celery_app worker -Q demo_s3preview,demo_s3
```

### CLI Commands

```bash
# Show configuration info
uv run s3w info

# Sync local media to storage
uv run s3w sync

# Generate presigned URL
uv run s3w presigned-url "docvers/ab/cd/abcd1234/document.pdf"

# Upload a file
uv run s3w upload /path/to/file.pdf docvers/ab/cd/abcd1234/file.pdf

# Generate thumbnails for all documents
uv run s3w generate-doc-thumbnails --progress

# Print configuration as JSON
uv run s3w config
```

## Architecture

### Storage Backend Abstraction

The worker uses boto3 for both AWS S3 and Cloudflare R2, since R2 is S3-compatible:

```
┌─────────────────────────────────────────────────────┐
│                   s3worker/client.py                │
│                                                     │
│  get_client() ─────┬──────────────────────────────► │
│                    │                                │
│          ┌────────┴────────┐                       │
│          │                  │                       │
│    AWS S3 Client      R2 Client                    │
│    (standard)         (custom endpoint)            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Key Differences

| Feature | AWS S3 | Cloudflare R2 |
|---------|--------|---------------|
| Endpoint | Regional S3 endpoints | `<account_id>.r2.cloudflarestorage.com` |
| Region | Specific (us-east-1, etc.) | `auto` (global) |
| Signature | S3v4 | S3v4 |
| Egress | Paid | Free |

## Celery Tasks

The worker provides the following Celery tasks:

| Task Name | Description |
|-----------|-------------|
| `s3_worker_add_doc_vers` | Upload document versions to storage |
| `s3_worker_remove_doc_vers` | Remove document versions from storage |
| `s3_worker_remove_doc_thumbnail` | Remove document thumbnail |
| `s3_worker_remove_docs_thumbnail` | Remove multiple document thumbnails |
| `s3_worker_remove_page_thumbnail` | Remove page thumbnails |
| `s3_worker_generate_doc_thumbnail` | Generate and upload document thumbnail |

## Migration from AWS to Cloudflare R2

To migrate from AWS S3 to Cloudflare R2:

1. Create an R2 bucket in Cloudflare dashboard
2. Generate R2 API tokens with read/write access
3. Update environment variables:
   ```bash
   PM_STORAGE_BACKEND=cloudflare
   R2_ACCESS_KEY_ID=your_r2_access_key
   R2_SECRET_ACCESS_KEY=your_r2_secret_key
   R2_ACCOUNT_ID=your_cloudflare_account_id
   PM_S3_BUCKET_NAME=your_r2_bucket_name
   ```
4. Migrate existing data using `rclone` or similar tools
5. Restart the worker

## License

MIT
