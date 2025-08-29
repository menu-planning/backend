from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import Field

from src.contexts.iam.core.adapters.api_schemas.value_objects.api_role import ApiRole
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiEntity,
)


class ApiUser(BaseApiEntity[User, UserSaModel]):
    """A Pydantic model representing and validating user data for
    API requests and responses.

    Security-Critical Validation Strategy:
    - BeforeValidator(validate_optional_text): Input sanitization for user ID
                                               (trim, handle None/empty)
    - AfterValidator(validate_iam_user_id_format): Security-critical business
                                                   logic validation
    - BeforeValidator(validate_iam_roles_collection): Collection validation with IAM
                                                      context security checks

    This model is used for input validation and serialization of domain objects
    in API requests and responses.
    It inherits from BaseEntity which provides common fields and configuration.

    Attributes:
        roles (frozenset[ApiRole]): Frozenset of IAM roles assigned to the user.
                                   Immutable collection ensuring role consistency.
        discarded (bool): Whether the user is discarded/deleted.
        version (int): Version number for optimistic locking during concurrent updates.
        created_at (datetime): Timestamp when the user was created.
        updated_at (datetime): Timestamp when the user was last updated.
    """

    roles: Annotated[
        frozenset[ApiRole],
        Field(
            default_factory=frozenset,
            description="Set of IAM roles assigned to the user",
        ),
    ]

    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Convert a domain User object to an ApiUser instance.

        This method handles the conversion from the domain layer to the API layer,
        ensuring proper type conversions and validation. It's typically used when
        returning user data from the API.

        Handles type conversions:
        - Domain list[Role] → API frozenset[ApiRole] (collection type standardization)
        - Ensures roles are properly converted and validated

        Args:
            domain_obj (User): The domain User object to convert. Must be a valid
                             User instance with all required attributes.

        Returns:
            ApiUser: An instance of ApiUser populated with data from the domain object.

        Raises:
            ValueError: If the conversion fails, validation fails, or the domain object
                       is malformed. This includes cases where role conversion fails
                       or required attributes are missing.

        Example:
            ```python
            domain_user = User(...)
            api_user = ApiUser.from_domain(domain_user)
            ```
        """
        try:
            return cls(
                id=domain_obj.id,
                roles=(
                    frozenset([ApiRole.from_domain(role) for role in domain_obj.roles])
                    if domain_obj.roles
                    else frozenset()
                ),  # list → frozenset conversion
                discarded=domain_obj.discarded,
                version=domain_obj.version,
                created_at=domain_obj.created_at or datetime.now(UTC),
                updated_at=domain_obj.updated_at or datetime.now(UTC),
            )
        except Exception as e:
            error_message = f"Failed to build IAM ApiUser from domain: {e}"
            raise ValueError(error_message) from e

    def to_domain(self) -> User:
        """Convert the ApiUser instance to a domain User object.

        This method handles the conversion from the API layer back to the domain layer,
        typically used when processing incoming API requests that need to be converted
        to domain objects for business logic processing.

        Handles type conversions per documented patterns:
        - API frozenset[ApiRole] → Domain list[Role] (collection type conversion)
        - Maintains data integrity during the conversion process

        Returns:
            User: A User domain object populated with data from the API model.

        Raises:
            ValueError: If the conversion fails, validation fails, or required
                       attributes are missing. This includes cases where role
                       conversion fails or the API model is in an invalid state.

        Example:
            ```python
            api_user = ApiUser(...)
            domain_user = api_user.to_domain()
            ```
        """
        try:
            return User(
                entity_id=str(self.id),
                roles=(
                    [role.to_domain() for role in self.roles] if self.roles else []
                ),  # frozenset → list conversion
                discarded=self.discarded,
                version=self.version,
                created_at=self.created_at,
                updated_at=self.updated_at,
            )
        except Exception as e:
            error_message = f"Failed to convert IAM ApiUser to domain: {e}"
            raise ValueError(error_message) from e

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiUser":
        """Convert a SQLAlchemy UserSaModel to an ApiUser instance.

        This method handles the conversion from the ORM layer to the API layer,
        typically used when retrieving user data from the database and preparing
        it for API responses.

        Handles ORM → API conversions per documented patterns:
        - ORM list[RoleSaModel] → API frozenset[ApiRole]
        - Ensures proper data type conversions and validation

        Args:
            orm_model (UserSaModel): The SQLAlchemy model to convert. Must be a
                                   valid UserSaModel instance with all required
                                   attributes and relationships loaded.

        Returns:
            ApiUser: An instance of ApiUser populated with data from the ORM model.

        Raises:
            ValueError: If the conversion fails, validation fails, or the ORM model
                       is malformed. This includes cases where role conversion fails,
                       required attributes are missing, or relationships are not
                       properly loaded.

        Example:
            ```python
            orm_user = UserSaModel.query.get(user_id)
            api_user = ApiUser.from_orm_model(orm_user)
            ```

        Note:
            Ensure that the ORM model has all necessary relationships (like roles)
            loaded before calling this method to avoid lazy loading issues.
        """
        try:
            return cls(
                id=orm_model.id,
                roles=(
                    frozenset(
                        [ApiRole.from_orm_model(role) for role in orm_model.roles]
                    )
                    if orm_model.roles
                    else frozenset()
                ),
                discarded=orm_model.discarded,
                version=orm_model.version,
                created_at=orm_model.created_at or datetime.now(UTC),
                updated_at=orm_model.updated_at or datetime.now(UTC),
            )
        except Exception as e:
            error_message = f"Failed to build IAM ApiUser from ORM model: {e}"
            raise ValueError(error_message) from e

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert the ApiUser instance to a dictionary of kwargs for ORM
        model creation.

        This method prepares the API model data for persistence to the database
        by converting it to a format suitable for ORM model instantiation.
        It's typically used when creating new user records or updating existing ones.

        Handles API → ORM conversions per documented patterns:
        - API frozenset[ApiRole] → ORM list[role_kwargs]
        - Ensures data is properly formatted for database operations

        Returns:
            dict[str, Any]: Dictionary of kwargs for ORM model creation. The keys
                           correspond to the ORM model's attribute names, and the
                           values are the properly formatted data ready for
                           database operations.

        Raises:
            ValueError: If the conversion fails, validation fails, or required
                       attributes are missing. This includes cases where role
                       conversion fails or the API model is in an invalid state.

        Example:
            ```python
            api_user = ApiUser(...)
            orm_kwargs = api_user.to_orm_kwargs()
            new_user = UserSaModel(**orm_kwargs)
            db.session.add(new_user)
            ```

        Note:
            The returned dictionary contains all necessary fields for creating
            or updating a UserSaModel, including properly formatted role data
            that can be directly used in database operations.
        """
        try:
            return {
                "id": str(self.id),
                "roles": (
                    [role.to_orm_kwargs() for role in self.roles] if self.roles else []
                ),
                "discarded": self.discarded,
                "version": self.version,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        except Exception as e:
            error_message = f"Failed to convert IAM ApiUser to ORM kwargs: {e}"
            raise ValueError(error_message) from e
