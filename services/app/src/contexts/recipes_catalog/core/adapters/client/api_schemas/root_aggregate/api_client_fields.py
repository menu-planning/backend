from __future__ import annotations

from typing import Annotated
from pydantic import Field

# Required object fields
ClientProfile = Annotated[
    'ApiProfile',  # type: ignore # Forward reference to avoid circular import
    Field(..., description="Profile information of the client"),
]

# Optional object fields
ClientContactInfo = Annotated[
    'ApiContactInfo | None',  # type: ignore # Forward reference to avoid circular import
    Field(None, description="Contact information of the client"),
]

ClientAddress = Annotated[
    'ApiAddress | None',  # type: ignore # Forward reference to avoid circular import
    Field(None, description="Address of the client"),
]

# Optional string fields
ClientNotes = Annotated[
    str | None,
    Field(None, description="Additional notes about the client"),
]

# Collection fields
ClientTags = Annotated[
    'frozenset[ApiTag]',  # type: ignore # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Frozenset of tags associated with the client"),
]

ClientMenus = Annotated[
    'list[ApiMenu]',  # type: ignore # Forward reference to avoid circular import
    Field(default_factory=list, description="List of menus associated with the client"),
] 