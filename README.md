# viu-loguru

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/viu-loguru.svg)](https://pypi.org/project/viu-loguru/)
[![Python versions](https://img.shields.io/pypi/pyversions/viu-loguru.svg)](https://pypi.org/project/viu-loguru/)
[![License](https://img.shields.io/github/license/viu-team/viu)](https://github.com/viu-team/viu/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/viu-loguru.svg)](https://pypi.org/project/viu-loguru/)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white)
![Loguru](https://img.shields.io/badge/Loguru-00A98F?style=for-the-badge&logo=python&logoColor=white)

</div>

**Adapter Loguru para envio de logs ao sistema Viu**

## ✨ Quer ver logs? → Joga no Viu. Viu?

viu-loguru é uma biblioteca Python que integra o [Loguru](https://github.com/Delgan/loguru) com o sistema Viu, oferecendo dois modos de transporte:

- **HTTP** (recomendado): Envia logs via API REST
- **Kafka**: Envia logs diretamente para o Kafka

### 🚀 Features

- ✅ **Modo HTTP** - Não expõe Kafka, autenticação via API Key
- ✅ **Modo Kafka** - Para alta performance (legacy)
- ✅ **Circuit Breaker** - Previne connection storms
- ✅ **Exponential Backoff** - Retry inteligente
- ✅ **Compression** - Gzip para redução de tráfego
- ✅ **Smart Batching** - 100 logs ou 128KB
- ✅ **Correlation IDs** - Rastreamento de requisições
- ✅ **FastAPI/Starlette Middleware** - Integração nativa
- ✅ **Async by default** - Performance máxima com aiokafka

## 📦 Instalação

```bash
# Instalação básica
pip install viu-loguru

# Com suporte FastAPI
pip install viu-loguru[fastapi]

# Com suporte Django
pip install viu-loguru[django]

# Versão síncrona (kafka-python)
pip install viu-loguru[sync]
```

## 🎯 Quick Start

### Modo HTTP (Recomendado)

```python
from viu_loguru import ViuLogger, TransportMode

viu = ViuLogger(config=ViuLoguruConfig(
    service_name="my-app",
    environment="production",
    transport_mode=TransportMode.HTTP,
    api_url="http://localhost:3000",  # URL do backend VIU
    api_key="viu_live_xxx"           # Gere no dashboard
))

viu.info("User logged in", user_id="123", ip="192.168.1.1")
viu.error("Payment failed", error_code="E001", amount=99.90)
```

### Modo Kafka (Legacy/Alternativo)

```python
from viu_loguru import ViuLogger, TransportMode

viu = ViuLogger(config=ViuLoguruConfig(
    service_name="my-app",
    environment="production",
    transport_mode=TransportMode.KAFKA,
    kafka_brokers="kafka.example.com:9092",
    kafka_topic="logs.tenant-id",
    kafka_username="tenant_user",
    kafka_password="secure-password"
))

viu.info("Application started", version="1.2.3")
```

## 📝 Exemplos de Uso

### Níveis de Log

#### INFO - Sem contexto
```python
viu.info("Application started")
viu.info("User logged in successfully")
viu.info("Database connection established")
```

#### INFO - Com contexto
```python
viu.info("User logged in", 
    user_id="123", 
    email="user@example.com",
    login_method="oauth"
)

viu.info("Request processed",
    method="GET",
    path="/api/users",
    response_time=45,
    status_code=200
)
```

#### ERROR - Sem contexto
```python
viu.error("Something went wrong")
viu.error("Database connection failed")
```

#### ERROR - Com contexto
```python
try:
    process_payment(order)
except Exception as e:
    viu.error("Payment processing failed",
        error=str(e),
        order_id=order.id,
        amount=order.total,
        currency="BRL",
        user_id=order.user_id
    )
```

#### WARNING - Sem contexto
```python
viu.warning("High memory usage detected")
viu.warning("API rate limit approaching")
```

#### WARNING - Com contexto
```python
viu.warning("Slow query detected",
    query="SELECT * FROM users",
    duration=2500,
    threshold=1000
)

viu.warning("Cache miss",
    key="user:123",
    operation="get_user_profile",
    fallback="database"
)
```

#### DEBUG - Sem contexto
```python
viu.debug("Entering authentication flow")
viu.debug("Cache lookup performed")
```

#### DEBUG - Com contexto
```python
viu.debug("Processing request",
    headers=request.headers,
    body=request.body,
    query=request.query
)

viu.debug("Database query executed",
    sql="SELECT * FROM users WHERE id = ?",
    params=[user_id],
    duration=12
)
```

#### Outros níveis
```python
# CRITICAL - Erros críticos que causam shutdown
viu.critical("Critical system failure",
    error="Out of memory",
    free_memory=0
)

# SUCCESS - Operações bem-sucedidas (nível customizado do Loguru)
viu.success("Deployment completed",
    version="1.2.3",
    environment="production"
)
```

### 🔐 Produção com Autenticação SASL

```python
from viu_loguru import ViuLogger, TransportMode

viu = ViuLogger(config=ViuLoguruConfig(
    service_name="my-api",
    environment="production",
    transport_mode=TransportMode.KAFKA,
    kafka_brokers="viu-kafka.example.com:9092",
    kafka_topic="logs.production",
    kafka_username="viu_tenant123abc",
    kafka_password="your-secure-password",
    kafka_sasl_mechanism="SCRAM-SHA-256",
    kafka_security_protocol="SASL_SSL"
))
```

### 🌍 Configuração via Environment Variables

```bash
# Modo HTTP
export VIU_TRANSPORT_MODE=http
export VIU_SERVICE_NAME=my-api
export VIU_ENVIRONMENT=production
export VIU_API_URL=http://localhost:3000
export VIU_API_KEY=viu_live_xxx

# Modo Kafka
export VIU_TRANSPORT_MODE=kafka
export VIU_KAFKA_BROKERS=kafka.example.com:9092
export VIU_KAFKA_TOPIC=logs.production
export VIU_KAFKA_USERNAME=viu_tenant123abc
export VIU_KAFKA_PASSWORD=your-secure-password
```

```python
# Carrega automaticamente das variáveis de ambiente
from viu_loguru import ViuLogger, ViuLoguruConfig

config = ViuLoguruConfig.from_env()
viu = ViuLogger(config)
```

## 🔗 Rastreamento e Correlation IDs

O viu-loguru **gera automaticamente** IDs de rastreamento para todos os logs:

### IDs Gerados Automaticamente

```python
viu.info("User action", user_id="123")
# Gera automaticamente:
# - correlation_id: UUID único da requisição
# - trace_id: UUID para rastreamento distribuído
# - span_id: UUID (16 chars) para operações individuais
```

### Ordem de Prioridade para `span_id`

1. **Explícito no log**: Valor passado diretamente
2. **Contexto manual**: Definido via `viu_span_id_context.set()`
3. **Headers HTTP**: Extraído de `traceparent` ou `X-B3-SpanId`
4. **Auto-geração**: UUID gerado automaticamente (padrão)

### Definir Manualmente

```python
from viu_loguru.context import viu_span_id_context

# Definir span_id para o contexto atual
viu_span_id_context.set("custom-span-123")
viu.info("Operation with custom span")

# Ou passar diretamente no log
viu.info("Specific operation", span_id="operation-456")
```

### Distributed Tracing com Hierarquia

```python
from viu_loguru.context import create_child_span

# Operação pai
viu.info("Starting parent operation")

# Criar span filho (mantém hierarchia parent/child)
child_span = create_child_span()
viu.info("Child operation", **child_span)
# child_span contém: span_id, parent_span_id, correlation_id, trace_id
```

### Detecção Automática de Headers HTTP

```python
# Headers W3C Trace Context ou Zipkin B3 são detectados automaticamente
viu.set_trace_headers({
    'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
})
# Extrai automaticamente trace_id e span_id do header
```

**Compatibilidade**: W3C Trace Context, Zipkin B3, OpenTelemetry


### 🔄 Integração com FastAPI

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from viu_loguru import ViuLogger, TransportMode
from viu_loguru.context import viu_correlation_context

app = FastAPI()

# Middleware para correlation IDs
class ViuCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID")
        if correlation_id:
            token = viu_correlation_context.set(correlation_id)
        try:
            response = await call_next(request)
            return response
        finally:
            if correlation_id:
                viu_correlation_context.reset(token)

app.add_middleware(ViuCorrelationMiddleware)

# Logger
viu = ViuLogger(config=ViuLoguruConfig(
    service_name="my-api",
    transport_mode=TransportMode.HTTP,
    api_url="http://localhost:3000",
    api_key="viu_live_xxx"
))

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    viu.info("Fetching user", user_id=user_id)
    return {"user_id": user_id}
```

## ⚙️ Configuração

### Modo HTTP

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `VIU_TRANSPORT_MODE` | Modo de transporte | `http` |
| `VIU_SERVICE_NAME` | Nome do serviço | `unknown-service` |
| `VIU_ENVIRONMENT` | Ambiente | `development` |
| `VIU_API_URL` | URL da API | (obrigatório) |
| `VIU_API_KEY` | API Key | (obrigatório) |
| `VIU_HTTP_TIMEOUT` | Timeout (s) | `10` |

### Modo Kafka

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `VIU_TRANSPORT_MODE` | Modo de transporte | `http` |
| `VIU_SERVICE_NAME` | Nome do serviço | `unknown-service` |
| `VIU_ENVIRONMENT` | Ambiente | `development` |
| `VIU_KAFKA_BROKERS` | Endereço Kafka | `localhost:9092` |
| `VIU_KAFKA_TOPIC` | Topic Kafka | `logs.app.raw` |
| `VIU_KAFKA_USERNAME` | Username SASL | (opcional) |
| `VIU_KAFKA_PASSWORD` | Password SASL | (opcional) |
| `VIU_KAFKA_SASL_MECHANISM` | Mecanismo SASL | `SCRAM-SHA-256` |
| `VIU_KAFKA_SECURITY_PROTOCOL` | Protocolo | `SASL_SSL` |

## 📈 Performance

- **Modo HTTP**: Envio imediato com retry
- **Modo Kafka**: Batching (100 logs ou 128KB), compressão gzip
- **Circuit Breaker**: Evita sobrecarga em falhas
- **Async**: Não bloqueia sua aplicação

## 🔒 Segurança

- **Modo HTTP**: API Key no header Authorization
- **Modo Kafka**: SASL_SSL ativado por padrão
- TLS/SSL completo
- Autenticação: SCRAM-SHA-256, SCRAM-SHA-512, PLAIN

## 🆚 HTTP vs Kafka

| Aspecto | HTTP | Kafka |
|---------|------|-------|
| Complexidade | Baixa | Alta |
| Exposição Kafka | Não | Sim |
| Autenticação | API Key | SASL |
| Performance | Boa | Excelente |
| Recomendado | Padrão | Alta performance |

## 🤝 Contributing

Contribuições são bem-vindas!

## 📄 License

MIT License - see [LICENSE](LICENSE) para detalhes.

---

<div align="center">
  <sub>Built with ❤️ by @mar.jr</sub>
</div>
