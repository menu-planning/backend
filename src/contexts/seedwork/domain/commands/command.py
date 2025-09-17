import inspect
import uuid


class Command:
    """Base command utilities.

    Commands represent intent to perform an action. This utility provides a
    consistent way to create identifiers for commands.

    Notes:
        Immutable. Equality by value (utility methods).
    """

    @staticmethod
    def generate_uuid() -> str:
        """Return a random command identifier as a hex string.

        Returns:
            Random UUID v4 as hexadecimal string.
        """
        return uuid.uuid4().hex
