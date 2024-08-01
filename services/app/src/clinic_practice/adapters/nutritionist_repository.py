from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    SaGenericRepository,
)

from ..domain.entities import Nutritionist
from .mappers import NutritionistMapper
from .sa_models import NutritionistSaModel


class NutritionistRepo(CompositeRepository[Nutritionist, NutritionistSaModel]):
    allowed_filters = {
        "login_email",
        "first_name",
        "last_name",
        "crn_number",
    }

    def __init__(
        self,
        db_session: Session,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            self._session,
            NutritionistMapper(),
            Nutritionist,
            NutritionistSaModel,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    def add(self, entity: Nutritionist):
        self._generic_repo.add(entity)

    def get(self, id: str) -> Nutritionist:
        return self._generic_repo.get(id)

    def get_sa_instance(self, id: str) -> NutritionistSaModel:
        return self._generic_repo.get_sa_instance(id)

    def get_by_email(
        self, email: str, return_sa_model: bool = False
    ) -> None | NutritionistSaModel | Nutritionist:
        stmt = select(NutritionistSaModel).filter_by(login_email=email)
        result = self._session.execute(stmt).first()
        if result:
            if return_sa_model:
                return result[0]
            else:
                domain_obj = self.data_mapper.map_sa_to_domain(result[0])
                if domain_obj:
                    self.seen.add(domain_obj)
                return domain_obj
        else:
            return None

    def get_sa_model_by_email(self, email: str) -> NutritionistSaModel:
        return self.get_by_email(email, _return_sa_model=True)

    def query(self, filter: dict[str, Any]) -> list[Nutritionist]:
        return self._generic_repo.query(filter)

    def persist(self, domain_obj: Nutritionist) -> None:
        self._generic_repo.persist(domain_obj)

    def persist_all(self) -> None:
        self._generic_repo.persist_all()
