"""
Middleware para FastAPI e Starlette
"""

from typing import Optional, Callable
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import (
    ViuLogger,
    viu_correlation_context,
    viu_trace_id_context,
    viu_span_id_context,
)
from .config import ViuLoguruConfig


class ViuCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware para injeção e propagação de Correlation IDs

    Usage:
        from viu_loguru.middleware import ViuCorrelationMiddleware

        app = FastAPI()

        app.add_middleware(
            ViuCorrelationMiddleware,
            service_name="my-api",
            environment="production",
        )
    """

    def __init__(
        self,
        app: Callable,
        service_name: str = "unknown-service",
        environment: str = "development",
        kafka_brokers: str = "localhost:9092",
        kafka_topic: str = "logs.app.raw",
    ):
        super().__init__(app)
        self.service_name = service_name
        self.environment = environment
        self.kafka_brokers = kafka_brokers
        self.kafka_topic = kafka_topic

        self._logger: Optional[ViuLogger] = None

    def _get_logger(self) -> ViuLogger:
        """Obtém ou cria o logger"""
        if self._logger is None:
            config = ViuLoguruConfig(
                service_name=self.service_name,
                environment=self.environment,
                kafka_brokers=self.kafka_brokers,
                kafka_topic=self.kafka_topic,
            )
            self._logger = ViuLogger.get_instance(config)
            self._logger.initialize()
        return self._logger

    def _generate_correlation_id(self) -> str:
        """Gera um novo correlation ID"""
        return str(uuid4())

    def _get_correlation_id(self, request: Request) -> str:
        """Extrai ou gera correlation ID da request"""
        correlation_header = request.headers.get("X-Correlation-ID")
        if correlation_header:
            return correlation_header
        return self._generate_correlation_id()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa a request e adiciona correlation IDs"""
        correlation_id = self._get_correlation_id(request)
        trace_id = self._generate_correlation_id()
        span_id = str(uuid4())[:16]

        token_correlation = viu_correlation_context.set(correlation_id)
        token_trace = viu_trace_id_context.set(trace_id)
        token_span = viu_span_id_context.set(span_id)

        request.state.correlation_id = correlation_id
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        response = await call_next(request)

        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Trace-ID"] = trace_id

        viu_correlation_context.reset(token_correlation)
        viu_trace_id_context.reset(token_trace)
        viu_span_id_context.reset(token_span)

        return response


def get_correlation_id(request: Request) -> str:
    """Helper para obter correlation ID da request atual"""
    return getattr(request.state, "correlation_id", None) or "unknown"


def get_trace_id(request: Request) -> str:
    """Helper para obter trace ID da request atual"""
    return getattr(request.state, "trace_id", None) or "unknown"


def get_span_id(request: Request) -> str:
    """Helper para obter span ID da request atual"""
    return getattr(request.state, "span_id", None) or "unknown"
