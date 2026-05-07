"""Async HTTP client for the corun-ai REST API.

Reads connection parameters from environment variables and injects the bearer
token into every request.
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
CORUN_POLL_INTERVAL: float = float(os.environ.get("CORUN_POLL_INTERVAL", "5"))
CORUN_POLL_TIMEOUT: float = float(os.environ.get("CORUN_POLL_TIMEOUT", "3600"))


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
    EnvironmentError
        When required environment variables are missing.
    """
    async with _make_client() as client:
        response = await client.get(path, params=params or None)
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
    EnvironmentError
        When required environment variables are missing.
    """
    async with _make_client() as client:
        response = await client.post(path, json=body)
        response.raise_for_status()
        return response.json()
