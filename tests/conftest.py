"""Shared pytest fixtures and helpers for the corun-mcp-server test suite."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required environment variables for every test."""
    monkeypatch.setenv("CORUN_BASE_URL", "http://testserver")
    monkeypatch.setenv("CORUN_API_TOKEN", "test-token-abc")


@pytest.fixture(autouse=True)
def reset_shared_client() -> None:
    """Reset the module-level shared HTTP client between tests.

    This ensures that tests which remove env vars (to trigger EnvironmentError)
    don't leave a stale client that masks the error in subsequent tests.
    """
    import corun_mcp_server.client as c

    c._shared_client = None
