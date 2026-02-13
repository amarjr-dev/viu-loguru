"""
Context Managers para Correlation IDs

Usage:
    from viu_loguru.context import viu_correlation_context, viu_request_context

    # Definir correlation ID para um bloco de código
    with viu_correlation_context(correlation_id="custom-id"):
        viu_logger.info("This log will have custom-id")

    # Usar contexto de request
    viu_request_context.set({"user_id": "123", "order_id": "456"})
    viu_logger.info("Order processed")
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Dict, Any, Generator, Optional


_correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
_parent_span_id_var: ContextVar[Optional[str]] = ContextVar(
    "parent_span_id", default=None
)
_request_context_var: ContextVar[Any] = ContextVar("request_context", default=None)


class viu_correlation_context:
    """
    Context manager para correlation ID

    Usage:
        from viu_loguru.context import viu_correlation_context

        viu_correlation_context.set("my-correlation-id")
        viu_logger.info("Log with correlation ID")

        with viu_correlation_context("another-id"):
            viu_logger.info("Log with different correlation ID")
    """

    @staticmethod
    def get(default: Optional[str] = None) -> Optional[str]:
        """Obtém o correlation ID atual"""
        return _correlation_id_var.get(default)

    @staticmethod
    def set(value: str) -> None:
        """Define o correlation ID"""
        _correlation_id_var.set(value)

    @staticmethod
    def reset() -> None:
        """Reseta o correlation ID"""
        _correlation_id_var.set(None)

    @staticmethod
    @contextmanager
    def manager(value: str) -> Generator[str, None, None]:
        """
        Context manager para correlation ID

        Usage:
            with viu_correlation_context.manager("custom-id"):
                viu_logger.info("Logs within this block")
        """
        token = _correlation_id_var.set(value)
        try:
            yield value
        finally:
            _correlation_id_var.reset(token)


class viu_trace_id_context:
    """Context manager para trace ID"""

    @staticmethod
    def get(default: Optional[str] = None) -> Optional[str]:
        return _trace_id_var.get(default)

    @staticmethod
    def set(value: str) -> None:
        _trace_id_var.set(value)

    @staticmethod
    def reset() -> None:
        _trace_id_var.set(None)

    @staticmethod
    @contextmanager
    def manager(value: str) -> Generator[str, None, None]:
        token = _trace_id_var.set(value)
        try:
            yield value
        finally:
            _trace_id_var.reset(token)


class viu_span_id_context:
    """Context manager para span ID"""

    @staticmethod
    def get(default: Optional[str] = None) -> Optional[str]:
        return _span_id_var.get(default)

    @staticmethod
    def set(value: str) -> None:
        _span_id_var.set(value)

    @staticmethod
    def reset() -> None:
        _span_id_var.set(None)

    @staticmethod
    @contextmanager
    def manager(value: str) -> Generator[str, None, None]:
        token = _span_id_var.set(value)
        try:
            yield value
        finally:
            _span_id_var.reset(token)


class viu_request_context:
    """
    Context manager para contexto de request

    Usage:
        from viu_loguru.context import viu_request_context

        viu_request_context.set({"user_id": "123"})
        viu_logger.info("User action")

        with viu_request_context.manager({"order_id": "456"}):
            viu_logger.info("Order action")
    """

    @staticmethod
    def get(default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Obtém o contexto atual"""
        result = _request_context_var.get(None)
        return result if result is not None else (default or {})

    @staticmethod
    def set(value: Dict[str, Any]) -> None:
        """Define o contexto"""
        _request_context_var.set(value)

    @staticmethod
    def update(**kwargs: Any) -> None:
        """Atualiza o contexto com novos valores"""
        current = _request_context_var.get({})
        _request_context_var.set({**current, **kwargs})

    @staticmethod
    def reset() -> None:
        """Reseta o contexto"""
        _request_context_var.set({})

    @staticmethod
    @contextmanager
    def manager(**kwargs: Any) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager para contexto de request

        Usage:
            with viu_request_context.manager(user_id="123", order_id="456"):
                viu_logger.info("Order processed")
        """
        token = _request_context_var.set(kwargs)
        try:
            yield kwargs
        finally:
            _request_context_var.reset(token)


def create_child_span() -> Dict[str, Any]:
    """
    Cria um novo span como filho do span atual

    Returns:
        Dict com span_id e parent_span_id

    Usage:
        child_span = create_child_span()
        viu_logger.info("Child span operation", **child_span)
    """
    import uuid

    parent_span_id = viu_span_id_context.get(None)
    if parent_span_id is None:
        parent_span_id = ""

    span_id = str(uuid.uuid4())[:16]

    token = _span_id_var.set(span_id)
    _parent_span_id_var.set(parent_span_id)

    return {
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "correlation_id": viu_correlation_context.get(None),
        "trace_id": viu_trace_id_context.get(None),
    }
