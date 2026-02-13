"""
Tests for Kafka producer functionality
"""

from unittest.mock import AsyncMock, patch

import pytest
from viu_loguru.config import ViuConfig
from viu_loguru.kafka_producer import (
    CircuitBreaker,
    ViuKafkaProducer,
    ViuKafkaProducerSync,
)


class TestCircuitBreaker:
    def test_initial_state(self):
        """Test circuit breaker initial state"""
        cb = CircuitBreaker(failure_threshold=3, timeout=10)

        assert cb.can_attempt() is True
        assert cb.state == "closed"

    def test_failure_recording(self):
        """Test failure recording"""
        cb = CircuitBreaker(failure_threshold=3, timeout=10)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"

        cb.record_failure()
        assert cb.state == "open"
        assert cb.can_attempt() is False

    def test_success_reset(self):
        """Test success resets failure count"""
        cb = CircuitBreaker(failure_threshold=3, timeout=10)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        assert cb.failures == 0
        assert cb.state == "closed"


@pytest.mark.asyncio
class TestViuKafkaProducer:
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return ViuConfig(
            service_name="test-service",
            kafka_brokers="localhost:9092",
            kafka_username="test",
            kafka_password="test",
        )

    @pytest.fixture
    async def producer(self, config):
        """Create producer instance"""
        prod = ViuKafkaProducer(config)
        yield prod
        if prod._producer:
            await prod.close()

    async def test_producer_initialization(self, producer, config):
        """Test producer initialization"""
        assert producer.config.kafka_brokers == config.kafka_brokers
        assert producer.topic == config.kafka_topic

    @patch("viu_loguru.kafka_producer.AIOKafkaProducer")
    async def test_connect_success(self, mock_producer_class, producer):
        """Test successful connection"""
        mock_instance = AsyncMock()
        mock_producer_class.return_value = mock_instance

        await producer.connect()

        assert mock_instance.start.called

    @patch("viu_loguru.kafka_producer.AIOKafkaProducer")
    async def test_send_with_retry(self, mock_producer_class, producer):
        """Test send with retry logic"""
        mock_instance = AsyncMock()
        mock_instance.send_and_wait = AsyncMock()
        mock_producer_class.return_value = mock_instance

        producer._producer = mock_instance

        await producer._send_with_retry("test log", max_retries=2)

        assert mock_instance.send_and_wait.called

    async def test_batch_flushing(self, producer):
        """Test batch flush mechanism"""
        with patch.object(producer, "_producer") as mock_producer:
            mock_producer.send_and_wait = AsyncMock()

            for i in range(5):
                producer._batch.append(f"log_{i}")

            await producer.flush()

            assert len(producer._batch) == 0


class TestViuKafkaProducerSync:
    def test_sync_producer_initialization(self):
        """Test synchronous producer initialization"""
        config = ViuConfig(service_name="test-service", kafka_brokers="localhost:9092")

        producer = ViuKafkaProducerSync(config)
        assert producer.config.service_name == "test-service"
