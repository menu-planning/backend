from typing import Any, Dict

from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import ClassificationSaModel
from src.contexts.products_catalog.core.domain.entities.classification import Category


class ApiCategory(ApiClassification):
    entity_type = Category
    entity_type_name = "category"