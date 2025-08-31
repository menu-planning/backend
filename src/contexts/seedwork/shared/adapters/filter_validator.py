from typing import Any

from sqlalchemy.inspection import inspect as sa_inspect
from src.contexts.seedwork.shared.adapters.repositories.filter_mapper import (
    FilterColumnMapper,
)
from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import (
    FilterValidationError,
)


class FilterValidator:
    """
    Validates filter dictionaries for allowed keys and value types using Pydantic
    BaseModel.
    Intended for use at the repository layer as a second line of defense after API
    schema validation.
    """

    def __init__(
        self,
        allowed_keys: list[str],
        special_allowed: list[str] | None = None,
        sa_model_type=None,
    ):
        """
        :param allowed_keys: Allowed filter keys (no postfix)
        :param special_allowed: List of special filter keys always allowed
            (e.g., 'skip', 'limit', etc.)
        :param sa_model_type: SQLAlchemy model type for column inspection
            (used for discarded handling)
        """
        self.allowed_keys = allowed_keys
        self.special_allowed = set(special_allowed or [])
        self.sa_model_type = sa_model_type

    def remove_postfix(self, key: str) -> str:
        """
        Remove known filter postfixes (e.g., _gte, _lte, etc.) from a key.
        """
        postfixes = [
            "_gte",
            "_lte",
            "_ne",
            "_not_in",
            "_is_not",
            "_not_exists",
            "_like",
        ]
        for postfix in postfixes:
            if key.endswith(postfix):
                return key[: -len(postfix)]
        return key

    def _has_discarded_column(self) -> bool:
        """
        Check if the SQLAlchemy model has a 'discarded' column.
        """
        if not self.sa_model_type:
            return False
        try:
            inspector = sa_inspect(self.sa_model_type)
        except Exception:
            return False
        else:
            return "discarded" in inspector.c

    def _handle_discarded_filter(self, filter_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Automatically handle the 'discarded' filter:
        - If the model has a 'discarded' column AND user didn't provide 'discarded'
          filter, automatically set discarded=False
        - If user provided 'discarded' filter, respect their choice

        :param filter_dict: The filter dictionary to potentially modify
        :return: Modified filter dictionary with discarded handling applied
        """
        if not self._has_discarded_column():
            return filter_dict

        # Check if user already provided a discarded filter (with any postfix)
        has_discarded_filter = any(
            self.remove_postfix(key) == "discarded" for key in filter_dict
        )

        # If no discarded filter provided, automatically add discarded=False
        if not has_discarded_filter:
            filter_dict = filter_dict.copy()  # Don't modify the original
            filter_dict["discarded"] = False

        return filter_dict

    def validate_filter_keys(
        self, filter_dict: dict[str, Any], repository=None
    ) -> None:
        """
        Ensure all filter keys are allowed (with postfixes handled).
        Raise FilterValidationException if any are invalid.
        :param repository: The repository instance (required for exception)
        """
        invalid = []
        suggestions = set(self.allowed_keys) | self.special_allowed
        for k in filter_dict:
            base = self.remove_postfix(k)
            if base not in self.allowed_keys and base not in self.special_allowed:
                invalid.append(k)
        if invalid:
            if repository is None:
                error_msg = (
                    "repository must be provided to FilterValidator for exception "
                    "raising"
                )
                raise ValueError(error_msg)
            raise FilterValidationError(
                message=f"Invalid filter keys: {', '.join(invalid)}",
                repository=repository,
                invalid_filters=invalid,
                suggested_filters=list(suggestions)[:10],
            )

    def validate(self, filter_dict: dict[str, Any], repository=None) -> dict[str, Any]:
        """
        Run both key and type validation, and handle automatic discarded filtering.
        Returns the potentially modified filter dictionary.

        :param filter_dict: The filter dictionary to validate
        :param repository: The repository instance (required for exception)
        :return: The validated and potentially modified filter dictionary
        """
        # First, handle discarded filter logic
        processed_filter = self._handle_discarded_filter(filter_dict)

        # Then run validations on the processed filter
        self.validate_filter_keys(processed_filter, repository=repository)

        return processed_filter

    """
    Example usage/test:
    >>> allowed = {"id": int, "name": str, "active": bool}
    >>> validator = FilterValidator(allowed, special_allowed=["skip", "limit"])
    >>> validator.validate_filter_keys(
    ...     {"id": 1, "name": "foo", "skip": 0}, repository=object()
    ... )
    >>> validator.validate(
    ...     {"id": 1, "name": "foo", "active": True}, repository=object()
    ... )
    """

    # ------------------------------------------------------------------
    # Class helpers for building from FilterColumnMapper configurations
    # ------------------------------------------------------------------

    @classmethod
    def from_mappers(
        cls,
        mappers: list[FilterColumnMapper],
        *,
        special_allowed: list[str] | None = None,
        sa_model_type=None,
    ) -> "FilterValidator":
        """Create a FilterValidator by inspecting FilterColumnMapper list."""
        allowed_keys = [
            filter_key
            for mapper in mappers
            for filter_key in mapper.filter_key_to_column_name
        ]
        return cls(
            allowed_keys, special_allowed=special_allowed, sa_model_type=sa_model_type
        )
