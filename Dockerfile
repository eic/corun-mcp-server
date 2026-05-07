# syntax=docker/dockerfile:1

# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir "." && \
    pip cache purge

# ---- Runtime stage ----
FROM python:3.12-slim

# Copy installed Python packages and entrypoint from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/corun-mcp-server /usr/local/bin/corun-mcp-server

# Use non-root user for security
RUN useradd -r -s /bin/false appuser

USER appuser

# Environment variables (must be overridden at runtime)
ENV CORUN_BASE_URL=""
ENV CORUN_API_TOKEN=""

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import corun_mcp_server" || exit 1

# Labels
LABEL org.opencontainers.image.title="corun MCP Server" \
      org.opencontainers.image.description="MCP server for corun-ai integration" \
      org.opencontainers.image.vendor="wdconinc" \
      org.opencontainers.image.source="https://github.com/wdconinc/corun-mcp-server" \
      org.opencontainers.image.licenses="MIT"

# Run the MCP server (stdio transport)
ENTRYPOINT ["corun-mcp-server"]
