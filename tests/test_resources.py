"""Unit tests for corun_mcp_server.resources."""

from __future__ import annotations

import httpx
import pytest
import respx

import corun_mcp_server.resources as res

# ---------------------------------------------------------------------------
# list_sections
# ---------------------------------------------------------------------------

SECTIONS_RESPONSE = [
    {"id": 1, "name": "intro", "title": "Introduction", "description": "Intro section"},
    {"id": 2, "name": "analysis", "title": "Analysis", "description": "Analysis section"},
]


@respx.mock
async def test_list_sections_returns_list() -> None:
    respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(200, json=SECTIONS_RESPONSE)
    )

    result = await res.list_sections()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "intro"


@respx.mock
async def test_list_sections_propagates_http_error() -> None:
    respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(500, text="Server error")
    )

    with pytest.raises(httpx.HTTPStatusError):
        await res.list_sections()


# ---------------------------------------------------------------------------
# get_section
# ---------------------------------------------------------------------------

SECTION_DETAIL = {
    "id": 1,
    "name": "intro",
    "title": "Introduction",
    "description": "Intro",
    "prompts": [
        {"group_id": "grp-1", "content": "Hello world", "status": "published", "version": 1}
    ],
}


@respx.mock
async def test_get_section_returns_detail() -> None:
    respx.get("http://testserver/api/v1/sections/intro/").mock(
        return_value=httpx.Response(200, json=SECTION_DETAIL)
    )

    result = await res.get_section("intro")
    assert result["name"] == "intro"
    assert len(result["prompts"]) == 1


@respx.mock
async def test_get_section_404_raises() -> None:
    respx.get("http://testserver/api/v1/sections/missing/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await res.get_section("missing")


# ---------------------------------------------------------------------------
# get_prompt
# ---------------------------------------------------------------------------

PROMPT_DETAIL = {
    "group_id": "grp-1",
    "version": 1,
    "content": "Hello world",
    "status": "published",
    "section": "intro",
    "pages": [{"group_id": "page-1", "status": "published", "created_at": "2024-01-01"}],
}


@respx.mock
async def test_get_prompt_returns_detail() -> None:
    respx.get("http://testserver/api/v1/prompts/grp-1/").mock(
        return_value=httpx.Response(200, json=PROMPT_DETAIL)
    )

    result = await res.get_prompt("grp-1")
    assert result["group_id"] == "grp-1"
    assert result["content"] == "Hello world"
    assert len(result["pages"]) == 1


@respx.mock
async def test_get_prompt_404_raises() -> None:
    respx.get("http://testserver/api/v1/prompts/nope/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await res.get_prompt("nope")


# ---------------------------------------------------------------------------
# get_page
# ---------------------------------------------------------------------------

PAGE_DETAIL = {
    "group_id": "page-1",
    "content": "# Hello\nSome content",
    "content_rendered": "<h1>Hello</h1><p>Some content</p>",
    "status": "published",
    "created_at": "2024-01-01T00:00:00Z",
    "data": {"generation_model": "gpt-4"},
}


@respx.mock
async def test_get_page_returns_detail() -> None:
    respx.get("http://testserver/api/v1/pages/page-1/").mock(
        return_value=httpx.Response(200, json=PAGE_DETAIL)
    )

    result = await res.get_page("page-1")
    assert result["group_id"] == "page-1"
    assert "content" in result
    assert result["data"]["generation_model"] == "gpt-4"


@respx.mock
async def test_get_page_404_raises() -> None:
    respx.get("http://testserver/api/v1/pages/missing/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await res.get_page("missing")


# ---------------------------------------------------------------------------
# list_job_definitions
# ---------------------------------------------------------------------------

DEFINITIONS_RESPONSE = [
    {"id": "def-1", "name": "default", "description": "Default generator", "status": "active"},
    {"id": "def-2", "name": "fast", "description": "Fast generator", "status": "active"},
]


@respx.mock
async def test_list_job_definitions_returns_list() -> None:
    respx.get("http://testserver/api/v1/definitions/").mock(
        return_value=httpx.Response(200, json=DEFINITIONS_RESPONSE)
    )

    result = await res.list_job_definitions()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "default"


@respx.mock
async def test_list_job_definitions_propagates_error() -> None:
    respx.get("http://testserver/api/v1/definitions/").mock(
        return_value=httpx.Response(403, json={"detail": "Forbidden"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await res.list_job_definitions()
