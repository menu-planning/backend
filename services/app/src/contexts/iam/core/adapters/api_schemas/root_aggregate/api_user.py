from datetime import datetime
from typing import Any, Dict, Annotated
from pydantic import Field

from src.contexts.iam.core.adapters.api_schemas.value_objects.api_role import ApiRole
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity

class ApiUser(BaseApiEntity[User, UserSaModel]):
    """A Pydantic model representing and validating user data for API requests and responses.
    
    Security-Critical Validation Strategy:
    - BeforeValidator(validate_optional_text): Input sanitization for user ID (trim, handle None/empty)
    - AfterValidator(validate_iam_user_id_format): Security-critical business logic validation
    - BeforeValidator(validate_iam_roles_collection): Collection validation with IAM context security checks
    
    This model is used for input validation and serialization of domain objects in API requests and responses.
    It inherits from BaseEntity which provides common fields and configuration.
    
    Attributes:
        roles (frozenset[ApiRole]): Frozenset of IAM roles assigned to the user
        discarded (bool): Whether the user is discarded
        version (int): Version number for optimistic locking
        created_at (datetime): When the user was created
        updated_at (datetime): When the user was last updated
    """

    
    roles: Annotated[
        frozenset[ApiRole],
        Field(default_factory=frozenset, description="Set of IAM roles assigned to the user")
    ]

    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Convert a domain User object to an ApiUser instance.
        
        Handles type conversions per docs/architecture/api-schema-patterns/patterns/type-conversions.md:
        - Domain list[Role] → API frozenset[ApiRole] (collection type standardization)
        
        Args:
            domain_obj: The domain User object to convert
            
        Returns:
            An instance of ApiUser
            
        Raises:
            ValueError: If the conversion fails or security validation fails
        """
        try:
            return cls(
                id=domain_obj.id,
                roles=frozenset([ApiRole.from_domain(role) for role in domain_obj.roles]) if domain_obj.roles else frozenset(),  # list → frozenset conversion
                discarded=domain_obj.discarded,
                version=domain_obj.version,
                created_at=domain_obj.created_at or datetime.now(),
                updated_at=domain_obj.updated_at or datetime.now()
            )
        except Exception as e:
            raise ValueError(f"Failed to build IAM ApiUser from domain: {e}") from e

    def to_domain(self) -> User:
        """Convert the ApiUser instance to a domain User object.
        
        Handles type conversions per documented patterns:
        - API frozenset[ApiRole] → Domain list[Role] (collection type conversion)
        
        Returns:
            A User domain object
            
        Raises:
            ValueError: If the conversion fails
        """
        try:
            return User(
                id=str(self.id),
                roles=[role.to_domain() for role in self.roles] if self.roles else [],  # frozenset → list conversion
                discarded=self.discarded,
                version=self.version,
                created_at=self.created_at,
                updated_at=self.updated_at
            )
        except Exception as e:
            raise ValueError(f"Failed to convert IAM ApiUser to domain: {e}") from e

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiUser":
        """Convert a SQLAlchemy UserSaModel to an ApiUser instance.
        
        Handles ORM → API conversions per documented patterns:
        - ORM list[RoleSaModel] → API frozenset[ApiRole]
        
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
                roles=frozenset([ApiRole.from_orm_model(role) for role in orm_model.roles]) if orm_model.roles else frozenset(),
                discarded=orm_model.discarded,
                version=orm_model.version,
                created_at=orm_model.created_at or datetime.now(),
                updated_at=orm_model.updated_at or datetime.now()
            )
        except Exception as e:
            raise ValueError(f"Failed to build IAM ApiUser from ORM model: {e}") from e

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the ApiUser instance to a dictionary of kwargs for ORM model creation.
        
        Handles API → ORM conversions per documented patterns:
        - API frozenset[ApiRole] → ORM list[role_kwargs]
        
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
            raise ValueError(f"Failed to convert IAM ApiUser to ORM kwargs: {e}") from e
