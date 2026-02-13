"""
pytest configuration and fixtures
"""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_context():
    """Reset context variables after each test"""
    from viu_loguru.context import (
        viu_correlation_context,
        viu_span_id_context,
        viu_trace_id_context,
    )

    yield

    # Reset all contexts
    try:
        viu_correlation_context.set(None)
        viu_trace_id_context.set(None)
        viu_span_id_context.set(None)
    except:
        pass
