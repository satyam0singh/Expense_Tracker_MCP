# instruction.md

# Expense Tracker MCP -- Migration & Expansion Instructions

## Role

You are an expert Staff Software Engineer and AI Architect.

Your task is to transform the provided SQLite-based Expense Tracker MCP
server into a **production-grade, enterprise-quality Expense Tracker
platform**.

Do NOT incrementally modify the existing project.

Instead:

-   Preserve the existing business logic where appropriate.
-   Redesign the architecture.
-   Produce clean, modular, maintainable code.
-   Follow modern backend engineering best practices.
-   Build as if this project will be deployed to production.

------------------------------------------------------------------------

# Primary Objective

Transform the current prototype into a complete project matching the
specification in **project.md**.

The final codebase must be suitable for:

-   Portfolio
-   Production deployment
-   Future SaaS conversion
-   Multi-user support
-   AI Agent integration
-   MCP ecosystem

------------------------------------------------------------------------

# Current Project

The current project contains:

-   FastMCP server
-   SQLite database
-   Single file implementation
-   Basic CRUD
-   JSON categories

Treat this as a prototype only.

------------------------------------------------------------------------

# Required Architecture

Use Clean Architecture.

``` text
expense_tracker/

server.py

database/
    db.py
    session.py
    base.py
    models.py
    migrations/

repositories/
services/
tools/
schemas/
core/
config/
utils/
tests/
```

Business logic must NEVER exist inside MCP tool functions.

Tools call Services.

Services call Repositories.

Repositories interact with SQLAlchemy.

------------------------------------------------------------------------

# Database

Replace SQLite completely.

Use:

-   PostgreSQL
-   SQLAlchemy 2.x ORM
-   Alembic migrations
-   psycopg

Do NOT use raw SQL except where unavoidable.

Use ORM models.

------------------------------------------------------------------------

# Models

Create models for:

-   User
-   Expense
-   Category
-   Budget
-   CreditCard
-   ExpenseAttachment
-   AuditLog

Use:

-   UUID primary keys
-   created_at
-   updated_at
-   soft delete support

------------------------------------------------------------------------

# Validation

Use Pydantic models for:

-   Request schemas
-   Response schemas

Validate:

-   Amount \> 0
-   Valid category
-   Valid dates
-   Required fields

------------------------------------------------------------------------

# MCP Tools

Implement tools including (but not limited to):

Expense: - add_expense - edit_expense - delete_expense -
restore_expense - list_expenses - search_expenses - get_expense

Analytics: - daily_summary - weekly_summary - monthly_summary -
yearly_summary - category_summary - spending_trends - highest_expense -
average_expense

Budget: - create_budget - update_budget - remaining_budget -
budget_status

Credit: - add_credit_card - update_credit_usage - credit_summary -
upcoming_due_dates

Reports: - export_csv - export_excel - export_pdf

Utilities: - import_categories - health_check

------------------------------------------------------------------------

# AI Features

Design the architecture so the following can be added later:

-   Receipt OCR
-   Voice expense entry
-   AI categorization
-   Spending prediction
-   Monthly AI insights
-   Duplicate detection
-   Recurring expense detection

Keep these features modular.

------------------------------------------------------------------------

# Configuration

Store configuration in:

.env

Use a settings module.

Never hardcode:

-   API keys
-   Passwords
-   Database URLs

------------------------------------------------------------------------

# Logging

Implement structured logging.

Log:

-   tool execution
-   database errors
-   validation failures
-   startup/shutdown

------------------------------------------------------------------------

# Error Handling

Never expose raw exceptions.

Return meaningful MCP-friendly responses.

Create custom exceptions.

------------------------------------------------------------------------

# Security

Implement:

-   SQL injection protection
-   Input validation
-   Audit logging
-   Soft delete
-   Environment variable management

Prepare architecture for JWT authentication and RBAC.

------------------------------------------------------------------------

# Testing

Create:

-   Unit tests
-   Repository tests
-   Service tests
-   MCP tool tests

------------------------------------------------------------------------

# Docker

Provide:

-   Dockerfile
-   docker-compose.yml

Compose should start:

-   PostgreSQL
-   Expense Tracker MCP

------------------------------------------------------------------------

# Documentation

Generate:

-   README.md
-   API documentation
-   MCP tool documentation
-   Setup guide
-   Development guide

------------------------------------------------------------------------

# Code Quality

Requirements:

-   Type hints everywhere
-   Google-style docstrings
-   Black formatting
-   Ruff compatible
-   Modular functions
-   No duplicated code

------------------------------------------------------------------------

# Migration Strategy

Preserve compatibility with the old SQLite schema by creating a
migration/import utility that can migrate existing expense records into
PostgreSQL.

------------------------------------------------------------------------

# Deliverables

Produce:

1.  Complete project structure
2.  Production-ready code
3.  PostgreSQL integration
4.  SQLAlchemy models
5.  Alembic migrations
6.  MCP tools
7.  Tests
8.  Docker support
9.  Documentation
10. Clean, maintainable architecture

Do not leave placeholders or TODOs where complete implementations are
expected.
