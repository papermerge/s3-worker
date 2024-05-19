FROM python:3.12-slim-bookworm

WORKDIR /app
ENV VIRTUAL_ENV=/app/venv

COPY poetry.lock pyproject.toml README.md LICENSE /app/

RUN pip install --upgrade poetry && \
    python -m venv ${VIRTUAL_ENV} && \
    poetry install -E pgsql -v

COPY s3worker /app/s3worker/

COPY docker/run.bash /run.bash
RUN chmod +x /run.bash

ENTRYPOINT ["/run.bash"]
CMD ["worker"]
