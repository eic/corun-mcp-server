# AI Agent Instructions for corun MCP Server

This document provides guidance for AI agents (GitHub Copilot, Claude, ChatGPT, etc.)
working on this repository.

## Project Overview

**corun MCP Server** — A standalone Python MCP (Model Context Protocol) server that
gives external LLM clients — Claude Desktop, Cursor, VS Code Copilot Chat, etc. — read
and write access to a [corun-ai](https://github.com/BNLNPPS/corun-ai) instance.

- **Language**: Python (≥ 3.10)
- **MCP framework**: `mcp>=1.0.0` (FastMCP)
- **HTTP client**: `httpx>=0.27` (async)
- **Purpose**: Browse documentation sections, submit prompts, trigger generation jobs,
  and poll results from a corun-ai deployment.

## Architecture

```
src/corun_mcp_server/
├── __init__.py     # Package marker and version
├── client.py       # Async httpx client; auth header injection; base URL handling
├── resources.py    # Read-only helpers: sections, prompts, pages, definitions
├── jobs.py         # Write/poll helpers: submit_prompt, generate_from_prompt, wait_for_job
└── server.py       # FastMCP server; @mcp.tool() wrappers; main() entry point

tests/
├── __init__.py
├── conftest.py         # autouse env-var fixture (CORUN_BASE_URL, CORUN_API_TOKEN)
├── test_client.py      # Unit tests for client.py (respx mocks)
├── test_resources.py   # Unit tests for resources.py
├── test_jobs.py        # Unit tests for jobs.py including state-transition polling
└── test_server.py      # Integration-style tests for MCP tool wrappers
```

## Key Principles

### 1. Layer Separation

- **`client.py`**: Knows about `httpx`, env vars, auth headers, and base URL only.
  Raises `EnvironmentError` early if `CORUN_BASE_URL` or `CORUN_API_TOKEN` are missing.
- **`resources.py`**: Thin wrappers around `client.get()`; no MCP imports.
- **`jobs.py`**: Thin wrappers around `client.post()` and `client.get()`; handles async
  polling via `asyncio.sleep()`; no MCP imports.
- **`server.py`**: Thin MCP wrappers via `@mcp.tool()`; catches all exceptions and returns
  `{"error": str(exc), ...}` dicts instead of raising.

### 2. Configuration via Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORUN_BASE_URL` | Base URL of corun-ai (e.g. `https://epic-devcloud.org/doc`) | *(required)* |
| `CORUN_API_TOKEN` | API token (`Authorization: Token` scheme) | *(required)* |
| `CORUN_POLL_INTERVAL` | Seconds between job polls | `5` |
| `CORUN_POLL_TIMEOUT` | Max seconds to wait for a job | `3600` |

### 3. Error Handling in server.py

All `@mcp.tool()` handlers use a `try/except Exception` block and return an error dict:

```python
@mcp.tool()
async def my_tool(param: str) -> dict[str, Any]:
    try:
        return await resources.my_function(param)
    except Exception as exc:
        return {"error": str(exc), "param": param}
```

For list-returning tools, wrap in a list: `return [{"error": str(exc)}]`.

### 4. Python Best Practices

- `from __future__ import annotations` at top of every source file.
- Full type annotations on all public functions.
- NumPy-style docstrings with `Parameters` and `Returns` sections.
- Target Python 3.10+.

## Adding a New Tool

1. **Implement the function** in `resources.py` (read) or `jobs.py` (write/poll):

```python
async def my_new_function(param: str) -> dict[str, Any]:
    """Short description.

    Parameters
    ----------
    param:
        Description of param.

    Returns
    -------
    dict[str, Any]
        Description of returned keys.
    """
    return await client.get(f"/api/v1/endpoint/{param}/")
```

2. **Add the MCP tool** in `server.py`:

```python
@mcp.tool()
async def my_new_tool(param: str) -> dict[str, Any]:
    """Short description for the LLM.

    Parameters
    ----------
    param:
        Description.

    Returns
    -------
    dict[str, Any]
        Description. Returns ``{"error": "..."}`` on failure.
    """
    try:
        return await resources.my_new_function(param)
    except Exception as exc:
        return {"error": str(exc), "param": param}
```

3. **Add tests** in `tests/test_resources.py` (or `test_jobs.py`) and `tests/test_server.py`.
4. **Update** `README.md`.

## Common Tasks

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=corun_mcp_server --cov-report=term-missing
```

### Linting

```bash
ruff check src/ tests/
```

### Verifying a Tool Manually

```python
import asyncio, os
os.environ["CORUN_BASE_URL"] = "https://your-instance.example.org"
os.environ["CORUN_API_TOKEN"] = "your-token"

from corun_mcp_server import resources
result = asyncio.run(resources.list_sections())
print(result)
```

## MCP Client Configuration

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "corun": {
      "command": "corun-mcp-server",
      "env": {
        "CORUN_BASE_URL": "https://epic-devcloud.org/doc",
        "CORUN_API_TOKEN": "<your-token>"
      }
    }
  }
}
```

### Docker

```bash
docker run --rm -i \
  -e CORUN_BASE_URL=https://epic-devcloud.org/doc \
  -e CORUN_API_TOKEN=<your-token> \
  ghcr.io/eic/corun-mcp-server
```

## Resources

- **MCP Specification**: https://modelcontextprotocol.io/
- **FastMCP (Python SDK)**: https://github.com/modelcontextprotocol/python-sdk
- **httpx**: https://www.python-httpx.org/
- **respx (httpx mock)**: https://lundberg.github.io/respx/
- **corun-ai**: https://github.com/BNLNPPS/corun-ai
- **uproot-mcp-server (reference)**: https://github.com/eic/uproot-mcp-server

## Questions?

- **MCP protocol**: See `server.py` for existing patterns; check MCP SDK docs.
- **httpx usage**: See `client.py`; refer to httpx docs.
- **corun-ai API**: Refer to https://github.com/BNLNPPS/corun-ai REST API docs.

---

*Keep this document up-to-date as the project evolves.*
