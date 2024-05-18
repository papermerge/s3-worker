import yaml
from celery import Celery
from s3worker import config
from celery.signals import setup_logging
from logging.config import dictConfig


settings = config.get_settings()


app = Celery(
    's3worker',
    broker=settings.papermerge__redis__url,
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
    if settings.papermerge__main__logging_cfg is None:
        return

    with open(settings.papermerge__main__logging_cfg, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)

    dictConfig(config)


if __name__ == '__main__':
    app.start()
