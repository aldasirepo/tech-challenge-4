FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Adiciona instrumentação para psycopg2 (Postgres)
RUN pip install --no-cache-dir opentelemetry-instrumentation-psycopg2==0.44b0

COPY . .

# Variáveis OTel
ENV OTEL_SERVICE_NAME=targeting-service
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4317
ENV OTEL_EXPORTER_OTLP_PROTOCOL=grpc
ENV OTEL_TRACES_EXPORTER=otlp
ENV OTEL_METRICS_EXPORTER=otlp
ENV OTEL_LOGS_EXPORTER=otlp
ENV OTEL_RESOURCE_ATTRIBUTES="service.name=targeting-service,service.version=1.0,deployment.environment=prod"
ENV OTEL_PYTHON_LOG_CORRELATION=true

EXPOSE 8003

# opentelemetry-instrument ativa instrumentação automática (Flask, requests, psycopg2)
CMD ["opentelemetry-instrument", "gunicorn", "--bind", "0.0.0.0:8003", "app:app"]
