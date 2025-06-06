from typing import Any, Dict, List
from pydantic import Field, field_validator

from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.seedwork.shared.adapters.api_schemas.type_adapters import RoleListAdapter
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.iam.core.adapters.ORM.sa_models.user import UserSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole

class ApiSeedUser(BaseValueObject[SeedUser, UserSaModel]):
    """Schema for the SeedUser value object."""
    
    id: str = Field(..., min_length=1, description="The unique identifier of the user")
    roles: List[ApiSeedRole] = Field(default_factory=list, description="List of roles assigned to the user")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that the user ID is not empty."""
        if not v:
            raise ValueError("User ID cannot be empty")
        return v

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v: List[ApiSeedRole]) -> List[ApiSeedRole]:
        """Validate roles using TypeAdapter."""
        return RoleListAdapter.validate_python(v)

    @classmethod
    def from_domain(cls, domain_obj: SeedUser) -> "ApiSeedUser":
        """Convert a SeedUser domain object to an ApiSeedUser instance.
        
        Args:
            domain_obj: The SeedUser domain object to convert
            
        Returns:
            An ApiSeedUser instance
        """
        return cls(
            id=domain_obj.id,
            roles=RoleListAdapter.validate_python([ApiSeedRole.from_domain(role) for role in domain_obj.roles] if domain_obj.roles else [])
        )

    def to_domain(self) -> SeedUser:
        """Convert the ApiSeedUser instance to a SeedUser domain object.
        
        Returns:
            A SeedUser instance
        """
        return SeedUser(
            id=self.id,
            roles=[role.to_domain() for role in self.roles] if self.roles else []
        )

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiSeedUser":
        """Convert an ORM model to an ApiSeedUser instance.
        
        Args:
            orm_model: The ORM model to convert
            
        Returns:
            An ApiSeedUser instance
        """
        return cls(
            id=orm_model.id,
            roles=RoleListAdapter.validate_python([ApiSeedRole.from_orm_model(role) for role in orm_model.roles] if orm_model.roles else [])
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the ApiSeedUser instance to ORM model kwargs.
        
        Returns:
            Dictionary of kwargs for ORM model creation
        """
        return {
            "id": self.id,
            "roles": [role.to_orm_kwargs() for role in self.roles] if self.roles else []
        }
