"""
Viu Loguru Adapter
Adapter Loguru para envio de logs ao sistema Viu (Kafka + Loki + HTTP API)

Quer ver o erro? → Joga no Viu.

Usage:
    # Modo HTTP (recomendado)
    from viu_loguru import ViuLogger, TransportMode

    viu = ViuLogger(config=ViuLoguruConfig(
        service_name="my-app",
        transport_mode=TransportMode.HTTP,
        api_url="https://api.viu.com",
        api_key="viu_live_xxx"
    ))
    viu.info("Hello World")

    # Modo Kafka (alternativo)
    from viu_loguru import ViuLogger, TransportMode

    viu = ViuLogger(config=ViuLoguruConfig(
        service_name="my-app",
        transport_mode=TransportMode.KAFKA,
        kafka_brokers="kafka:9092",
        kafka_topic="logs.tenant-id"
    ))
    viu.info("Hello World")
"""

__version__ = "0.2.0"

from .config import TransportMode, ViuConfig, ViuLoguruConfig
from .context import viu_correlation_context, viu_request_context
from .http_producer import HTTPProducer
from .logger import ViuLogger, setup_viu_logger
from .trace_headers import (
    detect_trace_headers_from_dict,
    detect_trace_headers_from_env,
    get_trace_context,
    set_trace_context,
)

__all__ = [
    "__version__",
    "ViuConfig",
    "ViuLoguruConfig",
    "ViuLogger",
    "TransportMode",
    "HTTPProducer",
    "setup_viu_logger",
    "viu_correlation_context",
    "viu_request_context",
    # Trace headers
    "detect_trace_headers_from_dict",
    "detect_trace_headers_from_env",
    "set_trace_context",
    "get_trace_context",
]

# Optional middleware import (requires starlette/fastapi)
try:
    from .middleware import ViuCorrelationMiddleware

    __all__.append("ViuCorrelationMiddleware")
except ImportError:
    ViuCorrelationMiddleware = None  # type: ignore
