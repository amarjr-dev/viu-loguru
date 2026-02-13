# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-02-12

### Added
- Initial release of viu-loguru
- Support for sending logs to Kafka with Loguru integration
- Circuit breaker pattern for Kafka connection resilience (5 failures → 60s timeout)
- Exponential backoff retry mechanism (2^attempt seconds)
- Gzip compression for log messages
- Smart batching (100 logs or 128KB, whichever comes first)
- Connection timeout (10 seconds)
- Send timeout (5 seconds per message)
- SASL_SSL security protocol as default
- Support for SASL/SCRAM-SHA-256 authentication
- Structured logging with context support
- Correlation ID, Trace ID, and Span ID tracking
- FastAPI/Starlette middleware for request context (optional dependency)
- Configuration via environment variables
- Configuration via dictionary
- Comprehensive test suite with pytest
- Code coverage reporting

### Security
- Default to SASL_SSL for secure connections
- No debug logging in production code
- Clean credential handling

### Performance
- Asynchronous Kafka producer with aiokafka
- Batch processing for efficient message delivery
- Circuit breaker prevents connection storms
- Smart retry mechanism reduces unnecessary attempts

[0.0.1]: https://github.com/amarjr-dev/viu-loguru/releases/tag/viu-loguru-v0.0.1
