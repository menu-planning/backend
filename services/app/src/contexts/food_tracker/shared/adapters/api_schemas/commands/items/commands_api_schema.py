from datetime import datetime
from typing import Any

import cattrs
from pydantic import (
    UUID4,
    BaseModel,
    Field,
    NonNegativeFloat,
    PastDatetime,
    field_serializer,
)
from src.contexts.food_tracker.shared.adapters.api_schemas.pydantic_validators import (
    NonEmptyStr,
)
from src.contexts.food_tracker.shared.domain.commands.add_item import AddItem
from src.contexts.food_tracker.shared.domain.commands.discard_items import DiscardItems
from src.contexts.food_tracker.shared.domain.commands.update_item import UpdateItem
from src.contexts.seedwork.shared.utils import converter
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.amount import (
    ApiAmount,
)


class ApiAddItem(BaseModel):
    date: PastDatetime
    description: NonEmptyStr
    amount: ApiAmount
    price_per_unit: NonNegativeFloat | None = None
    barcode: str | None = None
    cfe_key: str | None = None
    product_id: str | None = None
    house_ids: list[UUID4] | None = Field(default_factory=list)

    @field_serializer("date")
    def serialize_date(self, date: PastDatetime, _info):
        """Serializes the date to a domain model."""
        return date.isoformat()

    def to_domain(self) -> AddItem:
        """Converts the instance to a domain model object."""
        try:
            return converter.structure(self.model_dump(), AddItem)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiAddItem to domain model: {e}")


class ApiAddItemBulk(BaseModel):
    add_item_cmds: list[ApiAddItem]

    def to_domain(self) -> list[AddItem]:
        """Converts the instance to a list of domain model objects."""
        try:
            return [cmd.to_domain() for cmd in self.add_item_cmds]
        except Exception as e:
            raise ValueError(f"Failed to convert ApiAddItemBulk to domain model: {e}")


class ApiDiscardItems(BaseModel):
    item_ids: list[UUID4]

    def to_domain(self) -> DiscardItems:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), DiscardItems)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDiscardItems to domain model: {e}")


class ApiAttributesToUpdateOnItem(BaseModel):
    """
    A pydantic model representing and validating the data required to update
    a item via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        date (int): Date of the item.
        description (str): Description of the item.
        amount (ApiAmount): Amount of the item.
        is_food (bool): Whether the item is food.
        price_per_unit (float): Price per unit of the item.
        product_id (str): Identifier of the product associated with the item.


    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    date: datetime
    description: str
    amount: ApiAmount
    is_food: bool | None = None
    price_per_unit: float | None = None
    product_id: str | None = None

    # @field_serializer("amount")
    # def serialize_nutri_facts(self, amount: ApiAmount | None, _info):
    #     """Serializes the amount to a domain model."""
    #     return amount.to_domain() if amount else None

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump()
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnItem to domain model: {e}"
            )


class ApiUpdateItem(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a item via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        item_id (str): Identifier of the item to update.
        updates (ApiAttributesToUpdateOnRecipe): Attributes to update.

    Methods:
        to_domain() -> UpdateItem:
            Converts the instance to a domain model object for updating a item.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    item_id: str
    updates: ApiAttributesToUpdateOnItem

    def to_domain(self) -> UpdateItem:
        """Converts the instance to a domain model object for updating a item."""
        try:
            return UpdateItem(item_id=self.item_id, updates=self.updates.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateItem to domain model: {e}")
