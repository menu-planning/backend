from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from src.contexts._receipt_tracker.shared.domain.enums import CfeStateCodes, State
from src.contexts._receipt_tracker.shared.domain.events import (
    ItemsAddedToReceipt,
    ProductsAddedToItems,
    ReceiptAdded,
)
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts._receipt_tracker.shared.domain.value_objects.product import Product
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.seedwork.shared.endpoints.exceptions import (
    BadRequestException,
    InvalidApiSchemaException,
)


class Receipt(Entity):
    """A class representing a receipt."""

    state_mapping: ClassVar[dict[str, str]] = {State.SP: "35"}

    def __init__(
        self,
        *,
        cfe_key: str,
        house_ids: list[str],
        qrcode: str | None = None,
        date: datetime | None = None,
        state: str | None = None,
        seller_id: str | None = None,
        scraped: bool = False,
        products_added: bool = False,
        items: list[Item] | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Receipt."""
        super().__init__(id=cfe_key, discarded=discarded, version=version)
        self._house_ids = house_ids
        self._date = date
        self._state = state
        self._id = cfe_key
        self._seller_id = seller_id
        self._qrcode = qrcode
        self._scraped = scraped
        self._products_added = products_added
        self._items = items or []
        self.events: list[Event] = []

    @classmethod
    def add_receipt(
        cls,
        *,
        cfe_key: str,
        house_ids: list[str],
        qrcode: str | None = None,
        date: datetime | None = None,
        seller_id: str | None = None,
        scraped: bool = False,
        products_added: bool = False,
        items: list[Item] | None = None,
    ) -> Receipt:
        if len(cfe_key) != 44:
            raise InvalidApiSchemaException(
                f"Cfe key must have 44 digits. Got {len(cfe_key)}"
            )
        try:
            state_code = int(str(int(cfe_key))[:2])
        except ValueError as e:
            raise InvalidApiSchemaException(
                f"Cfe key must contain only numbers. cfe_key={cfe_key}"
            ) from e
        try:
            state_name = CfeStateCodes(state_code).name
        except ValueError as e:
            raise InvalidApiSchemaException(
                f"There is no state with receipt code={state_code}."
            ) from e
        if int(cfe_key[:2]) not in [p.value for p in CfeStateCodes]:
            raise InvalidApiSchemaException(f"Unknown state: {cfe_key}")
        event = ReceiptAdded(
            house_ids=house_ids if isinstance(house_ids, list) else [house_ids],
            state=state_name,
            cfe_key=cfe_key,
            qrcode=qrcode,
        )
        receipt = cls(
            house_ids=event.house_ids,
            cfe_key=event.cfe_key,
            state=event.state,
            qrcode=event.qrcode,
            date=date,
            seller_id=seller_id,
            scraped=scraped,
            products_added=products_added,
            items=items,
        )
        receipt.events.append(event)
        return receipt

    @property
    def house_ids(self) -> list[str]:
        self._check_not_discarded()
        return self._house_ids

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

    @property
    def date(self) -> datetime:
        self._check_not_discarded()
        return self._date

    @date.setter
    def date(self, value) -> None:
        self._check_not_discarded()
        if isinstance(value, datetime) and value != self._date:
            self._date = value
            self._increment_version()

    @property
    def state(self) -> str | None:
        self._check_not_discarded()
        return self._state

    @state.setter
    def state(self, value) -> None:
        self._check_not_discarded()
        if self._state:
            raise BadRequestException("Cannot change state of a receipt with a state")
        self._state = value
        self._increment_version()

    @property
    def qrcode(self) -> str | None:
        self._check_not_discarded()
        return self._qrcode

    @qrcode.setter
    def qrcode(self, value) -> None:
        self._check_not_discarded()
        if self._qrcode:
            raise BadRequestException("Cannot change qrcode of a receipt with a qrcode")
        self._qrcode = value
        self._increment_version()

    @property
    def scraped(self) -> bool:
        self._check_not_discarded()
        return self._scraped

    @scraped.setter
    def scraped(self, value) -> None:
        self._check_not_discarded()
        if value != self._scraped:
            self._scraped = value
            self._increment_version()

    @property
    def products_added(self) -> bool:
        self._check_not_discarded()
        return self._products_added

    # @products_added.setter
    # def products_added(self, value) -> None:
    #     self._check_not_discarded()
    #     if value != self._products_added:
    #         self._products_added = value
    #         self._increment_version()

    @property
    def seller_id(self) -> str | None:
        self._check_not_discarded()
        return self._seller_id

    @seller_id.setter
    def seller_id(self, value) -> None:
        self._check_not_discarded()
        if value != self._seller_id:
            self._seller_id = value
            self._increment_version()

    @property
    def items(self) -> list[Item]:
        self._check_not_discarded()
        return self._items

    def _add_item(
        self,
        item: Item,
    ) -> None:
        if not item.number:
            item = item.replace(number=len(self._items) + 1)
        self._items.append(item)

    def add_items(self, items: list[Item]) -> None:
        self._check_not_discarded()
        new_items = []
        for item in items:
            if item.number not in [i.number for i in self._items]:
                new_items.append(item)
        for item in new_items:
            self._add_item(item)
        if not self._scraped:
            event = ItemsAddedToReceipt(cfe_key=self._id)
            self.events.append(event)
            self._scraped = True
        self._increment_version()

    def add_products_to_items(
        self, barcode_product_mapping: dict[str, Product]
    ) -> None:
        self._check_not_discarded()
        new_items = []
        for item in self._items:
            new_item = item
            product = barcode_product_mapping.get(item.barcode)
            if product and product != item.product:
                new_item = item.replace(product=product)
            new_items.append(new_item)
        self._items = new_items
        if not self._products_added:
            event = ProductsAddedToItems(
                cfe_key=self.id,
            )
            self.events.append(event)
            self._products_added = True
        self._increment_version()

    def consolidate_items(self) -> list[Item]:
        self._check_not_discarded()
        result = {}
        for item in self._items:
            if item.barcode in result:
                result[item.barcode] += item
            else:
                result[item.barcode] = item
        return list(result.values())

    def add_house(self, house_id: str):
        self._check_not_discarded()
        if house_id not in self._house_ids:
            self._house_ids.append(house_id)
            self._increment_version()

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._id}, house_id={self._house_ids}, version={self._version})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Receipt) and self._id == __o._id

    def _update_properties(self, **kwargs) -> None:
        return NotImplemented
