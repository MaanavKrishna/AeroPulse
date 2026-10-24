# AeroPulse: one image for the web app and the collector.
FROM python:3.12-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN useradd --create-home --uid 10001 aeropulse
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install ".[postgres]"

USER aeropulse
ENV AEROPULSE_EXPORT_DIR=/app/exports
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["sh", "-c", "aeropulse db upgrade && uvicorn aeropulse.app:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*' --workers 2"]
