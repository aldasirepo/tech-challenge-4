import os
from opentelemetry import trace, metrics
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextPropagator
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

    # IMPORTANTE: Removido o http:// pois o gRPC espera apenas o host:porta
    url_default = (
        "otel-collector-opentelemetry-collector"
        ".monitoring.svc.cluster.local:4317"
    )
    # Garante o uso de os.getenv (minusculo)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", url_default)

    # Configuracao de Traces
    trace_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Configuracao de Metricas
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter, export_interval_millis=30000
    )
    meter_provider = MeterProvider(
        resource=resource, metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)

    # Ativa a propagacao de contexto
    set_global_textmap(TraceContextPropagator())

    return trace.get_tracer(service_name)