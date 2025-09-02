from __future__ import annotations

from typing import Annotated, Any

from pydantic import AfterValidator, Field
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import (
    ApiMenu,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedTextOptional,
)
from src.contexts.seedwork.adapters.api_schemas.validators import (
    validate_optional_text_length,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_address import (
    ApiAddress,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import (
    ApiContactInfo,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import (
    ApiProfile,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)

ClientProfileRequired = Annotated[
    ApiProfile,
    Field(..., description="Profile information of the client"),
]

ClientContactInfoOptinal = Annotated[
    ApiContactInfo | None,
    Field(None, description="Contact information of the client"),
]

ClientAddressOptional = Annotated[
    ApiAddress | None,
    Field(None, description="Address of the client"),
]

ClientNotesOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Notes of the client"),
    AfterValidator(lambda v: validate_optional_text_length(v, 10000, "Notes must be less than 10000 characters")),
]

ClientTagsOptionalFrozenset = Annotated[
    frozenset[ApiTag] | None,
    Field(default_factory=frozenset, description="Frozenset of tags associated with the client"),
]

ClientMenusOptionalList = Annotated[
    list[ApiMenu] | None,
    Field(default_factory=list, description="List of menus associated with the client"),
]

ClientOnboardingDataOptional = Annotated[
    dict[str, Any] | None,
    Field(None, description="Original form response data from client onboarding"),
]
