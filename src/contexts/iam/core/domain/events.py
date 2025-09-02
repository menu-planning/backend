"""IAM domain events."""
import uuid

from attrs import field, frozen
from src.contexts.seedwork.domain.event import Event


@frozen
class UserCreated(Event):
    """Event emitted when a new user is created in the IAM system.
    
    Attributes:
        user_id: Unique identifier of the created user (UUID v4).
    
    Notes:
        Emitted by: User.create_user(). Ordering: none.
    """
    user_id: str = field(factory=lambda: uuid.uuid4().hex)
