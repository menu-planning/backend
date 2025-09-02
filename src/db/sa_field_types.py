"""SQLAlchemy field type aliases for common column patterns.

This module provides type aliases that combine SQLAlchemy column configurations
with type annotations for common patterns like primary keys and indexed fields.
"""

from typing import Annotated

from sqlalchemy.orm import mapped_column

# Primary key string field
strpk = Annotated[str, mapped_column(primary_key=True)]

# Required string field with database index
str_required_idx = Annotated[str, mapped_column(nullable=False, index=True)]
