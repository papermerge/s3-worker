FROM python:3.14-alpine

ENV APP_DIR=/app/
WORKDIR ${APP_DIR}

RUN apk update && apk add linux-headers \
    python3-dev \
    gcc \
    libc-dev \
    libpq-dev \
    imagemagick \
    poppler-utils && \
    # ensure all packages are up-to-date
    apk upgrade --no-cache && \
    rm -rf /var/cache/apk/*

COPY uv.lock pyproject.toml README.md LICENSE ${APP_DIR}
COPY s3worker /${APP_DIR}/s3worker/

RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache -r <(uv export --frozen --no-dev) && \
    pip install --no-cache-dir . --no-deps


COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["worker"]
