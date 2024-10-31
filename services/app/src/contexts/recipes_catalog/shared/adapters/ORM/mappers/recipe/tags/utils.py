from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.tags.base_class import (
    TagSaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags.base_classes import Tag
from src.contexts.shared_kernel.domain.enums import Privacy
from src.db.base import SaBase


def tag_map_domain_to_sa(
    domain_obj: Tag, sa_model_type: type[TagSaModel], polymorphic_identity=str
) -> SaBase:
    return sa_model_type(
        type=polymorphic_identity,
        id=domain_obj.id,
        name=domain_obj.name,
        author_id=domain_obj.author_id,
        description=domain_obj.description,
        privacy=domain_obj.privacy.value,
        created_at=domain_obj.created_at,
        updated_at=domain_obj.updated_at,
        discarded=domain_obj.discarded,
        version=domain_obj.version,
    )


def tag_map_sa_to_domain(sa_obj: TagSaModel, domain_obj_type: type[Tag]) -> Tag:
    return domain_obj_type(
        id=sa_obj.id,
        name=sa_obj.name,
        author_id=sa_obj.author_id,
        description=sa_obj.description,
        privacy=Privacy(sa_obj.privacy),
        created_at=sa_obj.created_at,
        updated_at=sa_obj.updated_at,
        discarded=sa_obj.discarded,
        version=sa_obj.version,
    )
