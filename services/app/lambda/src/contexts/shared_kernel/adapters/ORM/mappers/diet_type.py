from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.diet_type import DietTypeSaModel
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.enums import Privacy


class DietTypeMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: DietType) -> DietTypeSaModel:
        return DietTypeSaModel(
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

    @staticmethod
    def map_sa_to_domain(sa_obj: DietTypeSaModel) -> DietType:
        return DietType(
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
