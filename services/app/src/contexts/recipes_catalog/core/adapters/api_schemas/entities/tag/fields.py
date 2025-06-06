from typing import Annotated
from pydantic import BeforeValidator, Field

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag, TagSetAdapter


TagValue = Annotated[str, Field(min_length=1, max_length=100)]
TagKey = Annotated[str, Field(min_length=1, max_length=50)]
TagType = Annotated[str, Field(min_length=1, max_length=50)]
TagSet = Annotated[set[ApiTag], BeforeValidator(TagSetAdapter.validate_python)]
