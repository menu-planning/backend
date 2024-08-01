from typing import Optional

import cattrs
from attrs import asdict
from pydantic import BaseModel
from src.contexts.products_catalog.shared.adapters.api_schemas.pydantic_validators import (
    ScoreValue,
)
from src.contexts.products_catalog.shared.domain.value_objects.score import Score


class ApiScore(BaseModel):
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

    Methods:
        from_domain(domain_obj: Score | None) -> Optional["ApiScore"]:
            Creates an instance of `ApiScore` from a domain model object.
        to_domain() -> Score:
            Converts the instance to a domain model object.

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.
    """

    final: ScoreValue
    ingredients: ScoreValue
    nutrients: ScoreValue

    @classmethod
    def from_domain(cls, domain_obj: Score) -> Optional["ApiScore"]:
        """Creates an instance of `ApiScore` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiScore from domain instance: {e}")

    def to_domain(self) -> Score:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), Score)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiScore to domain model: {e}")
