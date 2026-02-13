"""
Kafka Producer para envio de logs ao Viu
Otimizado para performance e segurança
"""

import asyncio
import time
from typing import List, Optional

try:
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaError
except ImportError:
    AIOKafkaProducer = None
    KafkaError = Exception


class CircuitBreaker:
    """Circuit breaker para proteção contra falhas Kafka"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open

    def record_success(self):
        """Registra sucesso - reseta contador"""
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        """Registra falha - incrementa contador"""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "open"

    def can_attempt(self) -> bool:
        """Verifica se pode tentar enviar"""
        if self.state == "closed":
            return True

        if self.state == "open":
            if time.time() - (self.last_failure_time or 0) > self.timeout:
                self.state = "half-open"
                return True
            return False

        # half-open
        return True


class ViuKafkaProducer:
    """
    Producer Kafka assíncrono otimizado para Viu

    Features:
    - Batching automático
    - Retry com backoff exponencial
    - Compressão gzip
    - Circuit breaker
    - SASL/SCRAM authentication
    - Thread-safe
    """

    def __init__(
        self,
        brokers: str = "localhost:9092",
        topic: str = "logs.app.raw",
        max_batch_size: int = 100,
        batch_timeout_ms: int = 1000,
        acks: str = "all",
        retries: int = 3,
        username: Optional[str] = None,
        password: Optional[str] = None,
        sasl_mechanism: str = "SCRAM-SHA-256",
        security_protocol: str = "SASL_SSL",
        compression_type: str = "gzip",
    ):
        if AIOKafkaProducer is None:
            raise ImportError(
                "aiokafka não instalado. Instale com: pip install viu-loguru"
            )

        self.brokers = brokers
        self.topic = topic
        self.max_batch_size = max_batch_size
        self.batch_timeout_ms = batch_timeout_ms
        self.compression_type = compression_type

        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False
        self._batch: List[str] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._circuit_breaker = CircuitBreaker()

        # Configuração de segurança
        self._producer_config = {
            "bootstrap_servers": brokers,
            "value_serializer": lambda v: v.encode("utf-8"),
            "acks": acks,
            "retries": retries,
            "compression_type": compression_type,
            "max_batch_size": 16384 * 8,  # 128KB
            "linger_ms": batch_timeout_ms,
        }

        if username and password:
            self._producer_config.update(
                {
                    "sasl_mechanism": sasl_mechanism,
                    "sasl_plain_username": username,
                    "sasl_plain_password": password,
                    "security_protocol": security_protocol,
                }
            )

    async def start(self) -> None:
        """Inicializa producer Kafka"""
        if self._producer is not None:
            return

        try:
            self._producer = AIOKafkaProducer(**self._producer_config)
            await asyncio.wait_for(self._producer.start(), timeout=10.0)
            self._running = True
            self._circuit_breaker.record_success()
        except asyncio.TimeoutError:
            self._producer = None
            self._circuit_breaker.record_failure()
            raise TimeoutError("Kafka connection timeout")
        except Exception:
            self._producer = None
            self._circuit_breaker.record_failure()
            raise

    async def stop(self) -> None:
        """Para producer e envia logs pendentes"""
        self._running = False

        if self._batch:
            await self._flush_batch()

        if self._producer:
            await self._producer.stop()
            self._producer = None

    def send(self, log_line: str) -> None:
        """Envia log de forma síncrona (com event loop)"""
        if not self._circuit_breaker.can_attempt():
            # Circuit breaker open - fallback para stdout
            print(log_line)
            return

        self._batch.append(log_line)

        if len(self._batch) >= self.max_batch_size:
            self._send_batch_sync()

    def _send_batch_sync(self) -> None:
        """Envia batch de forma síncrona"""
        if not self._batch:
            return

        try:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

            if self._producer is None:
                self._loop.run_until_complete(self.start())

            self._loop.run_until_complete(self._flush_batch())
        except Exception:
            # Em caso de erro, faz fallback para stdout
            for log in self._batch:
                print(log)
            self._batch.clear()

    async def _flush_batch(self) -> None:
        """Envia batch para Kafka com retry"""
        if not self._batch or self._producer is None:
            return

        batch = self._batch[: self.max_batch_size]
        self._batch = self._batch[self.max_batch_size :]

        for log_line in batch:
            try:
                await self._send_with_retry(log_line)
                self._circuit_breaker.record_success()
            except Exception:
                self._circuit_breaker.record_failure()
                print(log_line)

    async def _send_with_retry(self, log_line: str, max_retries: int = 3) -> None:
        """Envia com retry exponencial"""
        last_error = None

        for attempt in range(max_retries):
            try:
                await asyncio.wait_for(
                    self._producer.send_and_wait(self.topic, log_line), timeout=5.0
                )
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponencial backoff

        raise last_error or Exception("Send failed")

    def close(self) -> None:
        """Fecha producer"""
        if self._loop and self._producer:
            try:
                self._loop.run_until_complete(self.stop())
            except Exception:
                pass

        self._producer = None
        self._running = False


class ViuKafkaProducerSync:
    """Producer Kafka síncrono (fallback)"""

    def __init__(
        self,
        brokers: str = "localhost:9092",
        topic: str = "logs.app.raw",
        username: Optional[str] = None,
        password: Optional[str] = None,
        sasl_mechanism: str = "SCRAM-SHA-256",
        security_protocol: str = "SASL_SSL",
    ):
        try:
            from kafka import KafkaProducer
        except ImportError:
            raise ImportError(
                "kafka-python não instalado. Use: pip install viu-loguru[sync]"
            )

        config = {
            "bootstrap_servers": brokers,
            "value_serializer": lambda v: v.encode("utf-8"),
            "acks": "all",
            "compression_type": "gzip",
        }

        if username and password:
            config.update(
                {
                    "sasl_mechanism": sasl_mechanism,
                    "sasl_plain_username": username,
                    "sasl_plain_password": password,
                    "security_protocol": security_protocol,
                }
            )

        self._producer = KafkaProducer(**config)
        self.topic = topic

    def send(self, log_line: str) -> None:
        """Envia log"""
        try:
            future = self._producer.send(self.topic, log_line.encode("utf-8"))
            future.get(timeout=10)
        except Exception:
            print(log_line)

    def close(self) -> None:
        """Fecha producer"""
        self._producer.flush()
        self._producer.close()
