from typing import Annotated
from pydantic import AfterValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.fields import trim_whitespace

TagValue = Annotated[str, Field(min_length=1, max_length=100), AfterValidator(trim_whitespace)]
TagKey = Annotated[str, Field(min_length=1, max_length=50), AfterValidator(trim_whitespace)]
TagType = Annotated[str, Field(min_length=1, max_length=50), AfterValidator(trim_whitespace)]