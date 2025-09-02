from typing import Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating_fields import (
    RatingCommentOptional,
    RatingConvenienceRequired,
    RatingTasteRequired,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.rating_sa_model import (
    RatingSaModel,
)
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)


class ApiRating(BaseApiValueObject[Rating, RatingSaModel]):
    """
    A Pydantic model representing and validating user's ratings for a recipe.

    Enhanced with security validation to prevent injection attacks and data exposure.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (UUIDId): Unique identifier of the user who provided the rating.
        recipe_id (UUIDId): Unique identifier of the recipe being rated.
        taste (RatingTaste): Rating value for the taste of the recipe.
        convenience (RatingConvenience): Rating value for the convenience of
            preparing the recipe.
        comment (RatingComment): Comment about the recipe.
    """

    user_id: UUIDIdRequired
    recipe_id: UUIDIdRequired
    taste: RatingTasteRequired
    convenience: RatingConvenienceRequired
    comment: RatingCommentOptional

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
        return cls(
            user_id=orm_model.user_id,
            recipe_id=orm_model.recipe_id,
            taste=orm_model.taste,
            convenience=orm_model.convenience,
            comment=orm_model.comment,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Converts the instance to ORM model kwargs."""
        return {
            "user_id": self.user_id,
            "recipe_id": self.recipe_id,
            "taste": self.taste,
            "convenience": self.convenience,
            "comment": self.comment,
        }
