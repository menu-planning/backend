from typing import Optional, Dict, Any

from pydantic import Field, TypeAdapter

from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.fields import RatingValue
from src.contexts.recipes_catalog.core.domain.value_objects.rating import Rating
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.recipe.rating import RatingSaModel


class ApiRating(BaseValueObject[Rating, RatingSaModel]):
    """
    A Pydantic model representing and validating user's ratings for a recipe.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): Unique identifier of the user who provided the rating.
        recipe_id (str): Unique identifier of the recipe being rated.
        taste (RatingValue): Rating value for the taste of the recipe.
        convenience (RatingValue): Rating value for the convenience of
            preparing the recipe.
        comment (str, optional): An optional comment about the recipe.
    """

    user_id: str = Field(..., min_length=1)
    recipe_id: str = Field(..., min_length=1)
    taste: RatingValue
    convenience: RatingValue
    comment: Optional[str] = Field(default=None)

    @classmethod
    def from_domain(cls, domain_obj: Rating) -> "ApiRating":
        """Creates an instance of `ApiRating` from a domain model object."""
        return cls(
            user_id=domain_obj.user_id,
            recipe_id=domain_obj.recipe_id,
            taste=domain_obj.taste,
            convenience=domain_obj.convenience,
            comment=domain_obj.comment,
        )

    def to_domain(self) -> Rating:
        """Converts the instance to a domain model object."""
        return Rating(
            user_id=self.user_id,
            recipe_id=self.recipe_id,
            taste=self.taste,
            convenience=self.convenience,
            comment=self.comment,
        )

    @classmethod
    def from_orm_model(cls, orm_model: RatingSaModel) -> "ApiRating":
        """Creates an instance of `ApiRating` from an ORM model."""
        if orm_model is None:
            return None
        return cls(
            user_id=orm_model.user_id,
            recipe_id=orm_model.recipe_id,
            taste=orm_model.taste,
            convenience=orm_model.convenience,
            comment=orm_model.comment,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Converts the instance to ORM model kwargs."""
        return {
            "user_id": self.user_id,
            "recipe_id": self.recipe_id,
            "taste": self.taste,
            "convenience": self.convenience,
            "comment": self.comment,
        }

RatingListAdapter = TypeAdapter(list[ApiRating])