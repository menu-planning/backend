from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole, validate_role_name_format

class ApiRole(ApiSeedRole):
    """
    Recipes Catalog API schema for Role. Inherits from ApiSeedRole.
    Extend here if recipes_catalog needs custom fields or validation.
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
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        """Convert a Role domain object to an ApiRole instance."""
        return cls(
            name=domain_obj.name,
            permissions=frozenset(domain_obj.permissions)
        )
    
    def to_domain(self) -> Role:
        """Convert an ApiRole instance to a Role domain object."""
        return Role(
            name=self.name,
            permissions=frozenset(self.permissions)
        )
    
    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Convert a RoleSaModel instance to an ApiRole instance."""
        return cls(
            name=orm_model.name,
            permissions=frozenset(
                perm.strip() for perm in orm_model.permissions.split(", ") 
                if perm.strip()
            ) if orm_model.permissions else frozenset()
        )
    
    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert an ApiRole instance to a dictionary of keyword arguments for RoleSaModel."""
        return {
            "name": self.name,
            "permissions": ", ".join(sorted(self.permissions)) if self.permissions else ""
        }