from pydantic import BaseModel


class ApiNameTagFilter(BaseModel):
    """
    A Pydantic model representing and validating a filter for recipe tags.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the tag.
        skip (int, optional): Number of tags to skip.
        limit (int, optional): Maximum number of tags to return.
        sort (str, optional): Sort order for the tags.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary for use in a domain model object.
    """

    name: str | None = None
    skip: int | None = None
    limit: int | None = 100
    sort: str | None = "-name"
