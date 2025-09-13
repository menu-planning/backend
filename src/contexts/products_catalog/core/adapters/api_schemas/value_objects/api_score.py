from typing import Any

from src.contexts.products_catalog.core.adapters.api_schemas.pydantic_validators import (
    ScoreValue,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ScoreSaModel,
)
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)


class ApiScore(BaseApiValueObject[Score, Any]):
    """API schema for product score value object.

    Attributes:
        final: The final score of the food item.
        ingredients: The ingredients score of the food item.
        nutrients: The nutrients score of the food item.
    """

    final: ScoreValue
    ingredients: ScoreValue
    nutrients: ScoreValue

    @classmethod
    def from_domain(cls, domain_obj: Score) -> "ApiScore":
        """Create API schema instance from domain object.

        Args:
            domain_obj: Domain score object.

        Returns:
            ApiScore instance or None if domain_obj is None.
        """
        if domain_obj is None:
            return None
        return cls(
            final=domain_obj.final,
            ingredients=domain_obj.ingredients,
            nutrients=domain_obj.nutrients,
        )

    def to_domain(self) -> Score:
        """Convert API schema to domain object.

        Returns:
            Score domain object.
        """
        return Score(
            final=self.final,
            ingredients=self.ingredients,
            nutrients=self.nutrients,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ScoreSaModel) -> "ApiScore":
        """Create API schema instance from ORM model.

        Args:
            orm_model: SQLAlchemy score model.

        Returns:
            ApiScore instance.
        """
        return cls(
            final=orm_model.final_score,
            ingredients=orm_model.ingredients_score,
            nutrients=orm_model.nutrients_score,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema to ORM model kwargs.

        Returns:
            Dictionary of kwargs for ORM model creation.
        """
        return {
            "final_score": self.final,
            "ingredients_score": self.ingredients,
            "nutrients_score": self.nutrients,
        }
