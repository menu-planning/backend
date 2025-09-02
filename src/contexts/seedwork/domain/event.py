"""Domain event helpers and identifiers."""

import uuid


class Event:
    """Base event utilities.

    Exposes helpers commonly needed across domain events.

    Notes:
        Immutable. Equality by value (utility methods).
    """

    @staticmethod
    def generate_uuid() -> str:
        """Return a random event identifier as a hex string.

        Returns:
            Random UUID v4 as hexadecimal string.
        """
        return uuid.uuid4().hex
