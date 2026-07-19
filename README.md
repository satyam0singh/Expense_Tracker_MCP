# Expense Tracker MCP Server

A production-grade Model Context Protocol (MCP) server for comprehensive personal finance management. This server allows AI agents (like Claude or Gemini) to securely interact with your expenses, budgets, credit cards, and generate rich financial reports.

## Features

- **Clean Architecture**: Built on a solid Service/Repository pattern.
- **Asynchronous**: Fully async Python implementation utilizing `asyncio` and `asyncpg`.
- **Database**: PostgreSQL with SQLAlchemy 2.0 and Alembic for robust schema migrations.
- **Data Validation**: Strict schemas powered by Pydantic v2.
- **MCP Protocol**: Exposes tools dynamically using `FastMCP`.
- **Audit Trails**: Immutable JSONB audit logs for all mutations to track financial changes accurately.
- **Export Capabilities**: Generates Excel (`.xlsx`) and PDF reports.

## System Requirements

- Python 3.12+
- PostgreSQL 16+
- [uv](https://docs.astral.sh/uv/) (Recommended for fast dependency management)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/satyam0singh/Expense_Tracker_MCP.git
   cd Expense_Tracker_MCP
   ```

2. **Set up the environment:**
   Create a virtual environment and install dependencies.
   ```bash
   uv venv
   uv pip install -e .
   ```

3. **Configure Database:**
   Ensure PostgreSQL is running. Create a `.env` file from the provided `.env.docker` or `.env.example`:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/expense_db
   ```

4. **Run Migrations:**
   ```bash
   uv run alembic upgrade head
   ```

## Usage

### Standalone (Development / Local MCP)

To start the server communicating via `stdio` (Standard MCP client integration mode):

```bash
uv run python -m expense_tracker.server
```

You can configure an MCP client (e.g., Claude Desktop) with this command.

### Docker (Production)

To spin up the server and a PostgreSQL instance using Docker Compose:

```bash
docker-compose up -d
```

*Note: The `mcp-server` container in compose is primarily set up to tail logs or run migrations. To connect an AI agent to a dockerized MCP server, you typically pipe `stdio` through `docker run -i`.*

## Testing

Tests are written using `pytest` and use an in-memory SQLite database for rapid execution.

```bash
uv run pytest tests
```

## Architecture

This project strictly follows layered **Clean Architecture**:

- **Tools (`expense_tracker/tools/`)**: The presentation layer defining MCP endpoints using FastMCP.
- **Services (`expense_tracker/services/`)**: Orchestrates business logic across repositories (e.g., syncing budget when an expense is added).
- **Repositories (`expense_tracker/repositories/`)**: Abstract data access and domain queries.
- **Models (`expense_tracker/database/models/`)**: SQLAlchemy 2.0 ORM definitions.
- **Schemas (`expense_tracker/schemas/`)**: Pydantic v2 schemas for strict I/O validation.

## License

MIT License
