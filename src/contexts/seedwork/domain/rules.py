from abc import abstractmethod


class BusinessRule:
    """Base class for domain business rules.

    Subclasses must implement ``is_broken`` and may customize the
    human-readable message returned by ``get_message``.

    Notes:
        Immutable. Equality by value (rule implementation).
    """

    __message: str = "Business rule is broken"

    def get_message(self) -> str:
        """Return the human-readable message for this business rule.

        Returns:
            Human-readable message describing the broken rule.
        """
        return self.__message

    @abstractmethod
    def is_broken(self) -> bool:
        """Return True if the rule is broken (i.e., validation fails).

        Returns:
            True if the business rule is violated, False otherwise.
        """
        pass

    def __str__(self):
        """Return string representation of the business rule.

        Returns:
            String representation in format "{ClassName} {super().__str__()}".
        """
        return f"{self.__class__.__name__} {super().__str__()}"
