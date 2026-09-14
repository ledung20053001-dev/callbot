FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system callbot && adduser --system --ingroup callbot callbot

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip && \
    python -m pip install .

RUN mkdir -p /app/audio/output /app/.ai-log && \
    chown -R callbot:callbot /app

USER callbot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
