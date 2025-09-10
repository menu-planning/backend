"""SQLAlchemy field type aliases for common column patterns.

This module provides type aliases that combine SQLAlchemy column configurations
with type annotations for common patterns like primary keys and indexed fields.
"""

from datetime import datetime
from typing import Annotated

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import mapped_column

# Primary key string field
strpk = Annotated[str, mapped_column(primary_key=True)]

# Required string field with database index
str_required_idx = Annotated[str, mapped_column(nullable=False, index=True)]

# Timezone-aware datetime fields
datetime_tz = Annotated[datetime, mapped_column(TIMESTAMP(timezone=True))]
datetime_tz_created = Annotated[
    datetime,
    mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), index=True),
]
datetime_tz_updated = Annotated[
    datetime,
    mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    ),
]
