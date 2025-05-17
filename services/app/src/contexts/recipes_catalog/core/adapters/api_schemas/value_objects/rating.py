from typing import Optional

import cattrs
from attrs import asdict
from pydantic import BaseModel
from src.contexts.recipes_catalog.core.adapters.api_schemas.pydantic_validators import (
    RatingValue,
)
from src.contexts.recipes_catalog.core.domain.value_objects.rating import Rating


class ApiRating(BaseModel):
    """
    A Pydantic model representing and validating user's ratings for
    a recipe.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): Unique identifier of the user who provided the rating.
        recipe_id (str): Unique identifier of the recipe being rated.
        taste (RatingValue): Rating value for the taste of the recipe.
        convenience (RatingValue): Rating value for the convenience of
            preparing the recipe.
        comment (str, optional): An optional comment about the recipe.

    Methods:
        from_domain(domain_obj: Rating | None) -> Optional["ApiRating"]:
            Creates an instance of `ApiRating` from a domain model object.
            Returns `None` if `domain_obj` is `None`.
        to_domain() -> Rating:
            Converts the instance to a domain model object.

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.

    Example:
        Use `ApiRating` to represent user ratings in API responses or to parse
        user rating data received from API requests.
    """

    user_id: str
    recipe_id: str
    taste: RatingValue
    convenience: RatingValue
    comment: str | None = None

    @classmethod
    def from_domain(cls, domain_obj: Rating) -> "ApiRating":
        """Creates an instance of `ApiRating` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiRating from domain instance: {e}")

    def to_domain(self) -> Rating:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), Rating)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiRatingto domain model: {e}")
