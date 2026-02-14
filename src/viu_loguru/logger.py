"""
ViuLogger - Classe principal para logging com Viu
"""

import threading
from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional, Union
from uuid import uuid4

import orjson
from loguru import logger

from .config import TransportMode, ViuConfig, ViuLoguruConfig
from .kafka_producer import ViuKafkaProducer
from .http_producer import HTTPProducer


class ViuLogger:
    """
    Logger Viu integrado com Loguru

    Suporta dois modos de transporte:
    - HTTP (modo padrão): Envia logs via API REST
    - Kafka: Envia logs diretamente para o Kafka

    Usage:
        # Modo HTTP (recomendado)
        viu_logger = ViuLogger(config=ViuLoguruConfig(
            service_name="my-app",
            transport_mode=TransportMode.HTTP,
            api_url="https://api.viu.com",
            api_key="viu_live_xxx"
        ))

        # Modo Kafka (alternativo)
        viu_logger = ViuLogger(config=ViuLoguruConfig(
            service_name="my-app",
            transport_mode=TransportMode.KAFKA,
            kafka_brokers="kafka:9092",
            kafka_topic="logs.tenant-id"
        ))

        # Log simples
        viu_logger.info("User logged in", user_id="123")

        # Log com contexto
        viu_logger.info("Order created", order_id="456", amount=99.90)

        # Log de erro com stack trace
        viu_logger.error("Payment failed", error=str(e), exc_info=True)
    """

    _instance: Optional["ViuLogger"] = None
    _lock = threading.Lock()

    def __init__(self, config: Union[ViuLoguruConfig, ViuConfig]):
        if isinstance(config, ViuConfig):
            config = ViuLoguruConfig(**vars(config))
        self.config: ViuLoguruConfig = config
        self._kafka_producer: Optional[ViuKafkaProducer] = None
        self._http_producer: Optional[HTTPProducer] = None
        self._initialized = False

    @classmethod
    def get_instance(cls, config: Optional[ViuLoguruConfig] = None) -> "ViuLogger":
        """Obtém instância singleton do ViuLogger"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if config is None:
                        config = ViuLoguruConfig.from_env()
                    cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reseta a instância singleton (útil para testes)"""
        with cls._lock:
            if cls._instance is not None:
                if cls._instance._kafka_producer is not None:
                    cls._instance._kafka_producer.close()
                if cls._instance._http_producer is not None:
                    cls._instance._http_producer.close()
            cls._instance = None

    def initialize(self) -> None:
        """Inicializa o logger com Loguru e configura sinks"""
        if self._initialized:
            return

        # Inicializar o producer apropriado baseado no modo
        if self.config.transport_mode == TransportMode.HTTP:
            if not self.config.api_url or not self.config.api_key:
                raise ValueError(
                    "API URL and API Key are required for HTTP mode. "
                    "Set api_url and api_key in config or VIU_API_URL and VIU_API_KEY env vars."
                )
            self._http_producer = HTTPProducer(
                api_url=self.config.api_url,
                api_key=self.config.api_key,
                timeout=self.config.http_timeout,
            )
        else:
            # Modo Kafka (legacy)
            self._kafka_producer = ViuKafkaProducer(
                brokers=self.config.kafka_brokers,
                topic=self.config.kafka_topic,
                username=self.config.kafka_username,
                password=self.config.kafka_password,
                sasl_mechanism=self.config.kafka_sasl_mechanism,
                security_protocol=self.config.kafka_security_protocol,
            )

        logger.remove()

        if self.config.serialize:
            sink = self._create_json_sink()
        else:
            sink = self._create_console_sink()

        logger.add(sink, **self.config.to_loguru_sink_config())

        self._initialized = True

    def _create_json_sink(self) -> Callable:
        """Cria sink que formata logs como JSON"""

        def json_sink(message: "logger.Message") -> None:
            record = self._format_record(message)
            log_entry = self._create_log_entry(record)

            try:
                json_line = orjson.dumps(log_entry).decode("utf-8")
                print(json_line)

                # Enviar via HTTP ou Kafka conforme modo configurado
                if self.config.transport_mode == TransportMode.HTTP:
                    if self._http_producer is not None:
                        self._http_producer.send(log_entry)
                else:
                    if self._kafka_producer is not None:
                        self._kafka_producer.send(json_line)
            except Exception:
                # Fallback silencioso para stdout
                pass

        return json_sink

    def _create_console_sink(self) -> Callable:
        """Cria sink para console (desenvolvimento)"""

        def console_sink(message: "logger.Message") -> None:
            print(message)

        return console_sink

    def _format_record(self, message: "logger.Message") -> Dict[str, Any]:
        """Formata o record do Loguru"""
        record = message.record
        return {
            "timestamp": record["time"].isoformat()
            if hasattr(record["time"], "isoformat")
            else str(record["time"]),
            "level": record["level"].name
            if hasattr(record["level"], "name")
            else str(record["level"]),
            "message": record["message"],
            "module": record["module"],
            "file": record["file"].path
            if hasattr(record["file"], "path")
            else str(record["file"]),
            "line": record["line"],
            "function": record["function"],
            "exception": record["exception"] if record["exception"] else None,
        }

    def _create_log_entry(
        self,
        record: Dict[str, Any],
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Cria entrada de log padronizada no formato Viu"""
        correlation_id = viu_correlation_context.get(None)

        entry = {
            "timestamp": record["timestamp"],
            "level": record["level"],
            "service": self.config.service_name,
            "environment": self.config.environment,
            "message": record["message"],
            "correlation_id": correlation_id or str(uuid4()),
            "trace_id": viu_trace_id_context.get(None) or correlation_id,
            "span_id": viu_span_id_context.get(None),
            "module": record["module"],
            "file": record["file"],
            "line": record["line"],
            "context": extra or {},
        }

        if record["exception"]:
            entry["error"] = {
                "type": type(record["exception"][1]).__name__
                if record["exception"][1]
                else "Exception",
                "message": str(record["exception"][1])
                if record["exception"][1]
                else str(record["exception"][0]),
                "stacktrace": record["exception"][2]
                if len(record["exception"]) > 2
                else None,
            }

        for key, value in self.config.extra_labels.items():
            entry[key] = value

        return entry

    def log(
        self,
        level: str,
        message: str,
        exc_info: bool = False,
        **extra: Any,
    ) -> None:
        """Método base para logging"""
        if not self._initialized:
            self.initialize()

        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, **extra: Any) -> None:
        """Log em nível DEBUG"""
        self.log("DEBUG", message, **extra)

    def info(self, message: str, **extra: Any) -> None:
        """Log em nível INFO"""
        self.log("INFO", message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        """Log em nível WARNING"""
        self.log("WARNING", message, **extra)

    def warn(self, message: str, **extra: Any) -> None:
        """Log em nível WARN (alias)"""
        self.log("WARNING", message, **extra)

    def error(self, message: str, exc_info: bool = False, **extra: Any) -> None:
        """Log em nível ERROR"""
        self.log("ERROR", message, exc_info=exc_info, **extra)

    def exception(self, message: str, **extra: Any) -> None:
        """Log de exception com stack trace"""
        self.log("ERROR", message, exc_info=True, **extra)

    def critical(self, message: str, **extra: Any) -> None:
        """Log em nível CRITICAL"""
        self.log("CRITICAL", message, **extra)

    def close(self) -> None:
        """Fecha conexões e limpa recursos"""
        if self._kafka_producer is not None:
            self._kafka_producer.close()
        if self._http_producer is not None:
            self._http_producer.close()
        logger.remove()
        self._initialized = False


def setup_viu_logger(
    service_name: str,
    environment: str = "development",
    # Modo HTTP (padrão)
    transport_mode: str = "http",
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    # Modo Kafka (alternativo)
    kafka_brokers: str = "localhost:9092",
    kafka_topic: str = "logs.app.raw",
    level: str = "INFO",
) -> ViuLogger:
    """
    Função helper para setup rápido do ViuLogger

    Usage:
        # Modo HTTP (recomendado)
        viu_logger = setup_viu_logger(
            service_name="my-api",
            environment="production",
            transport_mode="http",
            api_url="https://api.viu.com",
            api_key="viu_live_xxx"
        )

        # Modo Kafka
        viu_logger = setup_viu_logger(
            service_name="my-api",
            environment="production",
            transport_mode="kafka",
            kafka_brokers="kafka:9092",
            kafka_topic="logs.tenant-id"
        )
    """
    mode = (
        TransportMode.KAFKA if transport_mode.lower() == "kafka" else TransportMode.HTTP
    )

    config = ViuLoguruConfig(
        service_name=service_name,
        environment=environment,
        transport_mode=mode,
        api_url=api_url,
        api_key=api_key,
        kafka_brokers=kafka_brokers,
        kafka_topic=kafka_topic,
        level=level,
    )

    viu_logger = ViuLogger.get_instance(config)
    viu_logger.initialize()

    return viu_logger


_correlation_id_context: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
viu_correlation_context = _correlation_id_context

_trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
viu_trace_id_context = _trace_id_context

_span_id_context: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
viu_span_id_context = _span_id_context

_request_context: ContextVar[Dict[str, Any]] = ContextVar(
    "request_context", default=None
)
viu_request_context = _request_context
