"""
Tests for ViuLogger configuration
"""

from viu_loguru.config import ViuConfig, ViuLoguruConfig


class TestViuConfig:
    def test_default_values(self):
        """Test default configuration values"""
        config = ViuConfig(service_name="test-service", environment="test")

        assert config.service_name == "test-service"
        assert config.environment == "test"
        assert config.kafka_brokers == "localhost:9092"
        assert config.kafka_topic == "logs.app.raw"
        assert config.kafka_security_protocol == "SASL_SSL"
        assert config.kafka_sasl_mechanism == "SCRAM-SHA-256"

    def test_custom_kafka_config(self):
        """Test custom Kafka configuration"""
        config = ViuConfig(
            service_name="test-service",
            kafka_brokers="kafka.example.com:9093",
            kafka_topic="custom.topic",
            kafka_username="user123",
            kafka_password="pass123",
        )

        assert config.kafka_brokers == "kafka.example.com:9093"
        assert config.kafka_topic == "custom.topic"
        assert config.kafka_username == "user123"
        assert config.kafka_password == "pass123"

    def test_from_env(self, monkeypatch):
        """Test configuration from environment variables"""
        monkeypatch.setenv("VIU_SERVICE_NAME", "env-service")
        monkeypatch.setenv("VIU_ENVIRONMENT", "production")
        monkeypatch.setenv("VIU_KAFKA_BROKERS", "kafka.prod.com:9092")
        monkeypatch.setenv("VIU_KAFKA_USERNAME", "prod_user")
        monkeypatch.setenv("VIU_KAFKA_PASSWORD", "prod_pass")

        config = ViuConfig.from_env()

        assert config.service_name == "env-service"
        assert config.environment == "production"
        assert config.kafka_brokers == "kafka.prod.com:9092"
        assert config.kafka_username == "prod_user"
        assert config.kafka_password == "prod_pass"

    def test_from_dict(self):
        """Test configuration from dictionary"""
        data = {
            "service_name": "dict-service",
            "environment": "staging",
            "kafka_brokers": "kafka.staging.com:9092",
            "kafka_topic": "logs.staging",
        }

        config = ViuConfig.from_dict(data)

        assert config.service_name == "dict-service"
        assert config.environment == "staging"
        assert config.kafka_brokers == "kafka.staging.com:9092"
        assert config.kafka_topic == "logs.staging"


class TestViuLoguruConfig:
    def test_loguru_config_defaults(self):
        """Test Loguru-specific configuration"""
        config = ViuLoguruConfig(service_name="test-service", log_level="DEBUG")

        assert config.log_level == "DEBUG"
        assert config.serialize is True
        assert config.colorize is False
