#!/bin/sh

CMD="$1"

if [ -z $CMD ]; then
  echo "No command specified"
  exit 1
fi

exec_worker() {
  if [[ -z "${S3_WORKER_ARGS}" ]]; then
    echo "S3_WORKER_ARGS is empty"
    echo "setting it to new value"
    export S3_WORKER_ARGS="-Q ${PM_S3_PREVIEW_QUEUE_NAME},${PM_S3_QUEUE_NAME}"
    echo "S3_WORKER_ARGS was set to $S3_WORKER_ARGS"
  fi
  echo "Starting worker with S3_WORKER_ARGS was set to $S3_WORKER_ARGS"
  exec celery -A s3worker.celery_app worker ${S3_WORKER_ARGS}
}

case $CMD in
  worker)
    exec_worker
    ;;
  *)
    exec "$@"
    ;;
esac
