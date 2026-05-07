"""Shared pytest fixtures and helpers for the corun-mcp-server test suite."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required environment variables for every test."""
    monkeypatch.setenv("CORUN_BASE_URL", "http://testserver")
    monkeypatch.setenv("CORUN_API_TOKEN", "test-token-abc")
