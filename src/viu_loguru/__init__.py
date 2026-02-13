"""
Viu Loguru Adapter
Adapter Loguru para envio de logs ao sistema Viu (Kafka + Loki)

Quer ver o erro? → Joga no Viu.
"""

__version__ = "0.0.1"

from .config import ViuConfig, ViuLoguruConfig
from .context import viu_correlation_context, viu_request_context
from .logger import ViuLogger

__all__ = [
    "__version__",
    "ViuConfig",
    "ViuLoguruConfig",
    "ViuLogger",
    "viu_correlation_context",
    "viu_request_context",
]

# Optional middleware import (requires starlette/fastapi)
try:
    from .middleware import ViuCorrelationMiddleware

    __all__.append("ViuCorrelationMiddleware")
except ImportError:
    ViuCorrelationMiddleware = None  # type: ignore
