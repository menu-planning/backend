from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.base_class import (
    ClassificationSaModel,
)


class CategorySaModel(ClassificationSaModel):
    __mapper_args__ = {
        "polymorphic_identity": "category",
    }
