from datetime import datetime
from typing import Any, Dict

from pydantic import Field

from src.contexts.iam.core.adapters.api_schemas.value_objects.role import ApiRole
from src.contexts.iam.core.adapters.ORM.sa_models.user import UserSaModel
from src.contexts.iam.core.domain.entities.user import User
from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseEntity


class ApiUser(BaseEntity[User, UserSaModel]):
    """A Pydantic model representing and validating user data for API requests and responses.
    
    This model is used for input validation and serialization of domain objects in API requests and responses.
    It inherits from BaseEntity which provides common fields and configuration.
    
    Attributes:
        id (str): The unique identifier of the user
        roles (set[ApiRole]): set of roles assigned to the user
        discarded (bool): Whether the user is discarded
        version (int): Version number for optimistic locking
        created_at (datetime): When the user was created
        updated_at (datetime): When the user was last updated
    """

    roles: set[ApiRole] = Field(default_factory=set)

    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Convert a domain User object to an ApiUser instance.
        
        Args:
            domain_obj: The domain User object to convert
            
        Returns:
            An instance of ApiUser
            
        Raises:
            ValueError: If the conversion fails
        """
        try:
            return cls(
                id=domain_obj.id,
                roles=set([ApiRole.from_domain(role) for role in domain_obj.roles]) if domain_obj.roles else set(),
                discarded=domain_obj.discarded,
                version=domain_obj.version,
                created_at=domain_obj.created_at or datetime.now(),
                updated_at=domain_obj.updated_at or datetime.now()
            )
        except Exception as e:
            raise ValueError(f"Failed to build from domain: {e}") from e

    def to_domain(self) -> User:
        """Convert the ApiUser instance to a domain User object.
        
        Returns:
            A User domain object
            
        Raises:
            ValueError: If the conversion fails
        """
        try:
            return User(
                id=str(self.id),
                roles=[role.to_domain() for role in self.roles] if self.roles else [],
                discarded=self.discarded,
                version=self.version,
                created_at=self.created_at,
                updated_at=self.updated_at
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiUser":
        """Convert a SQLAlchemy UserSaModel to an ApiUser instance.
        
        Args:
            orm_model: The SQLAlchemy model to convert
            
        Returns:
            An instance of ApiUser
            
        Raises:
            ValueError: If the conversion fails
        """
        try:
            return cls(
                id=orm_model.id,
                roles=set([ApiRole.from_orm_model(role) for role in orm_model.roles]) if orm_model.roles else set(),
                discarded=orm_model.discarded,
                version=orm_model.version,
                created_at=orm_model.created_at or datetime.now(),
                updated_at=orm_model.updated_at or datetime.now()
            )
        except Exception as e:
            raise ValueError(f"Failed to build from ORM model: {e}") from e

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the ApiUser instance to a dictionary of kwargs for ORM model creation.
        
        Returns:
            Dictionary of kwargs for ORM model creation
            
        Raises:
            ValueError: If the conversion fails
        """
        try:
            return {
                "id": str(self.id),
                "roles": [role.to_orm_kwargs() for role in self.roles] if self.roles else [],
                "discarded": self.discarded,
                "version": self.version,
                "created_at": self.created_at,
                "updated_at": self.updated_at
            }
        except Exception as e:
            raise ValueError(f"Failed to convert to ORM kwargs: {e}") from e
