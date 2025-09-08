"""SQLAlchemy model for category classification."""

from typing import Any, ClassVar

from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)


class CategorySaModel(ClassificationSaModel):
    """SQLAlchemy model for category classification.

    Inherits from ClassificationSaModel with category-specific polymorphic identity.
    """

    __mapper_args__: ClassVar[dict[str, Any]] = {
        "polymorphic_identity": "category",
    }
