# utils.py
from typing import TypeVar

from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification import (
    ClassificationSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    Classification,
)

_S = TypeVar("_S", bound=ClassificationSaModel)
_C = TypeVar("_C", bound=Classification)


def classification_map_domain_to_sa(
    domain_obj: Classification,
    sa_model_type: type[_S],
    polymorphic_identity: str,
) -> _S:
    return sa_model_type(
        type=polymorphic_identity,
        id=domain_obj.id,
        name=domain_obj.name,
        author_id=domain_obj.author_id,
        description=domain_obj.description,
        created_at=domain_obj.created_at,
        updated_at=domain_obj.updated_at,
        discarded=domain_obj.discarded,
        version=domain_obj.version,
    )


def classification_map_sa_to_domain(
    sa_obj: ClassificationSaModel,
    domain_obj_type: type[_C],
) -> _C:
    return domain_obj_type(
        entity_id=sa_obj.id,
        name=sa_obj.name,
        author_id=sa_obj.author_id,
        description=sa_obj.description,
        created_at=sa_obj.created_at,
        updated_at=sa_obj.updated_at,
        discarded=sa_obj.discarded,
        version=sa_obj.version,
    )
