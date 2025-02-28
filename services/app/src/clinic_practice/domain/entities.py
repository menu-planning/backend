from __future__ import annotations

import logging
import uuid

from src.contexts.nutrition_assessment_and_planning.modules.common.value_objects import (
    Contact,
    Email,
    FullName,
)
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.logging.logger import logger

from .events import (
    NutritionistAcceptedHouseInvitation,
    NutritionistCreated,
    NutritionistDeclinedHouseInvitation,
    NutritionistLeftHouse,
    PatientLinkedUser,
    PatientUnlinkedUser,
)
from .exceptions import (
    AlreadyMemberOfHouseError,
    HouseNotFoundError,
    NotMemberOfHouseError,
    PatientAlreadyLinkedError,
    PatientNotFoundError,
)
from .value_objects import CRN, BrandNotes, ProductNotes


class Nutritionist(Entity):
    def __init__(
        self,
        id: str,
        user_id: str,
        user_name: str,
        email: Email,
        contact: Contact,
        full_name: FullName | None = None,
        crn: CRN | None = None,
        patients: set[_Patient] | None = None,
        houses: set[str] | None = None,
        house_invitations: set[str] | None = None,
        products_notes: dict[str, ProductNotes] | None = None,
        brands_notes: dict[str, BrandNotes] | None = None,
        avatar_url: str | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Nutritionist."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._user_id = user_id
        self._user_name = user_name
        self._email = email
        self._crn = crn
        self._contact = contact
        self._full_name = full_name
        self._patients = patients or {}
        self._houses = houses or set()
        self._house_invitations = house_invitations or set()
        self._products_notes = products_notes or {}
        self._brands_notes = brands_notes or {}
        self._avatar_url = avatar_url
        self.events: list[Event] = []

    @classmethod
    def create_nutritionist(
        cls,
        user_id: str,
        user_name: str,
        email: Email,
    ) -> Nutritionist:
        event = NutritionistCreated(
            user_id=user_id,
        )
        user = cls(
            id=event.nutritionist_id,
            user_id=user_id,
            user_name=user_name,
            email=email,
            contact=Contact(default_email=email),
        )
        user.events.append(event)
        return user

    def _update_properties(self, **kwargs) -> None:
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        allowed_properties = ["contact", "crn", "avatar_url"]
        if not all(key in allowed_properties for key in kwargs.keys()):
            raise ValueError(
                f"Properties {kwargs.keys()} not allowed. "
                f"Allowed properties are {allowed_properties}"
            )
        else:
            self._update_properties(**kwargs)

    @property
    def user_id(self) -> str:
        self._check_not_discarded()
        return self._user_id

    @property
    def user_name(self) -> str:
        self._check_not_discarded()
        return self._user_name

    @property
    def email(self) -> Email:
        self._check_not_discarded()
        return self._email

    @property
    def crn(self) -> CRN:
        self._check_not_discarded()
        return self._crn

    @crn.setter
    def crn(self, value: CRN) -> None:
        self._check_not_discarded()
        self._crn = value
        self._increment_version()

    @property
    def full_name(self) -> FullName:
        self._check_not_discarded()
        return self._full_name

    @full_name.setter
    def full_name(self, value: FullName) -> None:
        self._check_not_discarded()
        self._full_name = value
        self._increment_version()

    @property
    def contact(self) -> Contact:
        self._check_not_discarded()
        return self._contact

    @contact.setter
    def contact(self, value: Contact) -> None:
        self._check_not_discarded()
        self._contact = value
        self._increment_version()

    @property
    def avatar_url(self):
        self._check_not_discarded()
        return self._avatar_url

    @avatar_url.setter
    def avatar_url(self, value: str) -> None:
        self._check_not_discarded()
        self._avatar_url = value
        self._increment_version()

    @property
    def houses(self) -> set[str]:
        self._check_not_discarded()
        return self._houses

    @property
    def house_invitations(self) -> set[str]:
        self._check_not_discarded()
        return self._house_invitations

    def add_house_invitation(self, house_id: str) -> None:
        self._check_not_discarded()
        self._house_invitations.add(house_id)
        self._increment_version()

    def accept_house_invitation(self, house_id: str) -> None:
        self._check_not_discarded()
        self._manage_house_invitation(house_id, True)

    def decline_house_invitation(self, house_id: str) -> None:
        self._check_not_discarded()
        self._manage_house_invitation(house_id, False)

    def _manage_house_invitation(
        self,
        house_id: str,
        response: bool,
    ) -> None:
        if house_id in self._houses:
            raise AlreadyMemberOfHouseError(
                f"Nutritionist {self.id} is already in house {house_id}"
            )
        if house_id not in self._house_invitations:
            raise HouseNotFoundError(
                f"House invitation from house {house_id} not found"
            )
        if response:
            event = NutritionistAcceptedHouseInvitation(
                house_id=house_id,
                user_id=self.id,
            )
            self._houses.add(house_id)
        else:
            event = NutritionistDeclinedHouseInvitation(
                house_id=house_id,
                user_id=self.id,
            )
        self._house_invitations.discard(house_id)
        self.events.append(event)
        self._increment_version()

    def leave_house(self, house_id: str) -> None:
        self._check_not_discarded()
        try:
            self._houses.remove(house_id)
            event = NutritionistLeftHouse(
                house_id=house_id,
                nutritionist_id=self.id,
            )
            self.events.append(event)
            self._increment_version()
        except KeyError:
            raise NotMemberOfHouseError(
                f"Nutritionist {self.id} is not a member of house {house_id}"
            )

    @property
    def patients(self) -> set[_Patient]:
        self._check_not_discarded()
        return self._patients

    def patient(self, patient_id: str) -> _Patient:
        self._check_not_discarded()
        return next(p for p in self._patients if p.id == patient_id)

    def update_patient_properties(self, patient_id: str, **kwargs) -> None:
        self._check_not_discarded
        patient = self.patient(patient_id)
        patient._update_properties(**kwargs)
        self._increment_version()

    def add_patient(
        self,
        contact: Contact,
    ) -> None:
        self._check_not_discarded()
        patient_id = uuid.uuid4().hex
        patient = _Patient.create_patient(
            id=patient_id,
            contact=contact,
        )
        self._patients.add(patient)
        self._increment_version()

    def delete_patient(self, patient: _Patient) -> None:
        self._check_not_discarded()
        if self.patient(patient.id) is None:
            raise PatientNotFoundError(f"Patient {patient.id} not found")
        patient._unlink_user()
        self._patients.discard(patient)
        event = PatientUnlinkedUser(
            nutritionist_id=self.id,
            patient_id=patient.id,
            user_id=patient._user_id,
        )
        self.events.append(event)
        self._increment_version()

    def link_patient(
        self,
        patient_id: str,
        user_id: str,
    ) -> None:
        self._check_not_discarded()
        event = PatientLinkedUser(
            nutritionist_id=self.id,
            patient_id=patient_id,
            user_id=user_id,
        )
        patient = self.patient(patient_id)
        patient._link_user(self, user_id)
        self.events.append(event)
        self._increment_version()

    def unlink_patient(self, patient_id: str) -> None:
        self._check_not_discarded()
        patient = self.patient(patient_id)
        patient._unlink_user()
        event = PatientUnlinkedUser(
            nutritionist_id=self.id,
            patient_id=patient.id,
            user_id=patient._user_id,
        )
        self.events.append(event)
        self._increment_version()

    @property
    def products_notes(
        self,
    ) -> dict[str, ProductNotes]:
        self._check_not_discarded()
        return self._products_notes

    def product_notes(self, product_id: str) -> ProductNotes:
        self._check_not_discarded()
        return self._products_notes.get(product_id, None)

    def edit_product_notes(self, product_id: str, notes: ProductNotes) -> None:
        self._check_not_discarded()
        self._update_notes(product_id=product_id, notes=notes.notes, like=notes.like)

    @property
    def brands_notes(self) -> dict[str, BrandNotes]:
        self._check_not_discarded()
        return self._brands_notes

    def brand_notes(self, brand):
        self._check_not_discarded()
        return self._brands_notes.get(brand, None)

    def edit_brand_notes(self, brand: str, notes: BrandNotes) -> None:
        self._check_not_discarded()
        self._update_notes(brand=brand, notes=notes.notes, like=notes.like)

    def _update_notes(self, **kwargs) -> None:
        self._check_not_discarded()
        product_id = kwargs.get("product_id", None)
        brand = kwargs.get("brand", None)
        if "product_id" in kwargs:
            del kwargs["product_id"]
            notes = self._products_notes.get(
                product_id,
                ProductNotes(
                    product_id=product_id,
                ),
            )
            notes = notes.replace(**kwargs)
            self._products_notes |= {product_id: notes}
        elif "brand" in kwargs:
            del kwargs["brand"]
            notes = self._brands_notes.get(
                brand,
                BrandNotes(
                    brand=brand,
                ),
            )
            notes = notes.replace(**kwargs)
            self._brands_notes |= {brand: notes}
        self._increment_version()

    def edit_patient_product_notes(
        self,
        patient_id: str,
        product_id: str,
        notes: ProductNotes,
    ) -> None:
        self._check_not_discarded()
        patient = self.patient(patient_id)
        patient._edit_product_notes(product_id, notes)

    def edit_patient_brand_notes(
        self,
        patient_id: str,
        brand: str,
        notes: BrandNotes,
    ) -> None:
        self._check_not_discarded()
        patient = self.patient(patient_id)
        patient._edit_brand_notes(brand, notes)

    def __repr__(self):
        return "{}{}(id={})".format(
            "*Discarded* " if self._discarded else "",
            self.__class__.__name__,
            self._id,
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Nutritionist) and self.id == __o.id


class _Patient(Entity):
    def __init__(
        self,
        id: str,
        contact: Contact,
        full_name: FullName | None = None,
        house: str | None = None,
        pending_user_link: str | None = None,
        products_notes: dict[str, ProductNotes] | None = None,
        brands_notes: dict[str, BrandNotes] | None = None,
        avatar_url: str | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Patient."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._contact = contact
        self._full_name = full_name
        self._house = house
        self._pending_user_link = pending_user_link or set()
        self._products_notes = products_notes or {}
        self._brands_notes = brands_notes or {}
        self._avatar_url = avatar_url
        self._user_id = None

    @classmethod
    def create_patient(
        cls,
        contact: Contact,
    ) -> _Patient:
        """Create a new Patient."""
        patient_id = uuid.uuid4().hex
        patient = cls(
            id=patient_id,
            contact=contact,
        )
        return patient

    def _update_properties(self, **kwargs) -> None:
        allowed_properties = ["contact", "crn", "avatar_url"]
        if not all(key in allowed_properties for key in kwargs.keys()):
            raise ValueError(
                f"Properties {kwargs.keys()} not allowed. "
                f"Allowed properties are {allowed_properties}"
            )
        else:
            super()._update_properties(**kwargs)

    @property
    def full_name(self) -> FullName:
        self._check_not_discarded()
        return self._full_name

    @property
    def house(self) -> FullName:
        self._check_not_discarded()
        return self._house

    @property
    def contact(self) -> Contact:
        self._check_not_discarded()
        return self._contact

    @property
    def avatar_url(self) -> str:
        self._check_not_discarded()
        return self._avatar_url

    def _link_user(self, nutritionist: Nutritionist, user_id: str) -> None:
        self._check_not_discarded()
        if user_id == self._pending_user_link:
            return
        if self._pending_user_link is not None:
            raise PatientAlreadyLinkedError(
                f"Patient {self.id} is already linked to user {self._pending_user_link}"
            )
        event = PatientLinkedUser(
            nutritionist_id=nutritionist.id,
            patient_id=self.id,
            user_id=user_id,
        )
        self._pending_user_link = user_id
        nutritionist.events.append(event)
        self._increment_version()

    def _unlink_user(self) -> None:
        self._check_not_discarded()
        if self._pending_user_link is None:
            return
        self._pending_user_link = None
        self._increment_version()

    @property
    def products_notes(
        self,
    ) -> dict[str, ProductNotes]:
        self._check_not_discarded()
        return self._products_notes

    def product_notes(self, product_id: str) -> ProductNotes:
        self._check_not_discarded()
        return self._products_notes.get(product_id, None)

    def _edit_product_notes(self, product_id: str, notes: ProductNotes) -> None:
        self._check_not_discarded()
        self._update_notes(product_id=product_id, notes=notes.notes, like=notes.like)

    @property
    def brands_notes(self) -> dict[str, BrandNotes]:
        self._check_not_discarded()
        return self._brands_notes

    def brand_notes(self, brand):
        self._check_not_discarded()
        return self._brands_notes.get(brand, None)

    def _edit_brand_notes(self, brand: str, notes: BrandNotes) -> None:
        self._check_not_discarded()
        self._update_notes(brand=brand, notes=notes.notes, like=notes.like)

    def _update_notes(self, **kwargs) -> None:
        self._check_not_discarded()
        product_id = kwargs.get("product_id", None)
        brand = kwargs.get("brand", None)
        if "product_id" in kwargs:
            del kwargs["product_id"]
            notes = self._products_notes.get(
                product_id,
                ProductNotes(
                    product_id=product_id,
                ),
            )
            notes = notes.replace(**kwargs)
            self._products_notes |= {product_id: notes}
        elif "brand" in kwargs:
            del kwargs["brand"]
            notes = self._brands_notes.get(
                brand,
                BrandNotes(
                    brand=brand,
                ),
            )
            notes = notes.replace(**kwargs)
            self._brands_notes |= {brand: notes}
        self._increment_version()

    def __repr__(self):
        return "{}{}(id={})".format(
            "*Discarded* " if self._discarded else "",
            self.__class__.__name__,
            self._id,
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, _Patient) and self.id == __o.id
