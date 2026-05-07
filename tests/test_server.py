"""Integration-style tests for the MCP server tool wrappers.

Each test calls the async tool function directly and verifies correct
delegation and error-dict returns.
"""

from __future__ import annotations

import httpx
import respx

import corun_mcp_server.server as srv

# ---------------------------------------------------------------------------
# list_sections
# ---------------------------------------------------------------------------

SECTIONS = [{"id": 1, "name": "intro", "title": "Introduction", "description": ""}]


@respx.mock
async def test_list_sections_success() -> None:
    respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(200, json=SECTIONS)
    )

    result = await srv.list_sections()
    assert isinstance(result, list)
    assert result[0]["name"] == "intro"


@respx.mock
async def test_list_sections_error_dict() -> None:
    respx.get("http://testserver/api/v1/sections/").mock(
        return_value=httpx.Response(500, text="error")
    )

    result = await srv.list_sections()
    assert isinstance(result, list)
    assert "error" in result[0]


# ---------------------------------------------------------------------------
# get_section
# ---------------------------------------------------------------------------

SECTION_DETAIL = {
    "id": 1,
    "name": "intro",
    "title": "Introduction",
    "description": "",
    "prompts": [],
}


@respx.mock
async def test_get_section_success() -> None:
    respx.get("http://testserver/api/v1/sections/intro/").mock(
        return_value=httpx.Response(200, json=SECTION_DETAIL)
    )

    result = await srv.get_section("intro")
    assert result["name"] == "intro"


@respx.mock
async def test_get_section_error_dict() -> None:
    respx.get("http://testserver/api/v1/sections/bad/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    result = await srv.get_section("bad")
    assert "error" in result
    assert result["section_name"] == "bad"


# ---------------------------------------------------------------------------
# get_prompt
# ---------------------------------------------------------------------------

PROMPT_DETAIL = {
    "group_id": "grp-1",
    "version": 1,
    "content": "Hello",
    "status": "published",
    "section": "intro",
    "pages": [],
}


@respx.mock
async def test_get_prompt_success() -> None:
    respx.get("http://testserver/api/v1/prompts/grp-1/").mock(
        return_value=httpx.Response(200, json=PROMPT_DETAIL)
    )

    result = await srv.get_prompt("grp-1")
    assert result["group_id"] == "grp-1"


@respx.mock
async def test_get_prompt_error_dict() -> None:
    respx.get("http://testserver/api/v1/prompts/bad/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    result = await srv.get_prompt("bad")
    assert "error" in result
    assert result["group_id"] == "bad"


# ---------------------------------------------------------------------------
# get_page
# ---------------------------------------------------------------------------

PAGE_DETAIL = {
    "group_id": "page-1",
    "content": "# Hello",
    "content_rendered": "<h1>Hello</h1>",
    "status": "published",
    "created_at": "2024-01-01T00:00:00Z",
    "data": {},
}


@respx.mock
async def test_get_page_success() -> None:
    respx.get("http://testserver/api/v1/pages/page-1/").mock(
        return_value=httpx.Response(200, json=PAGE_DETAIL)
    )

    result = await srv.get_page("page-1")
    assert result["group_id"] == "page-1"


@respx.mock
async def test_get_page_error_dict() -> None:
    respx.get("http://testserver/api/v1/pages/bad/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    result = await srv.get_page("bad")
    assert "error" in result
    assert result["group_id"] == "bad"


# ---------------------------------------------------------------------------
# list_job_definitions
# ---------------------------------------------------------------------------

DEFINITIONS = [{"id": "def-1", "name": "default", "description": "", "status": "active"}]


@respx.mock
async def test_list_job_definitions_success() -> None:
    respx.get("http://testserver/api/v1/definitions/").mock(
        return_value=httpx.Response(200, json=DEFINITIONS)
    )

    result = await srv.list_job_definitions()
    assert isinstance(result, list)
    assert result[0]["name"] == "default"


@respx.mock
async def test_list_job_definitions_error_dict() -> None:
    respx.get("http://testserver/api/v1/definitions/").mock(
        return_value=httpx.Response(500, text="error")
    )

    result = await srv.list_job_definitions()
    assert "error" in result[0]


# ---------------------------------------------------------------------------
# get_job_status
# ---------------------------------------------------------------------------

JOB_STATUS = {
    "id": "job-1",
    "status": "running",
    "definition": "def-1",
    "created_at": "2024-01-01T00:00:00Z",
    "modified_at": "2024-01-01T00:00:05Z",
}


@respx.mock
async def test_get_job_status_success() -> None:
    respx.get("http://testserver/api/v1/jobs/job-1/").mock(
        return_value=httpx.Response(200, json=JOB_STATUS)
    )

    result = await srv.get_job_status("job-1")
    assert result["status"] == "running"


@respx.mock
async def test_get_job_status_error_dict() -> None:
    respx.get("http://testserver/api/v1/jobs/bad/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    result = await srv.get_job_status("bad")
    assert "error" in result
    assert result["job_id"] == "bad"


# ---------------------------------------------------------------------------
# submit_prompt
# ---------------------------------------------------------------------------

PROMPT_CREATED = {"prompt_group_id": "grp-new", "version": 1, "status": "draft"}


@respx.mock
async def test_submit_prompt_success() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(201, json=PROMPT_CREATED)
    )

    result = await srv.submit_prompt("intro", "Hello world")
    assert result["prompt_group_id"] == "grp-new"


@respx.mock
async def test_submit_prompt_error_dict() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(400, json={"detail": "Bad"})
    )

    result = await srv.submit_prompt("intro", "Hello")
    assert "error" in result
    assert result["section_name"] == "intro"


# ---------------------------------------------------------------------------
# generate_from_prompt
# ---------------------------------------------------------------------------

JOB_CREATED = {"job_id": "job-new", "status": "queued"}


@respx.mock
async def test_generate_from_prompt_success() -> None:
    respx.post("http://testserver/api/v1/jobs/").mock(
        return_value=httpx.Response(201, json=JOB_CREATED)
    )

    result = await srv.generate_from_prompt("grp-1")
    assert result["job_id"] == "job-new"


@respx.mock
async def test_generate_from_prompt_error_dict() -> None:
    respx.post("http://testserver/api/v1/jobs/").mock(
        return_value=httpx.Response(400, json={"detail": "Bad"})
    )

    result = await srv.generate_from_prompt("grp-1")
    assert "error" in result
    assert result["prompt_group_id"] == "grp-1"


# ---------------------------------------------------------------------------
# submit_and_generate
# ---------------------------------------------------------------------------


@respx.mock
async def test_submit_and_generate_success() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(201, json=PROMPT_CREATED)
    )
    respx.post("http://testserver/api/v1/jobs/").mock(
        return_value=httpx.Response(201, json=JOB_CREATED)
    )

    result = await srv.submit_and_generate("intro", "Hello world")
    assert result["prompt_group_id"] == "grp-new"
    assert result["job_id"] == "job-new"


@respx.mock
async def test_submit_and_generate_error_dict() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(500, text="error")
    )

    result = await srv.submit_and_generate("intro", "Hello")
    assert "error" in result
    assert result["section_name"] == "intro"


# ---------------------------------------------------------------------------
# wait_for_job
# ---------------------------------------------------------------------------

JOB_COMPLETED = {
    "id": "job-1",
    "status": "completed",
    "definition": "def-1",
    "created_at": "2024-01-01T00:00:00Z",
    "modified_at": "2024-01-01T00:01:00Z",
    "result_page_group_id": "page-1",
}


@respx.mock
async def test_wait_for_job_success() -> None:
    respx.get("http://testserver/api/v1/jobs/job-1/").mock(
        return_value=httpx.Response(200, json=JOB_COMPLETED)
    )

    result = await srv.wait_for_job("job-1", timeout_s=10)
    assert result["status"] == "completed"
    assert result["result_page_group_id"] == "page-1"


@respx.mock
async def test_wait_for_job_timeout_error_dict() -> None:
    respx.get("http://testserver/api/v1/jobs/slow/").mock(
        return_value=httpx.Response(200, json={"id": "slow", "status": "running"})
    )

    result = await srv.wait_for_job("slow", timeout_s=0)
    assert "error" in result
    assert result["job_id"] == "slow"


# ---------------------------------------------------------------------------
# abort_job
# ---------------------------------------------------------------------------


@respx.mock
async def test_abort_job_success() -> None:
    respx.post("http://testserver/api/v1/jobs/job-1/abort/").mock(
        return_value=httpx.Response(200, json={"status": "aborted"})
    )

    result = await srv.abort_job("job-1")
    assert result["ok"] is True
    assert result["job_id"] == "job-1"


@respx.mock
async def test_abort_job_error_dict() -> None:
    respx.post("http://testserver/api/v1/jobs/bad/abort/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    result = await srv.abort_job("bad")
    assert "error" in result
    assert result["job_id"] == "bad"
