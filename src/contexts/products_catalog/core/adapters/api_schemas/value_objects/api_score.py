from typing import Any, Dict

from src.contexts.products_catalog.core.adapters.api_schemas.pydantic_validators import (
    ScoreValue,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ScoreSaModel,
)
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)


class ApiScore(BaseApiValueObject[Score, Any]):
    """
    A Pydantic model representing and validating the score of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        final (ScoreValue): The final score of the food item, which is an
            instance of the `ScoreValue` class defined in the codebase.

        ingredients (ScoreValue): The ingredients score of the food item,
            which is an instance of the `ScoreValue` class defined in the
            codebase.

        nutrients (ScoreValue): The nutrients score of the food item, which
            is an instance of the `ScoreValue` class defined in the codebase.
    """

    final: ScoreValue
    ingredients: ScoreValue
    nutrients: ScoreValue

    @classmethod
    def from_domain(cls, domain_obj: Score) -> "ApiScore":
        """Creates an instance of `ApiScore` from a domain model object."""
        if domain_obj is None:
            return None
        return cls(
            final=domain_obj.final,
            ingredients=domain_obj.ingredients,
            nutrients=domain_obj.nutrients,
        )

    def to_domain(self) -> Score:
        """Converts the instance to a domain model object."""
        return Score(
            final=self.final,
            ingredients=self.ingredients,
            nutrients=self.nutrients,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ScoreSaModel) -> "ApiScore":
        """Creates an instance of `ApiScore` from an ORM model."""
        return cls(
            final=orm_model.final_score,
            ingredients=orm_model.ingredients_score,
            nutrients=orm_model.nutrients_score,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Converts the instance to ORM model kwargs."""
        return {
            "final_score": self.final,
            "ingredients_score": self.ingredients,
            "nutrients_score": self.nutrients,
        }
