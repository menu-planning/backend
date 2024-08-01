from src.contexts.products_catalog.shared.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.shared.domain.entities.tags import Brand
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class BrandMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Brand) -> BrandSaModel:
        return BrandSaModel(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=domain_obj.author_id,
            description=domain_obj.description,
            created_at=domain_obj.created_at,
            updated_at=domain_obj.updated_at,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: BrandSaModel) -> Brand:
        return Brand(
            id=sa_obj.id,
            name=sa_obj.name,
            author_id=sa_obj.author_id,
            description=sa_obj.description,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
