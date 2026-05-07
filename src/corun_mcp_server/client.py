"""Async HTTP client for the corun-ai REST API.

Reads connection parameters from environment variables and injects a
Django REST Framework token into every request via the
``Authorization: Token <token>`` header.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CORUN_BASE_URL: str = os.environ.get("CORUN_BASE_URL", "")
CORUN_API_TOKEN: str = os.environ.get("CORUN_API_TOKEN", "")

# CORUN_POLL_INTERVAL and CORUN_POLL_TIMEOUT are read lazily via poll_interval()
# and poll_timeout() to avoid a crash at import time when the env vars contain
# non-numeric values.


def poll_interval() -> float:
    """Return the configured poll interval in seconds.

    Returns
    -------
    float
        Value of ``CORUN_POLL_INTERVAL`` env var (default: ``5``).

    Raises
    ------
    OSError
        When the env var contains a non-numeric value.
    """
    raw = os.environ.get("CORUN_POLL_INTERVAL", "5")
    try:
        return float(raw)
    except ValueError:
        raise OSError(f"CORUN_POLL_INTERVAL must be a number, got {raw!r}")


def poll_timeout() -> float:
    """Return the configured poll timeout in seconds.

    Returns
    -------
    float
        Value of ``CORUN_POLL_TIMEOUT`` env var (default: ``3600``).

    Raises
    ------
    OSError
        When the env var contains a non-numeric value.
    """
    raw = os.environ.get("CORUN_POLL_TIMEOUT", "3600")
    try:
        return float(raw)
    except ValueError:
        raise OSError(f"CORUN_POLL_TIMEOUT must be a number, got {raw!r}")


def _require_env() -> None:
    """Raise EnvironmentError if required variables are missing.

    Raises
    ------
    EnvironmentError
        When CORUN_BASE_URL or CORUN_API_TOKEN are not set.
    """
    missing = [v for v in ("CORUN_BASE_URL", "CORUN_API_TOKEN") if not os.environ.get(v)]
    if missing:
        raise OSError(
            f"Required environment variable(s) not set: {', '.join(missing)}"
        )


def _make_client() -> httpx.AsyncClient:
    """Create a configured :class:`httpx.AsyncClient`.

    Returns
    -------
    httpx.AsyncClient
        Client pre-configured with base URL and Authorization header.

    Raises
    ------
    EnvironmentError
        When CORUN_BASE_URL or CORUN_API_TOKEN are not set.
    """
    _require_env()
    base_url = os.environ["CORUN_BASE_URL"].rstrip("/")
    token = os.environ["CORUN_API_TOKEN"]
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Token {token}"},
        timeout=30.0,
    )


# ---------------------------------------------------------------------------
# Shared client (one per process for connection pooling)
# ---------------------------------------------------------------------------

_shared_client: httpx.AsyncClient | None = None


def _get_shared_client() -> httpx.AsyncClient:
    """Return the process-level shared client, creating it on first call.

    Reusing a single :class:`httpx.AsyncClient` across requests enables HTTP
    connection pooling, which reduces latency for frequent tool calls such as
    job-status polling.

    Returns
    -------
    httpx.AsyncClient
        Shared client instance.

    Raises
    ------
    OSError
        When required environment variables are missing.
    """
    global _shared_client
    _require_env()
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = _make_client()
    return _shared_client


async def get(path: str, **params: Any) -> Any:
    """Perform a GET request to the corun-ai API.

    Parameters
    ----------
    path:
        API path relative to the base URL (e.g. ``/api/v1/sections/``).
    **params:
        Optional query parameters forwarded to httpx.

    Returns
    -------
    Any
        Parsed JSON response body.

    Raises
    ------
    httpx.HTTPStatusError
        On 4xx or 5xx responses.
    OSError
        When required environment variables are missing.
    """
    http_client = _get_shared_client()
    response = await http_client.get(path, params=params or None)
    response.raise_for_status()
    return response.json()


async def post(path: str, body: dict[str, Any]) -> Any:
    """Perform a POST request to the corun-ai API.

    Parameters
    ----------
    path:
        API path relative to the base URL.
    body:
        JSON-serialisable request body.

    Returns
    -------
    Any
        Parsed JSON response body.

    Raises
    ------
    httpx.HTTPStatusError
        On 4xx or 5xx responses.
    OSError
        When required environment variables are missing.
    """
    http_client = _get_shared_client()
    response = await http_client.post(path, json=body)
    response.raise_for_status()
    return response.json()
