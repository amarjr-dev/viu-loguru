"""
Auto-detecção de headers de tracing

Supported formats:
- X-Correlation-ID
- X-Request-ID
- traceparent (W3C standard)
- X-B3-TraceId (Zipkin B3)
- X-B3-SpanId (Zipkin B3)
"""

import os
from typing import Dict, Optional
from contextvars import ContextVar
from dataclasses import dataclass


_trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_span_id_context: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


@dataclass
class TraceHeaders:
    """Headers de tracing detectados"""

    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


def parse_traceparent(traceparent: str) -> Optional[Dict[str, str]]:
    """
    Parse W3C traceparent header

    Format: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
    Parts:  version-traceId-spanId-flags
    """
    if not traceparent:
        return None

    try:
        parts = traceparent.split("-")
        if len(parts) < 3:
            return None

        # Versão (ignorar)
        # traceId: 16 ou 32 chars hex
        # spanId: 16 chars hex
        # flags: 2 chars hex (opcional)

        trace_id = parts[1] if len(parts) > 1 else None
        span_id = parts[2] if len(parts) > 2 else None

        # span_id pode conter flags, separar
        if span_id and len(span_id) > 16:
            span_id = span_id[:16]

        return {"trace_id": trace_id, "span_id": span_id}
    except Exception:
        return None


def detect_trace_headers_from_dict(headers: Dict[str, str]) -> TraceHeaders:
    """
    Detecta headers de tracing de um dicionário de headers HTTP

    Args:
        headers: Dicionário com headers (case-insensitive)

    Returns:
        TraceHeaders com os valores encontrados
    """
    # Normalizar keys para lowercase
    normalized = {k.lower(): v for k, v in headers.items()}

    result = TraceHeaders()

    # 1. traceparent (W3C) - prioritário
    traceparent = normalized.get("traceparent")
    if traceparent:
        parsed = parse_traceparent(traceparent)
        if parsed:
            result.trace_id = parsed.get("trace_id")
            result.span_id = parsed.get("span_id")

    # 2. X-B3-TraceId (Zipkin)
    if not result.trace_id:
        result.trace_id = normalized.get("x-b3-traceid")

    # 3. X-B3-SpanId (Zipkin)
    if not result.span_id:
        result.span_id = normalized.get("x-b3-spanid")

    # 4. X-Correlation-ID
    result.correlation_id = normalized.get("x-correlation-id")

    # 5. X-Request-ID (fallback para correlation)
    if not result.correlation_id:
        result.correlation_id = normalized.get("x-request-id")

    # 6. X-Trace-ID (outro formato comum)
    if not result.trace_id:
        result.trace_id = normalized.get("x-trace-id")

    return result


def detect_trace_headers_from_env() -> TraceHeaders:
    """
    Detecta headers de tracing das variáveis de ambiente

    Útil para ambientes onde headers são passados como env vars
    """
    result = TraceHeaders()

    # Verificar variáveis de ambiente comuns
    result.correlation_id = os.environ.get("VIU_CORRELATION_ID")
    result.trace_id = os.environ.get("VIU_TRACE_ID")
    result.span_id = os.environ.get("VIU_SPAN_ID")

    return result


def set_trace_context(
    trace_id: Optional[str] = None, span_id: Optional[str] = None
) -> None:
    """Define trace context para a requisição atual"""
    if trace_id:
        _trace_id_context.set(trace_id)
    if span_id:
        _span_id_context.set(span_id)


def get_trace_context() -> tuple:
    """Obtém trace context atual"""
    return _trace_id_context.get(), _span_id_context.get()


def clear_trace_context() -> None:
    """Limpa trace context"""
    _trace_id_context.set(None)
    _span_id_context.set(None)
