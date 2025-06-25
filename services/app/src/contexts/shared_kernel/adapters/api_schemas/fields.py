from typing import Annotated
from pydantic import BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text

TagValue = Annotated[str, BeforeValidator(validate_optional_text), Field(min_length=1, max_length=100)]
TagKey = Annotated[str, BeforeValidator(validate_optional_text), Field(min_length=1, max_length=50)]
TagType = Annotated[str, BeforeValidator(validate_optional_text), Field(min_length=1, max_length=50)]