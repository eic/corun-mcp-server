"""Unit tests for corun_mcp_server.jobs."""

from __future__ import annotations

import httpx
import pytest
import respx

import corun_mcp_server.jobs as job_mod

# ---------------------------------------------------------------------------
# get_job_status
# ---------------------------------------------------------------------------

JOB_RUNNING = {
    "id": "job-1",
    "status": "running",
    "definition": "def-1",
    "created_at": "2024-01-01T00:00:00Z",
    "modified_at": "2024-01-01T00:00:05Z",
}

JOB_COMPLETED = {
    "id": "job-1",
    "status": "completed",
    "definition": "def-1",
    "created_at": "2024-01-01T00:00:00Z",
    "modified_at": "2024-01-01T00:01:00Z",
    "result_page_group_id": "page-1",
}


@respx.mock
async def test_get_job_status_returns_dict() -> None:
    respx.get("http://testserver/api/v1/jobs/job-1/").mock(
        return_value=httpx.Response(200, json=JOB_RUNNING)
    )

    result = await job_mod.get_job_status("job-1")
    assert result["id"] == "job-1"
    assert result["status"] == "running"


@respx.mock
async def test_get_job_status_404_raises() -> None:
    respx.get("http://testserver/api/v1/jobs/nope/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await job_mod.get_job_status("nope")


# ---------------------------------------------------------------------------
# submit_prompt
# ---------------------------------------------------------------------------

PROMPT_CREATED = {"prompt_group_id": "grp-new", "version": 1, "status": "draft"}


@respx.mock
async def test_submit_prompt_without_definition() -> None:
    route = respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(201, json=PROMPT_CREATED)
    )

    result = await job_mod.submit_prompt("intro", "Hello world")
    assert result["prompt_group_id"] == "grp-new"
    assert b"definition_id" not in route.calls[0].request.content


@respx.mock
async def test_submit_prompt_with_definition() -> None:
    route = respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(201, json=PROMPT_CREATED)
    )

    await job_mod.submit_prompt("intro", "Hello world", definition_id="def-1")
    assert b"def-1" in route.calls[0].request.content


@respx.mock
async def test_submit_prompt_400_raises() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(400, json={"detail": "Bad request"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await job_mod.submit_prompt("intro", "Hello")


# ---------------------------------------------------------------------------
# generate_from_prompt
# ---------------------------------------------------------------------------

JOB_CREATED = {"job_id": "job-new", "status": "queued"}


@respx.mock
async def test_generate_from_prompt_without_definition() -> None:
    route = respx.post("http://testserver/api/v1/jobs/").mock(
        return_value=httpx.Response(201, json=JOB_CREATED)
    )

    result = await job_mod.generate_from_prompt("grp-1")
    assert result["job_id"] == "job-new"
    assert b"definition_id" not in route.calls[0].request.content


@respx.mock
async def test_generate_from_prompt_with_definition() -> None:
    route = respx.post("http://testserver/api/v1/jobs/").mock(
        return_value=httpx.Response(201, json=JOB_CREATED)
    )

    await job_mod.generate_from_prompt("grp-1", definition_id="def-1")
    assert b"def-1" in route.calls[0].request.content


# ---------------------------------------------------------------------------
# submit_and_generate
# ---------------------------------------------------------------------------


@respx.mock
async def test_submit_and_generate_returns_combined_result() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(201, json=PROMPT_CREATED)
    )
    respx.post("http://testserver/api/v1/jobs/").mock(
        return_value=httpx.Response(201, json=JOB_CREATED)
    )

    result = await job_mod.submit_and_generate("intro", "Hello world")
    assert result["prompt_group_id"] == "grp-new"
    assert result["job_id"] == "job-new"
    assert result["status"] == "queued"


@respx.mock
async def test_submit_and_generate_raises_on_missing_prompt_id() -> None:
    """Prompt API returns a response without a recognisable group-id field."""
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(201, json={"version": 1, "status": "draft"})
    )

    with pytest.raises(ValueError, match="prompt_group_id"):
        await job_mod.submit_and_generate("intro", "Hello world")


@respx.mock
async def test_submit_and_generate_propagates_prompt_error() -> None:
    respx.post("http://testserver/api/v1/prompts/").mock(
        return_value=httpx.Response(400, json={"detail": "Bad request"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await job_mod.submit_and_generate("intro", "Hello")


# ---------------------------------------------------------------------------
# wait_for_job — immediate completion
# ---------------------------------------------------------------------------


@respx.mock
async def test_wait_for_job_already_completed() -> None:
    respx.get("http://testserver/api/v1/jobs/job-1/").mock(
        return_value=httpx.Response(200, json=JOB_COMPLETED)
    )

    result = await job_mod.wait_for_job("job-1", timeout_s=10, poll_interval=0.01)
    assert result["status"] == "completed"
    assert result["result_page_group_id"] == "page-1"


@respx.mock
async def test_wait_for_job_failed_terminal_state() -> None:
    respx.get("http://testserver/api/v1/jobs/job-fail/").mock(
        return_value=httpx.Response(
            200,
            json={"id": "job-fail", "status": "failed", "error": "Out of tokens"},
        )
    )

    result = await job_mod.wait_for_job("job-fail", timeout_s=10, poll_interval=0.01)
    assert result["status"] == "failed"


@respx.mock
async def test_wait_for_job_aborted_terminal_state() -> None:
    respx.get("http://testserver/api/v1/jobs/job-abort/").mock(
        return_value=httpx.Response(200, json={"id": "job-abort", "status": "aborted"})
    )

    result = await job_mod.wait_for_job("job-abort", timeout_s=10, poll_interval=0.01)
    assert result["status"] == "aborted"


# ---------------------------------------------------------------------------
# wait_for_job — state transition (queued → running → completed)
# ---------------------------------------------------------------------------


@respx.mock
async def test_wait_for_job_polls_until_complete() -> None:
    responses = [
        httpx.Response(200, json={"id": "job-2", "status": "queued"}),
        httpx.Response(200, json={"id": "job-2", "status": "running"}),
        httpx.Response(
            200,
            json={"id": "job-2", "status": "completed", "result_page_group_id": "page-2"},
        ),
    ]
    respx.get("http://testserver/api/v1/jobs/job-2/").mock(side_effect=responses)

    result = await job_mod.wait_for_job("job-2", timeout_s=30, poll_interval=0.01)
    assert result["status"] == "completed"
    assert result["result_page_group_id"] == "page-2"


# ---------------------------------------------------------------------------
# wait_for_job — timeout
# ---------------------------------------------------------------------------


@respx.mock
async def test_wait_for_job_raises_timeout() -> None:
    respx.get("http://testserver/api/v1/jobs/job-slow/").mock(
        return_value=httpx.Response(200, json={"id": "job-slow", "status": "running"})
    )

    with pytest.raises(TimeoutError, match="job-slow"):
        await job_mod.wait_for_job("job-slow", timeout_s=0, poll_interval=0.01)


# ---------------------------------------------------------------------------
# abort_job
# ---------------------------------------------------------------------------


@respx.mock
async def test_abort_job_returns_ok() -> None:
    respx.post("http://testserver/api/v1/jobs/job-1/abort/").mock(
        return_value=httpx.Response(200, json={"status": "aborted"})
    )

    result = await job_mod.abort_job("job-1")
    assert result["ok"] is True
    assert result["job_id"] == "job-1"
    assert result["status"] == "aborted"


@respx.mock
async def test_abort_job_404_raises() -> None:
    respx.post("http://testserver/api/v1/jobs/nope/abort/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await job_mod.abort_job("nope")
