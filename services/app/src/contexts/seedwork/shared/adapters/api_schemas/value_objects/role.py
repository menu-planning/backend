from typing import Any, Dict, List, Union
from pydantic import Field, field_validator

from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel

class ApiSeedRole(BaseValueObject[SeedRole, RoleSaModel]):
    """Schema for the SeedRole value object."""
    
    name: str = Field(..., min_length=1, description="The name of the role")
    permissions: frozenset[str] = Field(default_factory=frozenset, description="Set of permissions associated with the role")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that the role name is lowercase and contains only alphanumeric characters, underscores, and hyphens."""
        if not v.islower():
            raise ValueError("Role name must be lowercase")
        if not all(c.isalnum() or c == '_' or c == '-' for c in v):
            raise ValueError("Role name must contain only alphanumeric characters, underscores, and hyphens")
        return v

    @field_validator('permissions', mode='before')
    @classmethod
    def validate_permissions(cls, v: Union[List[str], frozenset[str], set[str]]) -> frozenset[str]:
        """Validate that permissions are unique and non-empty."""
        if isinstance(v, (list, set)):
            v = frozenset(v)
        if not v:
            return frozenset()
        # frozensets automatically ensure uniqueness, so no need to check for duplicates
        return v

    @classmethod
    def from_domain(cls, domain_obj: SeedRole) -> "ApiSeedRole":
        """Convert a SeedRole domain object to an ApiSeedRole instance.
        
        Args:
            domain_obj: The SeedRole domain object to convert
            
        Returns:
            An ApiSeedRole instance
        """
        return cls(
            name=domain_obj.name,
            permissions=frozenset(domain_obj.permissions)
        )

    def to_domain(self) -> SeedRole:
        """Convert the ApiSeedRole instance to a SeedRole domain object.
        
        Returns:
            A SeedRole instance
        """
        return SeedRole(
            name=self.name,
            permissions=frozenset(self.permissions)
        )

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiSeedRole":
        """Convert an ORM model to an ApiSeedRole instance.
        
        Args:
            orm_model: The ORM model to convert
            
        Returns:
            An ApiSeedRole instance
        """
        return cls(
            name=orm_model.name,
            permissions=frozenset(orm_model.permissions.split(", ")) if orm_model.permissions else frozenset()
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the ApiSeedRole instance to ORM model kwargs.
        
        Returns:
            Dictionary of kwargs for ORM model creation
        """
        return {
            "name": self.name,
            "permissions": ", ".join(sorted(self.permissions)) if self.permissions else ""
        }
