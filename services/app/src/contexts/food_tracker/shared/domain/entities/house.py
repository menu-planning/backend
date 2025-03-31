import uuid
from collections.abc import Mapping

from attrs import asdict
from src.contexts.food_tracker.shared.domain.events.events import (
    MemberInvited,
    NutritionistInvited,
    ReceiptCreated,
)
from src.contexts.food_tracker.shared.domain.value_objects.receipt import Receipt
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event


class House(Entity):
    def __init__(
        self,
        *,
        id: str,
        owner_id: str,
        name: str,
        members_ids: set[str] | None = None,
        nutritionists_ids: set[str] | None = None,
        pending_receipts: set[Receipt] | None = None,
        added_receipts: set[Receipt] | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new House."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._owner_id = owner_id
        self._name = name
        self._members_ids = members_ids or set()
        self._nutritionists_ids = nutritionists_ids or set()
        self._pending_receipts = pending_receipts or set()
        self._added_receipts = added_receipts or set()
        self.events: list[Event] = []

    @classmethod
    def create_house(
        cls,
        *,
        owner_id: str,
        name: str,
        members_ids: set[str] | None = None,
        nutritionists_ids: set[str] | None = None,
        pending_receipts: set[Receipt] | None = None,
        added_receipts: set[Receipt] | None = None,
    ) -> "House":
        house_id = uuid.uuid4().hex
        house = cls(
            id=house_id,
            owner_id=owner_id,
            name=name,
            members_ids=members_ids,
            nutritionists_ids=nutritionists_ids,
            pending_receipts=pending_receipts,
            added_receipts=added_receipts,
        )
        return house


    @property
    def owner_id(self) -> str:
        self._check_not_discarded()
        return self._owner_id

    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._check_not_discarded()
        self._name = name
        self._increment_version()

    @property
    def members_ids(self) -> set[str]:
        self._check_not_discarded()
        return self._members_ids

    def invite_member(self, member_id: str) -> None:
        self._check_not_discarded()
        if member_id not in self._members_ids:
            self._members_ids.add(member_id)
            self._increment_version()
            self.events.append(MemberInvited(house_id=self.id, member_id=member_id))

    def remove_member(self, member_id: str) -> None:
        self._check_not_discarded()
        if member_id in self._members_ids:
            self._members_ids.remove(member_id)
            self._increment_version()

    @property
    def nutritionists_ids(self) -> set[str]:
        self._check_not_discarded()
        return self._nutritionists_ids

    def invite_nutritionist(self, nutritionist_id: str) -> None:
        self._check_not_discarded()
        if nutritionist_id not in self._nutritionists_ids:
            self._nutritionists_ids.add(nutritionist_id)
            self._increment_version()
            self.events.append(
                NutritionistInvited(house_id=self.id, nutritionist_id=nutritionist_id)
            )

    def remove_nutritionist(self, nutritionist_id: str) -> None:
        self._check_not_discarded()
        if nutritionist_id in self._nutritionists_ids:
            self._nutritionists_ids.remove(nutritionist_id)
            self._increment_version()

    @property
    def pending_receipts(self) -> set[Receipt]:
        self._check_not_discarded()
        return self._pending_receipts

    def add_receipt(self, receipt: Receipt) -> None:
        self._check_not_discarded()
        if (
            receipt not in self._pending_receipts
            and receipt not in self._added_receipts
        ):
            self._pending_receipts.add(receipt)
            self.events.append(
                ReceiptCreated(
                    house_id=self.id, cfe_key=receipt.cfe_key, qrcode=receipt.qrcode
                )
            )
            self._increment_version()

    def remove_pending_receipt(self, cfe_key: str) -> None:
        self._check_not_discarded()
        try:
            receipt = next(i for i in self._pending_receipts if i.cfe_key == cfe_key)
            self._pending_receipts.discard(receipt)
            self._increment_version()
        except StopIteration:
            pass

    @property
    def added_receipts(self) -> set[Receipt]:
        self._check_not_discarded()
        return self._added_receipts

    def remove_added_receipt(self, cfe_key: str) -> None:
        self._check_not_discarded()
        try:
            receipt = next(i for i in self._added_receipts if i.cfe_key == cfe_key)
            self._added_receipts.discard(receipt)
            self._increment_version()
        except StopIteration:
            pass

    def move_receipt_from_pending_to_added(self, cfe_key: str) -> None:
        self._check_not_discarded()
        try:
            receipt = next(i for i in self._pending_receipts if i.cfe_key == cfe_key)
            self._pending_receipts.discard(receipt)
            self._added_receipts.add(receipt)
            self._increment_version()
        except StopIteration:
            pass

    def delete(self) -> None:
        self._check_not_discarded()
        self._discard()
        self._increment_version()

    def __repr__(self) -> str:
        self._check_not_discarded()
        return f"{self.__class__.__name__}" f"(id={self.id!r})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, House):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)
