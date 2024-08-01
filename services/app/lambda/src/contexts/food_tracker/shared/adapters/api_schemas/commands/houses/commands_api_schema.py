import cattrs
from pydantic import UUID4, BaseModel
from src.contexts.food_tracker.shared.adapters.api_schemas.pydantic_validators import (
    NonEmptyStr,
)
from src.contexts.food_tracker.shared.domain.commands import (
    AddReceipt,
    ChangeHouseName,
    CreateHouse,
    DiscardHouses,
    InviteMember,
    InviteNutritionist,
    RemoveMember,
    RemoveNutritionist,
)


class ApiAddReceipt(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new receipt via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        cfe_key (str): The receipt's CFE key.
        house_id (UUID4, optional): The house id where the receipt belongs.
        qrcode (str, optional): The receipt's QR code.

    Methods:
        to_domain() -> AddReceipt:
            Converts the instance to a domain model object for adding a receipt.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    cfe_key: NonEmptyStr
    house_id: str | None = None
    qrcode: str | None = None

    def to_domain(self) -> AddReceipt:
        """Converts the instance to a domain model object for adding a receipt."""
        try:
            return cattrs.structure(self.model_dump(), AddReceipt)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiAddReceipt to domain model: {e}")


class ApiCreateHouse(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to create a new house via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        owner_id (UUID4): The owner's id.
        name (str): The house's name.

    Methods:
        to_domain() -> CreateHouse:
            Converts the instance to a domain model object for creating a house.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    owner_id: str
    name: NonEmptyStr

    def to_domain(self) -> CreateHouse:
        """Converts the instance to a domain model object for creating a house."""
        try:
            return cattrs.structure(self.model_dump(), CreateHouse)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateHouse to domain model: {e}")


class ApiChangeHouseName(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to change a house's name via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        house_id (UUID4): The house's id.
        name (str): The new name for the house.

    Methods:
        to_domain() -> ChangeHouseName:
            Converts the instance to a domain model object for changing a house's name.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    house_id: str
    name: NonEmptyStr

    def to_domain(self) -> ChangeHouseName:
        """Converts the instance to a domain model object for changing a house's name."""
        try:
            return cattrs.structure(self.model_dump(), ChangeHouseName)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiChangeHouseName to domain model: {e}"
            )


class ApiDiscardHouses(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to discard houses via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        house_ids (list[UUID4]): The ids of the houses to discard.

    Methods:
        to_domain() -> DiscardHouses:
            Converts the instance to a domain model object for discarding houses.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    house_ids: list[UUID4]

    def to_domain(self) -> DiscardHouses:
        try:
            return cattrs.structure(self.model_dump(), DiscardHouses)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDiscardHouses to domain model: {e}")


class ApiInviteMember(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to invite a member to a house via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        member_id (UUID4): The member's id.
        house_id (UUID4): The house's id.

    Methods:
        to_domain() -> InviteMember:
            Converts the instance to a domain model object for inviting a member.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    member_id: str
    house_id: str

    def to_domain(self) -> InviteMember:
        """Converts the instance to a domain model object for inviting a member."""
        try:
            cattrs.structure(self.model_dump(), InviteMember)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiInviteMember to domain model: {e}")


class ApiRemoveMember(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to remove a member from a house via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        member_id (UUID4): The member's id.
        house_id (UUID4): The house's id.

    Methods:
        to_domain() -> RemoveMember:
            Converts the instance to a domain model object for removing a member.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    member_id: str
    house_id: str

    def to_domain(self) -> RemoveMember:
        """Converts the instance to a domain model object for removing a member."""
        try:
            cattrs.structure(self.model_dump(), RemoveMember)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiRemoveMember to domain model: {e}")


class ApiInviteNutritionist(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to invite a nutritionist to a house via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        nutritionist_id (UUID4): The nutritionist's id.
        house_id (UUID4): The house's id.

    Methods:
        to_domain() -> InviteNutritionist:
            Converts the instance to a domain model object for inviting a nutritionist.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    nutritionist_id: str
    house_id: str

    def to_domain(self) -> InviteNutritionist:
        """Converts the instance to a domain model object for inviting a nutritionist."""
        try:
            cattrs.structure(self.model_dump(), InviteNutritionist)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiInviteNutritionist to domain model: {e}"
            )


class ApiRemoveNutritionist(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to remove a nutritionist from a house via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        nutritionist_id (UUID4): The nutritionist's id.
        house_id (UUID4): The house's id.

    Methods:
        to_domain() -> RemoveNutritionist:
            Converts the instance to a domain model object for removing a nutritionist.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    nutritionist_id: str
    house_id: str

    def to_domain(self) -> RemoveNutritionist:
        """Converts the instance to a domain model object for removing a nutritionist."""
        try:
            cattrs.structure(self.model_dump(), RemoveNutritionist)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiRemoveNutritionist to domain model: {e}"
            )
