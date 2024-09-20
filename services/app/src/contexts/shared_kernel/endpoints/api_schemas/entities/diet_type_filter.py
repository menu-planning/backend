from pydantic import BaseModel, model_validator
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.adapters.repositories.diet_type import DietTypeRepo
from src.contexts.shared_kernel.domain.enums import Privacy
from src.logging.logger import logger


class ApiDietTypeFilter(BaseModel):
    """
    A Pydantic model representing and validating the data required to filter
    diet type.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the diet type.
        author_id (str, optional): Identifier of the tag's author.
        privacy (Privacy, optional): Privacy setting of the tag.
        description (str, optional): Description of the tag.

    Methods:
        to_domain() -> TagFilter:
            Converts the instance to a domain model object for filtering tags.
    """

    name: str | None = None
    author_id: str | None = None
    privacy: Privacy | None = None
    description: str | None = None
    skip: int | None = None
    limit: int | None = 20
    sort: str | None = "-created_at"

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
        logger.debug(f"Validating filter: {values}")
        allowed_filters = []
        logger.debug(
            f"Filter to column mappers: {DietTypeRepo.filter_to_column_mappers}"
        )
        for mapper in DietTypeRepo.filter_to_column_mappers:
            logger.debug(f"Mapper: {mapper}")
            allowed_filters.extend(mapper.filter_key_to_column_name.keys())
        allowed_filters.extend(
            [
                "discarded",
                "skip",
                "limit",
                "sort",
                "created_at",
            ]
        )
        logger.debug(f"Allowed filters: {allowed_filters}")
        for k in values.keys():
            if SaGenericRepository.removePostfix(k) not in allowed_filters:
                raise ValueError(f"Invalid filter: {k}")
        # for k in allowed_filters:
        #     assert k in cls.model_fields, f"Missing filter on api: {k}"
        return values
