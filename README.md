# viu-loguru

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/viu-loguru.svg)](https://pypi.org/project/viu-loguru/)
[![Python versions](https://img.shields.io/pypi/pyversions/viu-loguru.svg)](https://pypi.org/project/viu-loguru/)
[![License](https://img.shields.io/github/license/viu-team/viu)](https://github.com/viu-team/viu/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/viu-loguru.svg)](https://pypi.org/project/viu-loguru/)
[![Test Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](https://github.com/viu-team/viu)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white)
![Loguru](https://img.shields.io/badge/Loguru-00A98F?style=for-the-badge&logo=python&logoColor=white)

</div>

**Adapter Loguru para envio de logs ao sistema Viu (Kafka + Loki)**

## ✨ Quer ver o erro? → Joga no Viu.

Viu-loguru é uma biblioteca Python que integra o [Loguru](https://github.com/Delgan/loguru) com Kafka e Loki, oferecendo logging estruturado, rastreabilidade e observabilidade de alta performance para suas aplicações.

### 🚀 Features

- ✅ **Circuit Breaker** - Previne connection storms (5 falhas → 60s timeout)
- ✅ **Exponential Backoff** - Retry inteligente (2^attempt segundos)
- ✅ **Compression** - Gzip para redução de tráfego
- ✅ **Smart Batching** - 100 logs ou 128KB (o que vier primeiro)
- ✅ **Timeouts** - 10s conexão, 5s envio
- ✅ **Security First** - SASL_SSL por padrão
- ✅ **Correlation IDs** - Rastreamento de requisições
- ✅ **FastAPI Middleware** - Integração nativa (opcional)
- ✅ **Async by default** - Performance máxima com aiokafka

## 📦 Instalação

```bash
# Instalação básica
pip install viu-loguru

# Com suporte FastAPI
pip install viu-loguru[fastapi]

# Com suporte Django
pip install viu-loguru[django]

# Com suporte Flask
pip install viu-loguru[flask]

# Versão síncrona (kafka-python)
pip install viu-loguru[sync]
```

## 🎯 Quick Start

### Uso Básico

```python
from viu_loguru import ViuLogger, ViuConfig

# Configuração para desenvolvimento (sem autenticação)
config = ViuConfig(
    service_name="my-api",
    environment="development",
    kafka_brokers="localhost:9092",
    kafka_topic="logs.app.raw"
)

# Criar logger
logger = ViuLogger(config)

# Logging estruturado
logger.info("User logged in", user_id="123", ip="192.168.1.1")
logger.error("Payment failed", error_code="E001", amount=99.90)
logger.warning("High memory usage", memory_percent=85.5)
```

### 🔐 Produção com Autenticação SASL

```python
from viu_loguru import ViuLogger, ViuConfig

config = ViuConfig(
    service_name="my-api",
    environment="production",
    kafka_brokers="viu-kafka.example.com:9092",
    kafka_topic="logs.production",
    kafka_username="viu_tenant123abc",
    kafka_password="your-secure-password",
    kafka_sasl_mechanism="SCRAM-SHA-256",
    kafka_security_protocol="SASL_SSL"  # Default!
)

logger = ViuLogger(config)
logger.info("Application started", version="1.2.3")
```

### 🌍 Configuração via Environment Variables

```bash
export VIU_SERVICE_NAME=my-api
export VIU_ENVIRONMENT=production
export VIU_KAFKA_BROKERS=viu-kafka.example.com:9092
export VIU_KAFKA_TOPIC=logs.production
export VIU_KAFKA_USERNAME=viu_tenant123abc
export VIU_KAFKA_PASSWORD=your-secure-password
export VIU_KAFKA_SASL_MECHANISM=SCRAM-SHA-256
export VIU_KAFKA_SECURITY_PROTOCOL=SASL_SSL
```

```python
from viu_loguru import ViuLogger, ViuConfig

# Carrega automaticamente das variáveis de ambiente
config = ViuConfig.from_env()
logger = ViuLogger(config)
```

### 🔄 Integração com FastAPI

```python
from fastapi import FastAPI, Request
from viu_loguru.middleware import ViuCorrelationMiddleware
from viu_loguru import ViuLogger, ViuConfig

app = FastAPI()

# Adicionar middleware para correlation IDs
app.add_middleware(
    ViuCorrelationMiddleware,
    service_name="my-api",
    environment="production",
    kafka_brokers="kafka.example.com:9092",
    kafka_username="user",
    kafka_password="pass"
)

# Logger estará disponível em todos os requests
@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    logger = ViuLogger(ViuConfig.from_env())
    logger.info("Fetching user", user_id=user_id)
    # request.state.correlation_id está disponível
    return {"user_id": user_id}
```

### 📊 Logging Estruturado Avançado

```python
# Contexto rico
logger.info(
    "User action completed",
    user_id="user_123",
    action="purchase",
    product_id="prod_456",
    amount=149.99,
    currency="USD",
    payment_method="credit_card",
    duration_ms=234
)

# Tratamento de exceções
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        error_type=type(e).__name__,
        error_message=str(e),
        exc_info=True  # Inclui stack trace
    )
```

### 🔍 Correlation IDs e Rastreamento

```python
from viu_loguru.context import viu_correlation_context

# Definir correlation ID manualmente
token = viu_correlation_context.set("request-123-abc")

try:
    logger.info("Processing request")  # Inclui correlation_id automaticamente
    # ... seu código
finally:
    viu_correlation_context.reset(token)
```

## ⚙️ Configuração

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `VIU_SERVICE_NAME` | Nome do serviço | `unknown-service` |
| `VIU_ENVIRONMENT` | Ambiente (dev/staging/prod) | `development` |
| `VIU_KAFKA_BROKERS` | Endereço Kafka | `localhost:9092` |
| `VIU_KAFKA_TOPIC` | Topic Kafka | `logs.app.raw` |
| `VIU_KAFKA_USERNAME` | Username SASL | (opcional) |
| `VIU_KAFKA_PASSWORD` | Password SASL | (opcional) |
| `VIU_KAFKA_SASL_MECHANISM` | Mecanismo SASL | `SCRAM-SHA-256` |
| `VIU_KAFKA_SECURITY_PROTOCOL` | Protocolo | `SASL_SSL` |

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install viu-loguru[test]

# Rodar testes
pytest

# Com cobertura
pytest --cov=viu_loguru --cov-report=html --cov-report=term

# Testes específicos
pytest tests/test_logger.py -v
```

## 📈 Performance

- **Batching**: Agrupa até 100 logs ou 128KB antes de enviar
- **Compression**: Reduz tráfego em ~70% com gzip
- **Circuit Breaker**: Evita sobrecarga em falhas
- **Async**: Não bloqueia sua aplicação
- **Timeouts**: Previne travamentos

## 🔒 Segurança

- SASL_SSL ativado por padrão
- Credenciais nunca aparecem nos logs
- Suporte TLS/SSL completo
- Opções de autenticação: SCRAM-SHA-256, SCRAM-SHA-512, PLAIN

## 🤝 Contributing

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](../../CONTRIBUTING.md).

## 📄 License

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🔗 Links

- [Documentação](https://github.com/viu-team/viu/tree/main/sdks-monorepo/packages/viu-loguru)
- [Issues](https://github.com/viu-team/viu/issues)
- [PyPI](https://pypi.org/project/viu-loguru/)
- [Changelog](CHANGELOG.md)

---

<div align="center">
  <sub>Built with ❤️ by amar.jr</sub>
</div>
