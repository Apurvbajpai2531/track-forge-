"""Observability wiring. Prometheus metrics now; OpenTelemetry tracing is added in part 2."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_observability(app: FastAPI) -> None:
    instrumentator = Instrumentator(should_group_status_codes=True, excluded_handlers=["/metrics", "/api/health"])
    instrumentator.instrument(app)
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
