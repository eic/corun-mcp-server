"""Unit tests for corun_mcp_server.client."""

from __future__ import annotations

import httpx
import pytest
import respx


@pytest.fixture()
def reload_client(monkeypatch: pytest.MonkeyPatch):
    """Return a helper that reloads the client module after env changes."""
    import importlib

    import corun_mcp_server.client as mod

    def _reload():
        importlib.reload(mod)
        return mod

    return _reload


# ---------------------------------------------------------------------------
# _require_env
# ---------------------------------------------------------------------------


def test_require_env_raises_when_base_url_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORUN_BASE_URL", raising=False)
    import corun_mcp_server.client as c

    with pytest.raises(EnvironmentError, match="CORUN_BASE_URL"):
        c._require_env()


def test_require_env_raises_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORUN_API_TOKEN", raising=False)
    import corun_mcp_server.client as c

    with pytest.raises(EnvironmentError, match="CORUN_API_TOKEN"):
        c._require_env()


def test_require_env_passes_when_both_set() -> None:
    import corun_mcp_server.client as c

    c._require_env()  # Should not raise


# ---------------------------------------------------------------------------
# _make_client
# ---------------------------------------------------------------------------


def test_make_client_sets_auth_header() -> None:
    import corun_mcp_server.client as c

    http_client = c._make_client()
    auth_header = http_client.headers.get("authorization")
    assert auth_header == "Token test-token-abc"


def test_make_client_sets_base_url() -> None:
    import corun_mcp_server.client as c

    http_client = c._make_client()
    assert "testserver" in str(http_client.base_url)


# ---------------------------------------------------------------------------
# get()
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_returns_json() -> None:
    respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "intro"}])
    )

    import corun_mcp_server.client as c

    result = await c.get("/api/v1/sections/")
    assert result == [{"id": 1, "name": "intro"}]


@respx.mock
async def test_get_sends_auth_header() -> None:
    route = respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(200, json=[])
    )

    import corun_mcp_server.client as c

    await c.get("/api/v1/sections/")
    assert route.called
    request = route.calls[0].request
    assert request.headers["authorization"] == "Token test-token-abc"


@respx.mock
async def test_get_raises_on_404() -> None:
    respx.get("http://testserver/api/v1/sections/missing/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    import corun_mcp_server.client as c

    with pytest.raises(httpx.HTTPStatusError):
        await c.get("/api/v1/sections/missing/")


@respx.mock
async def test_get_raises_on_500() -> None:
    respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    import corun_mcp_server.client as c

    with pytest.raises(httpx.HTTPStatusError):
        await c.get("/api/v1/sections/")


@respx.mock
async def test_get_passes_query_params() -> None:
    route = respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(200, json=[])
    )

    import corun_mcp_server.client as c

    await c.get("/api/v1/sections/", page=2)
    request = route.calls[0].request
    assert b"page=2" in request.url.query


# ---------------------------------------------------------------------------
# post()
# ---------------------------------------------------------------------------


@respx.mock
async def test_post_returns_json() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(
            201, json={"prompt_group_id": "grp-1", "version": 1, "status": "draft"}
        )
    )

    import corun_mcp_server.client as c

    result = await c.post("/api/v1/prompts/", {"section": "intro", "content": "Hello"})
    assert result["prompt_group_id"] == "grp-1"


@respx.mock
async def test_post_sends_json_body() -> None:
    route = respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(201, json={"prompt_group_id": "grp-1"})
    )

    import corun_mcp_server.client as c

    await c.post("/api/v1/prompts/", {"section": "intro", "content": "Hello"})
    request = route.calls[0].request
    assert b"intro" in request.content


@respx.mock
async def test_post_raises_on_400() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(400, json={"detail": "Bad request"})
    )

    import corun_mcp_server.client as c

    with pytest.raises(httpx.HTTPStatusError):
        await c.post("/api/v1/prompts/", {})


# ---------------------------------------------------------------------------
# Missing env at call time
# ---------------------------------------------------------------------------


async def test_get_raises_env_error_when_base_url_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CORUN_BASE_URL", raising=False)

    import corun_mcp_server.client as c

    with pytest.raises(EnvironmentError):
        await c.get("/api/v1/sections/")


async def test_post_raises_env_error_when_token_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CORUN_API_TOKEN", raising=False)

    import corun_mcp_server.client as c

    with pytest.raises(EnvironmentError):
        await c.post("/api/v1/prompts/", {})
