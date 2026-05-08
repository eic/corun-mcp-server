# corun-mcp-server

`corun-mcp-server` is a standalone Python MCP server that gives external LLM clients
read and write access to a [corun-ai](https://github.com/BNLNPPS/corun-ai) instance.

## Features

- **Browse** documentation sections, prompts, and AI-generated pages.
- **Submit** new prompts and trigger generation jobs.
- **Poll** job status and retrieve generated pages once complete.
- **Token-based authentication** for secure machine-to-machine access.

## Installation

```bash
pip install corun-mcp-server
```

Or install from source:

```bash
git clone https://github.com/eic/corun-mcp-server
cd corun-mcp-server
pip install -e ".[dev]"
```

## Configuration

Set the following environment variables before starting the server:

| Variable | Description | Default |
|----------|-------------|---------|
| `CORUN_BASE_URL` | Base URL of the corun-ai instance | *(required)* |
| `CORUN_API_TOKEN` | API token for `Authorization: Token` authentication | *(required)* |
| `CORUN_POLL_INTERVAL` | Seconds between job status polls | `5` |
| `CORUN_POLL_TIMEOUT` | Maximum seconds to wait for job completion | `3600` |

A `.env` file in the current directory is automatically loaded (never commit this file).

## Usage

### stdio transport (default)

```bash
export CORUN_BASE_URL=https://epic-devcloud.org/doc
export CORUN_API_TOKEN=your-token
corun-mcp-server
```

### Claude Desktop

Add to `claude_desktop_config.json`:

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

## Available Tools

### Read Tools

| Tool | Description |
|------|-------------|
| `list_sections` | List all active documentation sections |
| `get_section` | Get a section and its current prompts |
| `get_prompt` | Get a specific prompt and published pages |
| `get_page` | Get the full generated content of a page |
| `list_job_definitions` | List available job definitions |
| `get_job_status` | Get the current status of a generation job |

### Write Tools

| Tool | Description |
|------|-------------|
| `submit_prompt` | Create a new prompt (no generation) |
| `generate_from_prompt` | Trigger a generation job from an existing prompt |
| `submit_and_generate` | Create a prompt and immediately trigger generation |
| `wait_for_job` | Poll until a job completes and return the result |
| `abort_job` | Cancel a running job |

## Development

```bash
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=corun_mcp_server --cov-report=term-missing

# Lint
ruff check src/ tests/
```

## License

MIT — see [LICENSE](LICENSE).
