from datetime import datetime

from pydantic import UUID4, BaseModel, Field
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.amount import (
    ApiAmount,
)


class ApiItem(BaseModel):
    id: str
    house_id: str
    date: datetime
    description: str
    amount: ApiAmount
    is_food: bool | None = None
    price_per_unit: float | None = None
    barcode: str | None = None
    cfe_key: str | None = None
    product_id: str | None = None
    ids_of_products_with_similar_names: list[UUID4] = Field(default_factory=list)
    discarded: bool = False

    @classmethod
    def from_domain(cls, domain_obj: Item) -> "ApiItem":
        return cls(
            id=domain_obj.id,
            house_id=domain_obj.house_id,
            date=domain_obj.date,
            description=domain_obj.description,
            amount=ApiAmount.from_domain(domain_obj.amount),
            is_food=domain_obj.is_food,
            price_per_unit=domain_obj.price_per_unit,
            barcode=domain_obj.barcode,
            cfe_key=domain_obj.cfe_key,
            product_id=domain_obj.product_id,
            ids_of_products_with_similar_names=domain_obj.ids_of_products_with_similar_names,
            discarded=domain_obj.discarded,
        )

    def to_domain(self) -> Item:
        return Item(
            id=self.id,
            house_id=self.house_id,
            date=self.date,
            description=self.description,
            amount=self.amount.to_domain(),
            is_food=self.is_food,
            price_per_unit=self.price_per_unit,
            barcode=self.barcode,
            cfe_key=self.cfe_key,
            product_id=self.product_id.hex if self.product_id else None,
            ids_of_products_with_similar_names=self.ids_of_products_with_similar_names,
            discarded=self.discarded,
        )
