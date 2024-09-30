from typing import Optional

import cattrs
from attrs import asdict
from pydantic import BaseModel, Field
from src.contexts.products_catalog.shared.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.logging.logger import logger


class ApiIsFoodVotes(BaseModel):
    """
    A Pydantic model representing and validating the score of a food item.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.
    """

    acceptance_line: dict[float, float | None] = Field(default_factory=dict)
    is_food_houses: set[str] = Field(default_factory=set)
    is_not_food_houses: set[str] = Field(default_factory=set)

    @classmethod
    def from_domain(cls, domain_obj: IsFoodVotes) -> "ApiIsFoodVotes":
        """Creates an instance of `ApiIsFoodVotes` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            logger.error(
                f"Failed to build ApiIsFoodVotes from domain instance => {domain_obj}. ERROR: {e}"
            )
            raise ValueError(
                f"Failed to build ApiIsFoodVotes from domain instance: {e}"
            )

    def to_domain(self) -> IsFoodVotes:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), IsFoodVotes)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiIsFoodVotes to domain model: {e}")
