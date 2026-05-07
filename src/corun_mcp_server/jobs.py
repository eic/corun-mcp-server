"""Job submission and polling helpers for the corun-ai REST API.

Provides functions to submit prompts, trigger generation jobs, query job
status, and poll until completion.  No MCP imports — functions are
independently testable.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from corun_mcp_server import client

# Terminal job states
_TERMINAL_STATES: frozenset[str] = frozenset({"completed", "failed", "aborted"})


async def get_job_status(job_id: str) -> dict[str, Any]:
    """Return the current status and result of a job.

    Parameters
    ----------
    job_id:
        The unique identifier of the job.

    Returns
    -------
    dict[str, Any]
        Job object with keys ``id``, ``status``, ``definition``,
        ``created_at``, ``modified_at``, and optionally
        ``result_page_group_id`` and ``error``.
    """
    return await client.get(f"/api/v1/jobs/{job_id}/")


async def submit_prompt(
    section_name: str,
    content: str,
    definition_id: str | None = None,
) -> dict[str, Any]:
    """Create a new prompt in a section without triggering generation.

    Parameters
    ----------
    section_name:
        The URL-friendly name of the target section.
    content:
        Prompt text content.
    definition_id:
        Optional job definition to associate with the prompt.

    Returns
    -------
    dict[str, Any]
        Created prompt with keys ``prompt_group_id``, ``version``, ``status``.
    """
    body: dict[str, Any] = {"section": section_name, "content": content}
    if definition_id is not None:
        body["definition_id"] = definition_id
    return await client.post("/api/v1/prompts/", body)


async def generate_from_prompt(
    prompt_group_id: str,
    definition_id: str | None = None,
) -> dict[str, Any]:
    """Trigger a generation job from an existing prompt.

    Parameters
    ----------
    prompt_group_id:
        The group identifier of the prompt to generate from.
    definition_id:
        Optional job definition override.

    Returns
    -------
    dict[str, Any]
        Created job with keys ``job_id``, ``status``.
    """
    body: dict[str, Any] = {"prompt_group_id": prompt_group_id}
    if definition_id is not None:
        body["definition_id"] = definition_id
    return await client.post("/api/v1/jobs/", body)


async def submit_and_generate(
    section_name: str,
    content: str,
    definition_id: str | None = None,
) -> dict[str, Any]:
    """Create a prompt and immediately trigger a generation job.

    Parameters
    ----------
    section_name:
        The URL-friendly name of the target section.
    content:
        Prompt text content.
    definition_id:
        Optional job definition to use.

    Returns
    -------
    dict[str, Any]
        Combined result with keys ``prompt_group_id``, ``job_id``, ``status``.
    """
    prompt = await submit_prompt(section_name, content, definition_id)
    prompt_group_id: str = prompt.get("prompt_group_id") or prompt.get("group_id", "")
    job = await generate_from_prompt(prompt_group_id, definition_id)
    return {
        "prompt_group_id": prompt_group_id,
        "job_id": job.get("job_id") or job.get("id", ""),
        "status": job.get("status", ""),
    }


async def wait_for_job(
    job_id: str,
    timeout_s: int | None = None,
    poll_interval: float | None = None,
) -> dict[str, Any]:
    """Poll a job until it reaches a terminal state.

    Parameters
    ----------
    job_id:
        The unique identifier of the job to poll.
    timeout_s:
        Maximum seconds to wait.  Defaults to ``CORUN_POLL_TIMEOUT``.
    poll_interval:
        Seconds between polls.  Defaults to ``CORUN_POLL_INTERVAL``.

    Returns
    -------
    dict[str, Any]
        Final job status with keys ``job_id``, ``status``,
        optionally ``result_page_group_id`` and ``content``.

    Raises
    ------
    TimeoutError
        When the job does not complete within *timeout_s* seconds.
    """
    from corun_mcp_server.client import CORUN_POLL_INTERVAL, CORUN_POLL_TIMEOUT

    effective_timeout = timeout_s if timeout_s is not None else CORUN_POLL_TIMEOUT
    effective_interval = poll_interval if poll_interval is not None else CORUN_POLL_INTERVAL

    deadline = time.monotonic() + effective_timeout

    while True:
        job = await get_job_status(job_id)
        status: str = job.get("status", "")
        if status in _TERMINAL_STATES:
            return {
                "job_id": job_id,
                "status": status,
                "result_page_group_id": job.get("result_page_group_id"),
            }
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Job {job_id!r} did not complete within {effective_timeout}s "
                f"(last status: {status!r})"
            )
        await asyncio.sleep(effective_interval)


async def abort_job(job_id: str) -> dict[str, Any]:
    """Cancel a running job.

    Parameters
    ----------
    job_id:
        The unique identifier of the job to abort.

    Returns
    -------
    dict[str, Any]
        Result with keys ``ok``, ``job_id``, ``status``.
    """
    result = await client.post(f"/api/v1/jobs/{job_id}/abort/", {})
    return {
        "ok": True,
        "job_id": job_id,
        "status": result.get("status", "aborted"),
    }
