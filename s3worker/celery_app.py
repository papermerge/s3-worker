from celery import Celery
from s3worker import config, utils
from celery.signals import setup_logging

settings = config.get_settings()


app = Celery(
    's3worker',
    broker=str(settings.redis_url),
    include=['s3worker.tasks']
)

app.autodiscover_tasks()

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
    max_retries=3,
    broker_connection_retry_on_startup=False,
    interval_start=0,
    interval_step=0.2,
    interval_max=0.2,
)


@setup_logging.connect
def config_loggers(*args, **kwags):
    if settings.log_config:
        utils.setup_logging(settings.log_config)


if __name__ == '__main__':
    app.start()
