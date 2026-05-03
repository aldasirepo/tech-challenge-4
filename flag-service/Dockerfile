FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Adiciona instrumentação para psycopg2 (Postgres)
RUN pip install --no-cache-dir opentelemetry-instrumentation-psycopg2==0.44b0

COPY . .

# Variáveis OTel
ENV OTEL_SERVICE_NAME=flag-service
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4317
ENV OTEL_EXPORTER_OTLP_PROTOCOL=grpc
ENV OTEL_TRACES_EXPORTER=otlp
ENV OTEL_METRICS_EXPORTER=otlp
ENV OTEL_LOGS_EXPORTER=otlp
ENV OTEL_RESOURCE_ATTRIBUTES="service.name=flag-service,service.version=1.0,deployment.environment=prod"
ENV OTEL_PYTHON_LOG_CORRELATION=true

EXPOSE 8002

# Usa o opentelemetry-instrument para ativar instrumentação automática
CMD ["opentelemetry-instrument", "gunicorn", "--bind", "0.0.0.0:8002", "app:app"]
