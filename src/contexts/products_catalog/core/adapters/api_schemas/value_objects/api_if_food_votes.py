from typing import Any

from pydantic import Field
from src.contexts.products_catalog.core.adapters.ORM.sa_models.is_food_votes import (
    IsFoodVotesSaModel,
)
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)


class ApiIsFoodVotes(BaseApiValueObject[IsFoodVotes, IsFoodVotesSaModel]):
    """API schema for is_food_votes value object.

    Attributes:
        acceptance_line: The acceptance line configuration that determines voting thresholds.
        is_food_houses: Set of house IDs that voted this product as food.
        is_not_food_houses: Set of house IDs that voted this product as not food.
    """

    acceptance_line: dict[float, float | None] = Field(default_factory=dict)
    is_food_houses: set[str] = Field(default_factory=set)
    is_not_food_houses: set[str] = Field(default_factory=set)

    @classmethod
    def from_domain(cls, domain_obj: IsFoodVotes) -> "ApiIsFoodVotes":
        """Create API schema instance from domain object.

        Args:
            domain_obj: Domain is_food_votes object.

        Returns:
            ApiIsFoodVotes instance or None if domain_obj is None.
        """
        if domain_obj is None:
            return None
        return cls(
            acceptance_line=domain_obj.acceptance_line or {},
            is_food_houses=set(domain_obj.is_food_houses),
            is_not_food_houses=set(domain_obj.is_not_food_houses),
        )

    def to_domain(self) -> IsFoodVotes:
        """Convert API schema to domain object.

        Returns:
            IsFoodVotes domain object.
        """
        return IsFoodVotes(
            acceptance_line=self.acceptance_line,
            is_food_houses=frozenset(self.is_food_houses),
            is_not_food_houses=frozenset(self.is_not_food_houses),
        )

    @classmethod
    def from_orm_model(cls, orm_models: list[IsFoodVotesSaModel]) -> "ApiIsFoodVotes":
        """Create API schema instance from list of ORM models.

        Args:
            orm_models: List of IsFoodVotesSaModel instances representing individual votes.

        Returns:
            ApiIsFoodVotes instance with aggregated vote data.
        """
        is_food_houses = set()
        is_not_food_houses = set()

        for vote in orm_models:
            if vote.is_food:
                is_food_houses.add(vote.house_id)
            else:
                is_not_food_houses.add(vote.house_id)

        return cls(
            acceptance_line={
                0: None,
                3: 1,
                5: 0.7,
            },  # Default acceptance line configuration
            is_food_houses=is_food_houses,
            is_not_food_houses=is_not_food_houses,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema to ORM model kwargs.

        Note: This returns a list of kwargs dicts since IsFoodVotes maps to multiple
        IsFoodVotesSaModel records (one per house vote).

        Returns:
            Dictionary with 'votes' key containing list of individual vote kwargs.
        """
        vote_kwargs_list = []

        # Create kwargs for each house that voted "is food"
        for house_id in self.is_food_houses:
            vote_kwargs_list.append(
                {
                    "house_id": house_id,
                    "is_food": True,
                }
            )

        # Create kwargs for each house that voted "is not food"
        for house_id in self.is_not_food_houses:
            vote_kwargs_list.append(
                {
                    "house_id": house_id,
                    "is_food": False,
                }
            )

        return {"votes": vote_kwargs_list}
