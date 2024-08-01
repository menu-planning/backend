from pydantic import BaseModel
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.endpoints.pydantic_validators import CreatedAtValue


class ApiDietType(BaseModel):
    """
    A Pydantic model representing and validating a Diet Type.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the DietType.
        name (str): Name of the DietType.
        author_id (str): Identifier of the recipes's author.
        privacy (Privacy): Privacy setting of the DietType.
        description (str, optional): Description of the DietType.

    Methods:
        from_domain(domain_obj: DietType) -> "ApiDietType":
            Creates an instance of `ApiDietType` from a domain model object.
        to_domain() -> DietType:
            Converts the instance to a domain model object.
    """

    id: str
    name: str
    author_id: str
    description: str | None = None
    privacy: Privacy = Privacy.PRIVATE
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    discarded: bool = False
    version: int = 1

    @classmethod
    def from_domain(cls, domain_obj: DietType) -> "ApiDietType":
        """Creates an instance of `ApiDietType` from a domain model object."""
        try:
            return cls(
                id=domain_obj.id,
                name=domain_obj.name,
                author_id=domain_obj.author_id,
                description=domain_obj.description,
                privacy=domain_obj.privacy,
                created_at=domain_obj.created_at,
                updated_at=domain_obj.updated_at,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
        except Exception as e:
            raise ValueError(f"Failed to build ApiDietType from domain instance: {e}")

    def to_domain(self) -> DietType:
        """Converts the instance to a domain model object."""
        try:
            return DietType(
                id=self.id,
                name=self.name,
                author_id=self.author_id,
                description=self.description,
                privacy=self.privacy,
                created_at=self.created_at,
                updated_at=self.updated_at,
                discarded=self.discarded,
                version=self.version,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDietType to domain model: {e}")
