from typing import Annotated

from pydantic import Field
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)

TagValue = Annotated[SanitizedText, Field(min_length=1, max_length=100)]
TagKey = Annotated[SanitizedText, Field(min_length=1, max_length=50)]
TagType = Annotated[SanitizedText, Field(min_length=1, max_length=50)]
