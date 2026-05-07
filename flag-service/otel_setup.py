import os
from opentelemetry import trace, metrics
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def setup_otel(service_name: str):
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENV", "prod"),
    })

    url_default = "otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4317"
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", url_default)

    # Traces
    trace_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Metricas
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Ativa a propagacao usando o nome de classe correto
    set_global_textmap(TraceContextTextMapPropagator())

    return trace.get_tracer(service_name)