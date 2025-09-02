from enum import Enum, unique


@unique
class Permission(Enum):
    """Base permission enumeration for access control.

    Notes:
        Immutable. Equality by value (permission string).
    """
    pass


@unique
class Role(Enum):
    """Base role enumeration for user roles.

    Notes:
        Immutable. Equality by value (role string).
    """
    pass
