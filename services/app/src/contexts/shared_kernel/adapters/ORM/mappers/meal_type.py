from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.meal_type import MealTypeSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.meal_type import MealType


class MealTypeMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: MealType) -> MealTypeSaModel:
        return MealTypeSaModel(
            id=domain_obj.name,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: MealTypeSaModel) -> MealType:
        return MealType(
            name=sa_obj.id,
        )
