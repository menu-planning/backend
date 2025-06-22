from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from pydantic import Field


class ApiRole(BaseValueObject[Role, RoleSaModel]):
    """A class to represent and validate a role in the IAM context."""

    name: str
    context: str = Field(default="IAM")
    permissions: list[str] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        """Creates an instance of `ApiRole` from a domain model object.
        
        Args:
            domain_obj: The domain Role object to convert
            
        Returns:
            An instance of ApiRole
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            return cls(
                name=domain_obj.name,
                context=domain_obj.context,
                permissions=domain_obj.permissions,
            )
        except Exception as e:
            raise ValueError(f"Failed to build from domain: {e}") from e

    def to_domain(self) -> Role:
        """Converts the instance to a domain model object.
        
        Returns:
            A Role domain object
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            return Role(
                name=self.name,
                context=self.context,
                permissions=self.permissions,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Convert from ORM model.
        
        Args:
            orm_model: The SQLAlchemy model to convert from
            
        Returns:
            An instance of ApiRole
        """
        data = {
            "name": orm_model.name,
            "context": orm_model.context,
            "permissions": [p.strip() for p in orm_model.permissions.split(",")] if orm_model.permissions else [],
        }
        return cls.model_validate(data)

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs.
        
        Returns:
            Dictionary of kwargs for ORM model creation
        """
        data = self.model_dump()
        data["permissions"] = ",".join(self.permissions) if self.permissions else ""
        return data
