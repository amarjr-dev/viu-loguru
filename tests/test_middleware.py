"""
Tests for FastAPI/Starlette middleware
"""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

try:
    from viu_loguru.middleware import ViuCorrelationMiddleware

    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False


@pytest.mark.skipif(not MIDDLEWARE_AVAILABLE, reason="Starlette not installed")
class TestViuCorrelationMiddleware:
    def test_middleware_adds_correlation_id(self):
        """Test middleware adds correlation ID to request"""

        async def homepage(request):
            correlation_id = getattr(request.state, "correlation_id", None)
            return PlainTextResponse(f"correlation_id: {correlation_id}")

        app = Starlette(
            routes=[
                Route("/", homepage),
            ]
        )

        app.add_middleware(
            ViuCorrelationMiddleware, service_name="test-service", environment="test"
        )

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert "correlation_id:" in response.text
        assert response.headers.get("X-Correlation-ID") is not None

    def test_middleware_preserves_existing_correlation_id(self):
        """Test middleware preserves existing correlation ID from header"""

        async def homepage(request):
            correlation_id = getattr(request.state, "correlation_id", None)
            return PlainTextResponse(correlation_id)

        app = Starlette(
            routes=[
                Route("/", homepage),
            ]
        )

        app.add_middleware(ViuCorrelationMiddleware, service_name="test-service")

        client = TestClient(app)
        test_correlation_id = "test-123-456"
        response = client.get("/", headers={"X-Correlation-ID": test_correlation_id})

        assert response.status_code == 200
        assert response.text == test_correlation_id
        assert response.headers.get("X-Correlation-ID") == test_correlation_id
