from src.contexts.products_catalog.shared.adapters.ORM.sa_models.classification.base_class import (
    ClassificationSaModel,
)


class FoodGroupSaModel(ClassificationSaModel):
    __mapper_args__ = {
        "polymorphic_identity": "food_group",
    }
