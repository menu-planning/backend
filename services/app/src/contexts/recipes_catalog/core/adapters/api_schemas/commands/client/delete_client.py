from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseCommand
from src.contexts.recipes_catalog.core.domain.commands.client.delete_client import DeleteClient
from src.contexts.seedwork.shared.adapters.api_schemas.fields import UUIDId
from src.db.base import SaBase


class ApiDeleteClient(BaseCommand[DeleteClient, SaBase]):
    """
    A Pydantic model representing and validating the data required
    to delete a client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        client_id (str): ID of the client to delete.

    Methods:
        to_domain() -> DeleteClient:
            Converts the instance to a domain model object for deleting a client.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    client_id: UUIDId

    def to_domain(self) -> DeleteClient:
        """Converts the instance to a domain model object for deleting a client."""
        try:
            return DeleteClient(client_id=self.client_id)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDeleteClient to domain model: {e}")
