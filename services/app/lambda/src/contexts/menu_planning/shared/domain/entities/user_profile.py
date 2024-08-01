from src.contexts.seedwork.shared.domain.entitie import Entity


class UserProfile(Entity):
    def __init__(
        self,
        id: str,
        username: str,
        email: str,
        discarded: bool = False,
        version: int = 1,
    ):