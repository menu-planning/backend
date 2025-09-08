"""SQLAlchemy model for parent category classification."""

from typing import Any, ClassVar

from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)


class ParentCategorySaModel(ClassificationSaModel):
    """SQLAlchemy model for parent category classification.

    Inherits from ClassificationSaModel with parent category-specific polymorphic identity.
    """

    __mapper_args__: ClassVar[dict[str, Any]] = {
        "polymorphic_identity": "parent_category",
    }
