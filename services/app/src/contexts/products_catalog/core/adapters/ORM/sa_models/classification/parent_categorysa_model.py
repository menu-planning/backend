from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)


class ParentCategorySaModel(ClassificationSaModel):
    __mapper_args__ = {
        "polymorphic_identity": "parent_category",
    }
