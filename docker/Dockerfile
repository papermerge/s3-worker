FROM python:3.13-alpine

ENV APP_DIR=/app/
WORKDIR ${APP_DIR}


RUN apk update && apk add linux-headers \
    python3-dev \
    gcc \
    libc-dev \
    libpq-dev \
    imagemagick \
    poppler-utils

COPY poetry.lock pyproject.toml README.md LICENSE ${APP_DIR}
COPY s3worker /${APP_DIR}/s3worker/

RUN pip install --upgrade poetry && \
    poetry install -E pg -v

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["worker"]
