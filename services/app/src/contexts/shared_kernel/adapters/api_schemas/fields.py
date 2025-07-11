from typing import Annotated
from pydantic import BeforeValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str

TagValue = Annotated[str, BeforeValidator(remove_whitespace_and_empty_str), Field(min_length=1, max_length=100)]
TagKey = Annotated[str, BeforeValidator(remove_whitespace_and_empty_str), Field(min_length=1, max_length=50)]
TagType = Annotated[str, BeforeValidator(remove_whitespace_and_empty_str), Field(min_length=1, max_length=50)]