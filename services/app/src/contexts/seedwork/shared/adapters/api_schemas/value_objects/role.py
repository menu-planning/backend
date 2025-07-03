from typing import Any, Dict, Annotated
from pydantic import Field, AfterValidator, BeforeValidator


from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel


def validate_role_name_format(v: str) -> str:
    """Validate role name format after basic text processing.
    
    Uses AfterValidator for type safety - input is guaranteed to be str.
    """
    if not v.islower():
        raise ValueError("Role name must be lowercase")
    if not all(c.isalnum() or c == '_' or c == '-' for c in v):
        raise ValueError("Role name must contain only alphanumeric characters, underscores, and hyphens")
    return v

class ApiSeedRole(BaseApiValueObject[SeedRole, RoleSaModel]):
    """Schema for the SeedRole value object.
    
    Validation Strategy:
    - BeforeValidator(validate_optional_text): Input sanitization (trim, handle None/empty)
    - AfterValidator(validate_role_name_format): Business logic validation (type-safe)
    - BeforeValidator(validate_permissions_collection): Complex type conversion with clear errors
    """
    
    name: Annotated[
        str, 
        BeforeValidator(validate_optional_text),
        AfterValidator(validate_role_name_format),
        Field(..., min_length=1, description="The name of the role")
    ]
    permissions: Annotated[
        frozenset[str],
        Field(default_factory=frozenset, description="Set of permissions associated with the role")
    ]

    @classmethod
    def from_domain(cls, domain_obj: SeedRole) -> "ApiSeedRole":
        """Convert a SeedRole domain object to an ApiSeedRole instance.
        
        Handles type conversions per docs/architecture/api-schema-patterns/patterns/type-conversions.md:
        - Domain frozenset[str] → API frozenset[str] (already correct type)
        
        Args:
            domain_obj: The SeedRole domain object to convert
            
        Returns:
            An ApiSeedRole instance
        """
        return cls(
            name=domain_obj.name,
            permissions=frozenset(domain_obj.permissions)  # Ensure frozenset type
        )

    def to_domain(self) -> SeedRole:
        """Convert the ApiSeedRole instance to a SeedRole domain object.
        
        Handles type conversions per documented patterns:
        - API frozenset[str] → Domain frozenset[str] (no conversion needed)
        
        Returns:
            A SeedRole instance
        """
        return SeedRole(
            name=self.name,
            permissions=frozenset(self.permissions)  # Maintain frozenset type
        )

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiSeedRole":
        """Convert an ORM model to an ApiSeedRole instance.
        
        Handles ORM → API conversions per documented patterns:
        - ORM comma-separated string → API frozenset[str]
        
        Args:
            orm_model: The ORM model to convert
            
        Returns:
            An ApiSeedRole instance
        """
        return cls(
            name=orm_model.name,
            permissions=frozenset(
                perm.strip() for perm in orm_model.permissions.split(", ") 
                if perm.strip()
            ) if orm_model.permissions else frozenset()
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the ApiSeedRole instance to ORM model kwargs.
        
        Handles API → ORM conversions per documented patterns:
        - API frozenset[str] → ORM comma-separated string
        
        Returns:
            Dictionary of kwargs for ORM model creation
        """
        return {
            "name": self.name,
            "permissions": ", ".join(sorted(self.permissions)) if self.permissions else ""
        }
