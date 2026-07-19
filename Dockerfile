FROM python:3.12-slim

# Install system dependencies and Postgres client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install 'uv' for fast dependency management
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency definition
COPY pyproject.toml README.md ./

# Install dependencies into the system python environment
RUN uv pip install --system -e .

# Copy application source code
COPY . .

# The application communicates over stdio for MCP, so no EXPOSE is strictly needed.
# If you configure FastMCP for SSE later, you would EXPOSE that port here.

# Define the entrypoint to run the MCP server
ENTRYPOINT ["python", "-m", "expense_tracker.server"]
