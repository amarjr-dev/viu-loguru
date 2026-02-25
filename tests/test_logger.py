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

    def test_span_id_auto_generation(self, logger):
        """Test span_id is auto-generated when not provided"""
        from viu_loguru.context import viu_span_id_context

        # Ensure context is clean
        viu_span_id_context.reset()

        with patch.object(logger, "_http_producer") as mock_producer:
            mock_producer.send = Mock()
            logger._initialized = True

            # Mock the sink to capture log entry
            captured_entry = {}

            def capture_sink(message):
                nonlocal captured_entry
                record = logger._format_record(message)
                captured_entry = logger._create_log_entry(
                    record, message.record.get("extra", {})
                )

            with patch.object(logger, "_create_json_sink", return_value=capture_sink):
                logger.initialize()
                logger.info("Test message without span_id")

                # Verify span_id was auto-generated (16 chars)
                assert "span_id" in captured_entry
                assert captured_entry["span_id"] is not None
                assert len(captured_entry["span_id"]) == 16

    def test_span_id_manual_override(self, logger):
        """Test manually provided span_id has priority over auto-generation"""
        from viu_loguru.context import viu_span_id_context

        manual_span_id = "manual-span-123"
        token = viu_span_id_context.set(manual_span_id)

        try:
            with patch.object(logger, "_http_producer") as mock_producer:
                mock_producer.send = Mock()
                logger._initialized = True

                captured_entry = {}

                def capture_sink(message):
                    nonlocal captured_entry
                    record = logger._format_record(message)
                    captured_entry = logger._create_log_entry(
                        record, message.record.get("extra", {})
                    )

                with patch.object(
                    logger, "_create_json_sink", return_value=capture_sink
                ):
                    logger.initialize()
                    logger.info("Test message with manual span_id")

                    # Verify manual span_id was used
                    assert captured_entry["span_id"] == manual_span_id
        finally:
            viu_span_id_context.reset(token)

    def test_span_id_explicit_in_log_call(self, logger):
        """Test span_id provided in log call has highest priority"""
        from viu_loguru.context import viu_span_id_context

        # Set context span_id
        viu_span_id_context.set("context-span-456")

        explicit_span_id = "explicit-789"

        with patch.object(logger, "_http_producer") as mock_producer:
            mock_producer.send = Mock()
            logger._initialized = True

            captured_entry = {}

            def capture_sink(message):
                nonlocal captured_entry
                record = logger._format_record(message)
                captured_entry = logger._create_log_entry(
                    record, message.record.get("extra", {})
                )

            with patch.object(logger, "_create_json_sink", return_value=capture_sink):
                logger.initialize()
                logger.info("Test message", span_id=explicit_span_id)

                # Verify explicit span_id has priority
                assert captured_entry["span_id"] == explicit_span_id
