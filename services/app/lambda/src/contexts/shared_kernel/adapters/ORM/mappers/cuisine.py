from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.cuisine import CuisineSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine


class CuisineMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Cuisine) -> CuisineSaModel:
        return CuisineSaModel(
            id=domain_obj.name,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: CuisineSaModel) -> Cuisine:
        return Cuisine(
            name=sa_obj.id,
        )
