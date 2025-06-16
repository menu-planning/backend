from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel
from src.db.base import SaBase
from datetime import date


class ApiProfile(BaseValueObject[Profile, SaBase]):
    """A class to represent and validate a profile."""

    name: str | None = None
    birthday: date | None = None
    sex: str | None = None

    @classmethod
    def from_domain(cls, domain_obj: Profile) -> "ApiProfile":
        """Creates an instance of `ApiProfile` from a domain model object."""
        return cls(
            name=domain_obj.name,
            birthday=domain_obj.birthday,
            sex=domain_obj.sex,
        )

    def to_domain(self) -> Profile:
        """Converts the instance to a domain model object."""
        return Profile(
            name=self.name,
            birthday=self.birthday,
            sex=self.sex,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ProfileSaModel) -> "ApiProfile":
        """Convert from ORM model."""
        return cls.model_validate(orm_model)

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return self.model_dump()
