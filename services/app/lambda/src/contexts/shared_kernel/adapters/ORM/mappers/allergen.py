from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.allergen import AllergenSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen


class AllergenMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Allergen) -> AllergenSaModel:
        return AllergenSaModel(
            id=domain_obj.name,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: AllergenSaModel) -> Allergen:
        return Allergen(
            name=sa_obj.id,
        )
