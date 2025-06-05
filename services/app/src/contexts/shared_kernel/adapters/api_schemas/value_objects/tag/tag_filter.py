from pydantic import BaseModel


class ApiTagFilter(BaseModel):
    """
    A Pydantic model representing and validating a filter for tags.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        key (str, optional): Key of the tag.
        value (str, optional): Value of the tag.
        author_id (str, optional): ID of the author of the tag.
        skip (int, optional): Number of tags to skip.
        limit (int, optional): Maximum number of tags to return.
        sort (str, optional): Sort order for the tags.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary for use in a domain model object.
    """

    model_config = {"frozen": True}

    key: str | list[str] |  None = None
    value: str | list[str] |  None = None
    author_id: str |list[str] | None = None
    type: str | list[str] | None = None
    skip: int | None = None
    limit: int | None = 100
    sort: str | None = "-key"

    def to_domain(self) -> dict:
        """Convert the instance to a dictionary for use in a domain model object."""
        return self.model_dump(exclude_none=True)
