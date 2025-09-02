"""SQLAlchemy model for process type classification."""
from typing import Any, ClassVar

from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)


class ProcessTypeSaModel(ClassificationSaModel):
    """SQLAlchemy model for process type classification.
    
    Inherits from ClassificationSaModel with process type-specific polymorphic identity.
    """
    __mapper_args__: ClassVar[dict[str, Any]] = {
        "polymorphic_identity": "process_type",
    }
