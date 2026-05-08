# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a Vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, report them privately via [GitHub Security Advisories](https://github.com/eic/corun-mcp-server/security/advisories/new)
or by emailing the maintainer directly.

We will respond within 72 hours.

## Security Notes

- **Never** hardcode `CORUN_API_TOKEN` in source code or commit it to version control.
- `CORUN_BASE_URL` and `CORUN_API_TOKEN` must be provided via environment variables or a
  `.env` file that is **excluded from version control** (added to `.gitignore`).
- This MCP server is **stateless** — it does not store tokens or session data between tool
  calls.
- API tokens should be treated as secrets with the same care as passwords.
- The corun-ai instance should enforce per-token rate limits to prevent runaway job
  submission.
- Use read-only tokens for clients that only need browsing capability.
