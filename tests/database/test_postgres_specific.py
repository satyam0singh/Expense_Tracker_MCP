import pytest
import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.database.models.audit_log import AuditLog
from tests.database.conftest import SYSTEM_USER_ID

@pytest.mark.asyncio
@pytest.mark.postgres
async def test_postgres_jsonb_audit_log(postgres_session: AsyncSession):
    """Test that Postgres-specific JSONB columns can store and retrieve data."""
    
    # Create an audit log with nested JSON changes
    audit_id = uuid.uuid4()
    changes = {
        "before": {"amount": "10.00", "currency": "USD"},
        "after": {"amount": "20.00", "currency": "USD"},
        "meta": {"source": "mcp_client", "tags": ["important", "review_needed"]}
    }
    
    log = AuditLog(
        id=audit_id,
        user_id=SYSTEM_USER_ID,
        entity_type="expense",
        entity_id=uuid.uuid4(),
        action="update",
        changes=changes
    )
    
    postgres_session.add(log)
    await postgres_session.commit()
    
    # Retrieve it back
    result = await postgres_session.execute(select(AuditLog).where(AuditLog.id == audit_id))
    fetched_log = result.scalar_one_or_none()
    
    assert fetched_log is not None
    assert fetched_log.changes is not None
    assert fetched_log.changes["before"]["amount"] == "10.00"
    assert "important" in fetched_log.changes["meta"]["tags"]
