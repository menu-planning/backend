from typing import Annotated
from pydantic import Field

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import ApiMenu
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.address import ApiAddress
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag

# Required object fields
ClientProfile = Annotated[
    ApiProfile,  # Forward reference to avoid circular import
    Field(..., description="Profile information of the client"),
]

# Optional object fields
ClientContactInfo = Annotated[
    ApiContactInfo | None,  # Forward reference to avoid circular import
    Field(None, description="Contact information of the client"),
]

ClientAddress = Annotated[
    ApiAddress | None,  # Forward reference to avoid circular import
    Field(None, description="Address of the client"),
]

# Optional string fields
ClientNotes = Annotated[
    str | None,
    Field(None, description="Additional notes about the client"),
]

# Collection fields
ClientTags = Annotated[
    frozenset[ApiTag],  # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Frozenset of tags associated with the client"),
]

ClientMenus = Annotated[
    list[ApiMenu],  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of menus associated with the client"),
] 