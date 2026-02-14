"""
Configuração do Viu Loguru Adapter
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TransportMode(str, Enum):
    """Modo de transporte dos logs"""

    KAFKA = "kafka"
    HTTP = "http"


@dataclass
class ViuConfig:
    """
    Configuração base do Viu

    Args:
        service_name: Nome do serviço/aplicação
        environment: Ambiente (development, production, etc)

        # Modo de transporte (kafka ou http)
        transport_mode: Modo de envio dos logs (kafka|http)

        # Configuração HTTP
        api_url: URL da API do VIU (para modo HTTP)
        api_key: API Key do tenant (para modo HTTP)

        # Configuração Kafka
        kafka_brokers: Endereço dos brokers Kafka
        kafka_topic: Topic Kafka para envio dos logs
        kafka_username: Username para SASL authentication
        kafka_password: Password para SASL authentication
        kafka_sasl_mechanism: Mecanismo SASL (SCRAM-SHA-256, SCRAM-SHA-512, PLAIN)
        kafka_security_protocol: Protocolo de segurança (SASL_SSL, SASL_PLAINTEXT)

        # Configuração comum
        correlation_id_header: Nome do header para correlation ID
        service_header: Nome do header para nome do serviço
        extra_labels: Labels adicionais para os logs
    """

    service_name: str
    environment: str = "development"

    # Modo de transporte
    transport_mode: TransportMode = TransportMode.HTTP

    # Configuração HTTP (modo recomendado)
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    http_timeout: int = 10

    # Configuração Kafka (modo alternativo)
    kafka_brokers: str = "localhost:9092"
    kafka_topic: str = "logs.app.raw"
    kafka_username: Optional[str] = None
    kafka_password: Optional[str] = None
    kafka_sasl_mechanism: str = "SCRAM-SHA-256"
    kafka_security_protocol: str = "SASL_SSL"

    # Configuração comum
    correlation_id_header: str = "X-Correlation-ID"
    service_header: str = "X-Service-Name"
    extra_labels: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "ViuConfig":
        """Cria configuração a partir de variáveis de ambiente"""
        # Determina o modo de transporte
        transport_mode = os.getenv("VIU_TRANSPORT_MODE", "http").lower()
        if transport_mode == "kafka":
            mode = TransportMode.KAFKA
        else:
            mode = TransportMode.HTTP

        return cls(
            service_name=os.getenv("VIU_SERVICE_NAME", "unknown-service"),
            environment=os.getenv("VIU_ENVIRONMENT", "development"),
            transport_mode=mode,
            # HTTP config
            api_url=os.getenv("VIU_API_URL", None),
            api_key=os.getenv("VIU_API_KEY", None),
            http_timeout=int(os.getenv("VIU_HTTP_TIMEOUT", "10")),
            # Kafka config
            kafka_brokers=os.getenv("VIU_KAFKA_BROKERS", "localhost:9092"),
            kafka_topic=os.getenv("VIU_KAFKA_TOPIC", "logs.app.raw"),
            kafka_username=os.getenv("VIU_KAFKA_USERNAME", None),
            kafka_password=os.getenv("VIU_KAFKA_PASSWORD", None),
            kafka_sasl_mechanism=os.getenv("VIU_KAFKA_SASL_MECHANISM", "SCRAM-SHA-256"),
            kafka_security_protocol=os.getenv(
                "VIU_KAFKA_SECURITY_PROTOCOL", "SASL_SSL"
            ),
            correlation_id_header=os.getenv(
                "VIU_CORRELATION_ID_HEADER", "X-Correlation-ID"
            ),
            service_header=os.getenv("VIU_SERVICE_HEADER", "X-Service-Name"),
            extra_labels={},
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ViuConfig":
        """Cria configuração a partir de dicionário"""
        transport_mode = data.get("transport_mode", "http").lower()
        if transport_mode == "kafka":
            mode = TransportMode.KAFKA
        else:
            mode = TransportMode.HTTP

        return cls(
            service_name=data.get("service_name", "unknown-service"),
            environment=data.get("environment", "development"),
            transport_mode=mode,
            # HTTP config
            api_url=data.get("api_url", None),
            api_key=data.get("api_key", None),
            http_timeout=data.get("http_timeout", 10),
            # Kafka config
            kafka_brokers=data.get("kafka_brokers", "localhost:9092"),
            kafka_topic=data.get("kafka_topic", "logs.app.raw"),
            kafka_username=data.get("kafka_username", None),
            kafka_password=data.get("kafka_password", None),
            kafka_sasl_mechanism=data.get("kafka_sasl_mechanism", "SCRAM-SHA-256"),
            kafka_security_protocol=data.get("kafka_security_protocol", "SASL_SSL"),
            correlation_id_header=data.get("correlation_id_header", "X-Correlation-ID"),
            service_header=data.get("correlation_id_header", "X-Service-Name"),
            extra_labels=data.get("extra_labels", {}),
        )


@dataclass
class ViuLoguruConfig(ViuConfig):
    """
    Configuração específica para Loguru

    Args:
        level: Nível mínimo de log
        format: Formato da mensagem de log
        serialize: Se True, logs serão JSON
        backtrace: Ativar backtrace para exceptions
        diagnose: Ativar diagnose para exceptions
        enqueue: Enviar logs de forma assíncrona
        queue_size: Tamanho da fila assíncrona
        filter_extra_keys: Keys extras para incluir no log
    """

    level: str = "INFO"
    format: str = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{extra[correlation_id]:<36} | {message}"
    )
    serialize: bool = True
    backtrace: bool = True
    diagnose: bool = True
    enqueue: bool = True
    queue_size: int = 10000
    filter_extra_keys: tuple = ()

    def to_loguru_sink_config(self) -> Dict[str, Any]:
        """Retorna configuração para uso com Loguru sink"""
        return {
            "serialize": self.serialize,
            "backtrace": self.backtrace,
            "diagnose": self.diagnose,
            "enqueue": self.enqueue,
        }
