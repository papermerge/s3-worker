# S3 Worker

Microservice to synchronize local folder with S3 bucket.

## Requirements

```
poetry --version
Poetry (version 2.1.4)
```

## Celery Command
```
poetry run celery -A s3worker.celery_app worker -Q demo_s3preview,demo_s3
```