"""
Tests for ViuLogger core functionality
"""

from unittest.mock import Mock, patch

import pytest
from viu_loguru.config import ViuConfig
from viu_loguru.logger import ViuLogger


class TestViuLogger:
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return ViuConfig(
            service_name="test-service",
            environment="test",
            kafka_brokers="localhost:9092",
        )

    @pytest.fixture
    def logger(self, config):
        """Create logger instance"""
        return ViuLogger(config)

    def test_logger_initialization(self, logger, config):
        """Test logger initialization"""
        assert logger.config.service_name == config.service_name
        assert logger.config.environment == config.environment

    def test_log_entry_format(self, logger):
        """Test log entry formatting"""
        with patch.object(logger, "_kafka_producer") as mock_producer:
            mock_producer.send = Mock()

            logger.info("Test message", user_id="123")

            # Verify producer was called
            assert mock_producer.send.called

    def test_correlation_id_context(self, logger):
        """Test correlation ID context management"""
        from viu_loguru.context import viu_correlation_context

        correlation_id = "test-correlation-123"
        token = viu_correlation_context.set(correlation_id)

        try:
            assert viu_correlation_context.get() == correlation_id
        finally:
            viu_correlation_context.reset(token)

    @patch("viu_loguru.logger.ViuLogger._kafka_producer")
    def test_logging_without_kafka(self, mock_producer, logger):
        """Test logging when Kafka is not available"""
        mock_producer = None

        # Should not raise exception
        logger.info("Test message without Kafka")
        logger.error("Error message without Kafka")

    def test_structured_logging(self, logger):
        """Test structured logging with context"""
        with patch.object(logger, "_kafka_producer") as mock_producer:
            mock_producer.send = Mock()

            logger.info(
                "User action",
                user_id="user123",
                action="login",
                ip_address="192.168.1.1",
            )

            assert mock_producer.send.called
