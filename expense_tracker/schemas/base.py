"""Base Pydantic schemas.

Provides shared base classes for all schemas to ensure consistent
config (e.g., ORM mode enabled, timezone awareness).
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base Pydantic schema with standard configuration.

    Enables reading from SQLAlchemy ORM models directly.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )


class BaseResponse(BaseSchema):
    """Base schema for response objects containing standard ORM fields."""

    id: uuid.UUID = Field(description="Unique identifier (UUID)")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
