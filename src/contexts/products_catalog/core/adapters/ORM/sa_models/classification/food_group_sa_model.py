"""SQLAlchemy model for food group classification."""

from typing import Any, ClassVar

from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)


class FoodGroupSaModel(ClassificationSaModel):
    """SQLAlchemy model for food group classification.

    Inherits from ClassificationSaModel with food group-specific polymorphic identity.
    """

    __mapper_args__: ClassVar[dict[str, Any]] = {
        "polymorphic_identity": "food_group",
    }
