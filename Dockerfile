FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# lightweight runtime deps only
RUN apt-get update --no-install-recommends \
    && apt-get install --no-install-recommends -y gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install --default-timeout=100 -r ./requirements.txt

COPY app ./app
COPY pyproject.toml README.md ./

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/volumes/log_analyzer \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
