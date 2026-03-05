FROM python:3.11-slim


LABEL maintainer="DCO-Monitor"
LABEL description="Data Centre Operations Prometheus Exporter"


ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DCO_EXPORTER_PORT=8000 \
    DCO_LOG_PATH=/var/log/dco_exporter.log


RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY dco_exporter.py .


EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/metrics')" || exit 1

ENTRYPOINT ["python", "-u", "dco_exporter.py"]
