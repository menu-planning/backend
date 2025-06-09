from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)


class FoodGroupSaModel(ClassificationSaModel):
    __mapper_args__ = {
        "polymorphic_identity": "food_group",
    }
