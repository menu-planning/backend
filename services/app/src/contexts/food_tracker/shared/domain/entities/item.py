from datetime import datetime

from attrs import asdict
from src.contexts.food_tracker.shared.domain.events.events import (
    ItemAdded,
    ItemIsFoodChanged,
    ProductNotFound,
    WrongProductAllocated,
)
from src.contexts.food_tracker.shared.domain.rules import (
    CanNotChangeIsFoodAttributeOfItemWithUniqueBarcode,
    CanNotChangeProductOfItemWithUniqueBarcode,
)
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.value_objects import Amount


class Item(Entity):
    def __init__(
        self,
        *,
        id,
        house_id: str,
        date: datetime,
        description: str,
        amount: Amount,
        is_food: bool | None = None,
        price_per_unit: float | None = None,
        barcode: str | None = None,
        cfe_key: str | None = None,
        product_id: str | None = None,
        ids_of_productos_with_similar_names: set[str] | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new House."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._house_id = house_id
        self._date = date
        self._description = description
        self._amount = amount
        self._is_food = is_food
        self._product_id = product_id
        self._price_per_unit = price_per_unit
        self._barcode = barcode
        self._cfe_key = cfe_key
        self._ids_of_products_with_similar_names = (
            ids_of_productos_with_similar_names or set()
        )
        self.events: list[Event] = []

    @classmethod
    def add_item(
        cls,
        *,
        house_id: str,
        date: datetime,
        description: str,
        amount: Amount,
        is_food: bool | None = None,
        price_per_unit: float | None = None,
        barcode: str | None = None,
        cfe_key: str | None = None,
        product_id: str | None = None,
    ) -> "Item":
        event = ItemAdded()
        item = cls(
            id=event.item_id,
            house_id=house_id,
            date=date,
            description=description,
            amount=amount,
            is_food=is_food,
            price_per_unit=price_per_unit,
            barcode=barcode,
            cfe_key=cfe_key,
            product_id=product_id,
        )
        item.events.append(event)
        return item


    @property
    def house_id(self) -> str:
        self._check_not_discarded()
        return self._house_id

    @property
    def date(self) -> datetime:
        self._check_not_discarded()
        return self._date

    @date.setter
    def date(self, date: datetime) -> None:
        self._check_not_discarded()
        self._date = date
        self._increment_version()

    @property
    def description(self) -> str:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, description: str) -> None:
        self._check_not_discarded()
        self._description = description
        self._increment_version()

    @property
    def amount(self) -> Amount:
        self._check_not_discarded()
        return self._amount

    @amount.setter
    def amount(self, amount: Amount) -> None:
        self._check_not_discarded()
        self._amount = amount
        self._increment_version()

    @property
    def price_per_unit(self) -> float | None:
        self._check_not_discarded()
        return self._price_per_unit

    @price_per_unit.setter
    def price_per_unit(self, price_per_unit: float) -> None:
        self._check_not_discarded()
        self._price_per_unit = price_per_unit
        self._increment_version()

    @property
    def product_id(self) -> str | None:
        self._check_not_discarded()
        return self._product_id

    @product_id.setter
    def product_id(self, product_id: str | None) -> None:
        self._check_not_discarded()
        if product_id is None:
            self.events.append(
                ProductNotFound(
                    item_id=self.id,
                    description=self.description,
                    barcode=self.barcode,
                )
            )
        if product_id == self._product_id:
            return
        self.check_rule(
            CanNotChangeProductOfItemWithUniqueBarcode(
                product_id=self._product_id, is_barcode_unique=self.is_barcode_unique
            )
        )
        if (
            self.ids_of_products_with_similar_names
            and self.ids_of_products_with_similar_names[0] == self._product_id
        ):
            self.events.append(
                WrongProductAllocated(
                    item_id=self.id,
                    description=self.description,
                    product_id=self._product_id,
                )
            )
        self._product_id = product_id
        # self._is_food = is_food
        self._increment_version()

    @property
    def barcode(self) -> str | None:
        self._check_not_discarded()
        return self._barcode

    @property
    def is_barcode_unique(self) -> bool:
        self._check_not_discarded()
        try:
            return self._barcode is not None and len(str(int(self._barcode))) > 6
        except Exception:
            return False

    @property
    def cfe_key(self) -> str | None:
        self._check_not_discarded()
        return self._cfe_key

    @property
    def ids_of_products_with_similar_names(self) -> set[str] | None:
        self._check_not_discarded()
        return self._ids_of_products_with_similar_names

    @ids_of_products_with_similar_names.setter
    def ids_of_products_with_similar_names(self, value: set[str]) -> None:
        self._check_not_discarded()
        self._ids_of_products_with_similar_names = value
        self._increment_version()

    @property
    def is_food(self) -> bool | None:
        self._check_not_discarded()
        return self._is_food

    @is_food.setter
    def is_food(self, value: bool) -> None:
        self._check_not_discarded()
        if value == self._is_food or value is None:
            return
        self.check_rule(
            CanNotChangeIsFoodAttributeOfItemWithUniqueBarcode(
                product_id=self._product_id, is_barcode_unique=self.is_barcode_unique
            )
        )
        self._is_food = value
        self.events.append(
            ItemIsFoodChanged(
                house_id=self.house_id,
                item_id=self.id,
                barcode=self.barcode,
                is_food=value,
            )
        )
        self._increment_version()

    def delete(self) -> None:
        self._check_not_discarded()
        self._discard()
        self._increment_version()

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        if "is_food" in kwargs and "product_id" in kwargs:
            self.is_food = kwargs["is_food"]
            del kwargs["is_food"]
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<Item id={self.id} house_id={self.house_id} description={self.description}"
            f" amount={self.amount} is_food={self.is_food} price_per_unit={self.price_per_unit}"
            f" barcode={self.barcode} cfe_key={self.cfe_key} product_id={self.product_id}"
            f" ids_of_products_with_similar_names={self.ids_of_products_with_similar_names}"
            f" discarded={self.discarded} version={self.version}>"
        )
