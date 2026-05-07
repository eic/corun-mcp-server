"""Read-only resource helpers for the corun-ai REST API.

Provides functions to list and retrieve documentation sections, prompts, and
generated pages.  No MCP imports — functions are independently testable.
"""

from __future__ import annotations

from typing import Any

from corun_mcp_server import client


async def list_sections() -> list[dict[str, Any]]:
    """Return all active documentation sections.

    Returns
    -------
    list[dict[str, Any]]
        List of section objects with keys ``id``, ``name``, ``title``,
        ``description``.
    """
    return await client.get("/api/v1/sections/")


async def get_section(section_name: str) -> dict[str, Any]:
    """Return a section and its current prompts.

    Parameters
    ----------
    section_name:
        The URL-friendly name of the section.

    Returns
    -------
    dict[str, Any]
        Section detail with nested ``prompts`` list containing
        ``group_id``, ``content``, ``status``, ``version``.
    """
    return await client.get(f"/api/v1/sections/{section_name}/")


async def get_prompt(group_id: str) -> dict[str, Any]:
    """Return a specific prompt and any published pages derived from it.

    Parameters
    ----------
    group_id:
        The group identifier of the prompt.

    Returns
    -------
    dict[str, Any]
        Prompt detail with keys ``group_id``, ``version``, ``content``,
        ``status``, ``section``, and ``pages``.
    """
    return await client.get(f"/api/v1/prompts/{group_id}/")


async def get_page(group_id: str) -> dict[str, Any]:
    """Return the full generated content of a page.

    Parameters
    ----------
    group_id:
        The group identifier of the page.

    Returns
    -------
    dict[str, Any]
        Page detail with keys ``group_id``, ``content``, ``content_rendered``,
        ``status``, ``created_at``, ``data``.
    """
    return await client.get(f"/api/v1/pages/{group_id}/")


async def list_job_definitions() -> list[dict[str, Any]]:
    """Return all active job definitions.

    Returns
    -------
    list[dict[str, Any]]
        List of job definition objects with keys ``id``, ``name``,
        ``description``, ``status``.
    """
    return await client.get("/api/v1/definitions/")
