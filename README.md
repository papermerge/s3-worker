# S3 Worker

Microservice to synchronize local folder with S3 bucket.

## Celery Command
```
uv run celery -A s3worker.celery_app worker -Q demo_s3preview,demo_s3
```
