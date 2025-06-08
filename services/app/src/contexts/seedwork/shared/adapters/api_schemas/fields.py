from datetime import datetime
from typing import Annotated, Any
import re

from pydantic import AfterValidator, Field

from src.logging.logger import logger

def validate_uuid_format(v: str) -> str:
        """Log a warning if the ID is not in UUID hex format."""
        if not re.match(r'^[0-9a-f]{32}$', v):
            logger.warning(f"ID '{v}' is not in UUID hex format (32 hexadecimal characters)")
        if len(v) > 36 or len(v) < 1:
            raise ValueError("ID length does not match required length")
        return v

# ID fields
UUIDId = Annotated[str, AfterValidator(validate_uuid_format)]
UUIDIdOptional = Annotated[
    str | None, 
    Field(default=None), 
    AfterValidator(lambda v: validate_uuid_format(v) if v is not None else None),
]

def _timestamp_check(v: Any) -> datetime:
    if v and not isinstance(v, datetime):
        try:
            return datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format. Must be isoformat: {v}") from e
    return v


CreatedAtValue = Annotated[datetime, Field(default=datetime.now()), AfterValidator(_timestamp_check)]

def trim_whitespace(v: str | None, value_if_none: Any) -> str | None:
    if v is None and value_if_none:
        return value_if_none
    if v is None:
        return None
    return v.strip()