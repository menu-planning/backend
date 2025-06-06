from datetime import datetime
from typing import Annotated, Any
import re

from pydantic import BeforeValidator, Field

from src.logging.logger import logger

def validate_uuid_format(v: str) -> str:
        """Log a warning if the ID is not in UUID hex format."""
        if not re.match(r'^[0-9a-f]{32}$', v):
            logger.warning(f"ID '{v}' is not in UUID hex format (32 hexadecimal characters)")
        if len(v) > 36 or len(v) < 1:
            raise ValueError("ID length does not match required length")
        return v

# ID fields
UUIDId = Annotated[str, BeforeValidator(validate_uuid_format)]
UUIDIdOptional = Annotated[str | None, BeforeValidator(validate_uuid_format), Field(default=None)]

def _timestamp_check(v: Any):
    if v and not isinstance(v, datetime):
        try:
            return datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format. Must be isoformat: {v}") from e
    return v


CreatedAtValue = Annotated[datetime | None, BeforeValidator(_timestamp_check)]
