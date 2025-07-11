from __future__ import annotations

from typing import Annotated
from pydantic import Field

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import ApiMenu
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_address import ApiAddress
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

# Required object fields
ClientProfileRequired = Annotated[
    ApiProfile,
    Field(..., description="Profile information of the client"),
]

# Optional object fields
ClientContactInfoOptinal = Annotated[ 
    ApiContactInfo | None,
    Field(None, description="Contact information of the client"),
]

ClientAddressOptional = Annotated[
    ApiAddress | None,
    Field(None, description="Address of the client"),
]

# Optional string fields
ClientNotesOptional = Annotated[
    str | None,
    Field(None, description="Additional notes about the client"),
]

# Collection fields
ClientTagsOptionalFrozenset = Annotated[
    frozenset[ApiTag] | None,
    Field(default_factory=frozenset, description="Frozenset of tags associated with the client"),
]

ClientMenusOptionalList = Annotated[
    list[ApiMenu] | None,
    Field(default_factory=list, description="List of menus associated with the client"),
] 