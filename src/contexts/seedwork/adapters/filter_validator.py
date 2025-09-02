from typing import Any

from sqlalchemy.inspection import inspect as sa_inspect
from src.contexts.seedwork.adapters.repositories.filter_mapper import (
    FilterColumnMapper,
)
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    FilterValidationError,
)


class FilterValidator:
    """Validate filter dictionaries for allowed keys and value types.

    This class provides validation for filter dictionaries used in repository
    operations. It serves as a second line of defense after API schema
    validation, ensuring that only allowed filter keys are used and that
    the model supports the requested filtering operations.

    The validator automatically handles common patterns like:
    - Filter key postfixes (_gte, _lte, _ne, etc.)
    - Special allowed keys (skip, limit, etc.)
    - Automatic discarded column handling
    - Column existence validation

    Args:
        allowed_keys: List of allowed filter keys (without postfixes)
        special_allowed: List of special filter keys always allowed
        sa_model_type: SQLAlchemy model type for column inspection
    """

    def __init__(
        self,
        allowed_keys: list[str],
        special_allowed: list[str] | None = None,
        sa_model_type=None,
    ):
        """Initialize FilterValidator with configuration.

        Args:
            allowed_keys: Allowed filter keys (no postfix)
            special_allowed: List of special filter keys always allowed
                (e.g., 'skip', 'limit', etc.)
            sa_model_type: SQLAlchemy model type for column inspection
                (used for discarded handling)
        """
        self.allowed_keys = allowed_keys
        self.special_allowed = set(special_allowed or [])
        self.sa_model_type = sa_model_type

    def remove_postfix(self, key: str) -> str:
        """Remove known filter postfixes from a key.

        Args:
            key: Filter key that may contain postfixes

        Returns:
            Key with postfix removed, or original key if no postfix found

        Supported postfixes:
            - _gte: greater than or equal
            - _lte: less than or equal
            - _ne: not equal
            - _not_in: not in collection
            - _is_not: is not null/true
            - _not_exists: does not exist
            - _like: pattern matching
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
        """Check if the SQLAlchemy model has a 'discarded' column.

        Returns:
            True if the model has a discarded column, False otherwise
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
        """Automatically handle the 'discarded' filter logic.

        This method implements the soft delete pattern by automatically
        setting discarded=False when the user doesn't specify a discarded
        filter, ensuring that only non-discarded records are returned.

        Args:
            filter_dict: The filter dictionary to potentially modify

        Returns:
            Modified filter dictionary with discarded handling applied

        Behavior:
            - If model has 'discarded' column AND user didn't provide
              'discarded' filter, automatically set discarded=False
            - If user provided 'discarded' filter, respect their choice
            - If model has no 'discarded' column, return unchanged
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
        """Ensure all filter keys are allowed (with postfixes handled).

        Args:
            filter_dict: Dictionary of filters to validate
            repository: The repository instance (required for exception)

        Raises:
            FilterValidationError: If any filter keys are invalid
            ValueError: If repository is not provided for exception raising

        Validation logic:
            - Removes postfixes from keys before validation
            - Checks against allowed_keys and special_allowed
            - Provides helpful error messages with suggestions
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
        """Run complete filter validation and processing.

        This method performs the full validation pipeline:
        1. Automatic discarded filter handling
        2. Filter key validation
        3. Returns processed filter dictionary

        Args:
            filter_dict: The filter dictionary to validate
            repository: The repository instance (required for exception)

        Returns:
            The validated and potentially modified filter dictionary

        Raises:
            FilterValidationError: If filter keys are invalid
            ValueError: If repository is not provided for exception raising
        """
        # First, handle discarded filter logic
        processed_filter = self._handle_discarded_filter(filter_dict)

        # Then run validations on the processed filter
        self.validate_filter_keys(processed_filter, repository=repository)

        return processed_filter

    @classmethod
    def from_mappers(
        cls,
        mappers: list[FilterColumnMapper],
        *,
        special_allowed: list[str] | None = None,
        sa_model_type=None,
    ) -> "FilterValidator":
        """Create a FilterValidator by inspecting FilterColumnMapper list.

        Args:
            mappers: List of FilterColumnMapper instances
            special_allowed: List of special filter keys always allowed
            sa_model_type: SQLAlchemy model type for column inspection

        Returns:
            Configured FilterValidator instance

        This factory method extracts allowed filter keys from mapper
        configurations, making it easy to create validators that match
        the repository's filter capabilities.
        """
        allowed_keys = [
            filter_key
            for mapper in mappers
            for filter_key in mapper.filter_key_to_column_name
        ]
        return cls(
            allowed_keys, special_allowed=special_allowed, sa_model_type=sa_model_type
        )
