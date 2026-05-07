"""corun MCP server.

Exposes corun-ai tools over the Model Context Protocol (MCP).  All tool
handlers are thin wrappers around :mod:`corun_mcp_server.resources` and
:mod:`corun_mcp_server.jobs`; exceptions are caught and returned as error
dicts rather than raised.

Run with::

    corun-mcp-server          # stdio transport (default)
    python -m corun_mcp_server.server
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from corun_mcp_server import jobs, resources

mcp = FastMCP("corun-mcp-server")

# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_sections() -> list[dict[str, Any]]:
    """Return all active documentation sections.

    Returns
    -------
    list[dict[str, Any]]
        List of section objects with keys ``id``, ``name``, ``title``,
        ``description``.  Returns ``[{"error": "..."}]`` on failure.
    """
    try:
        return await resources.list_sections()
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
async def get_section(section_name: str) -> dict[str, Any]:
    """Return a section and its current prompts.

    Parameters
    ----------
    section_name:
        The URL-friendly name of the section.

    Returns
    -------
    dict[str, Any]
        Section detail including a ``prompts`` list.  Returns
        ``{"error": "..."}`` on failure.
    """
    try:
        return await resources.get_section(section_name)
    except Exception as exc:
        return {"error": str(exc), "section_name": section_name}


@mcp.tool()
async def get_prompt(group_id: str) -> dict[str, Any]:
    """Return a specific prompt and any published pages derived from it.

    Parameters
    ----------
    group_id:
        The group identifier of the prompt.

    Returns
    -------
    dict[str, Any]
        Prompt detail.  Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await resources.get_prompt(group_id)
    except Exception as exc:
        return {"error": str(exc), "group_id": group_id}


@mcp.tool()
async def get_page(group_id: str) -> dict[str, Any]:
    """Return the full generated content of a page.

    Parameters
    ----------
    group_id:
        The group identifier of the page.

    Returns
    -------
    dict[str, Any]
        Page detail with rendered content.  Returns ``{"error": "..."}`` on
        failure.
    """
    try:
        return await resources.get_page(group_id)
    except Exception as exc:
        return {"error": str(exc), "group_id": group_id}


@mcp.tool()
async def list_job_definitions() -> list[dict[str, Any]]:
    """Return all active job definitions available for generation.

    Returns
    -------
    list[dict[str, Any]]
        List of job definition objects with keys ``id``, ``name``,
        ``description``, ``status``.  Returns ``[{"error": "..."}]`` on
        failure.
    """
    try:
        return await resources.list_job_definitions()
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
async def get_job_status(job_id: str) -> dict[str, Any]:
    """Return the current status and result of a generation job.

    Parameters
    ----------
    job_id:
        The unique identifier of the job.

    Returns
    -------
    dict[str, Any]
        Job status object.  Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await jobs.get_job_status(job_id)
    except Exception as exc:
        return {"error": str(exc), "job_id": job_id}


# ---------------------------------------------------------------------------
# Write tools
# ---------------------------------------------------------------------------


@mcp.tool()
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
        Created prompt info with ``prompt_group_id``, ``version``, ``status``.
        Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await jobs.submit_prompt(section_name, content, definition_id)
    except Exception as exc:
        return {"error": str(exc), "section_name": section_name}


@mcp.tool()
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
        Created job info with ``job_id``, ``status``.
        Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await jobs.generate_from_prompt(prompt_group_id, definition_id)
    except Exception as exc:
        return {"error": str(exc), "prompt_group_id": prompt_group_id}


@mcp.tool()
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
        Combined result with ``prompt_group_id``, ``job_id``, ``status``.
        Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await jobs.submit_and_generate(section_name, content, definition_id)
    except Exception as exc:
        return {"error": str(exc), "section_name": section_name}


@mcp.tool()
async def wait_for_job(
    job_id: str,
    timeout_s: int | None = None,
) -> dict[str, Any]:
    """Poll a job until it reaches a terminal state.

    This is a long-running tool that loops with asyncio.sleep between polls.

    Parameters
    ----------
    job_id:
        The unique identifier of the job to poll.
    timeout_s:
        Maximum seconds to wait.  Defaults to ``CORUN_POLL_TIMEOUT`` (3600).

    Returns
    -------
    dict[str, Any]
        Final job result with ``job_id``, ``status``, optionally
        ``result_page_group_id``.  Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await jobs.wait_for_job(job_id, timeout_s=timeout_s)
    except Exception as exc:
        return {"error": str(exc), "job_id": job_id}


@mcp.tool()
async def abort_job(job_id: str) -> dict[str, Any]:
    """Cancel a running generation job.

    Parameters
    ----------
    job_id:
        The unique identifier of the job to abort.

    Returns
    -------
    dict[str, Any]
        Result with ``ok``, ``job_id``, ``status``.
        Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await jobs.abort_job(job_id)
    except Exception as exc:
        return {"error": str(exc), "job_id": job_id}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
