from typing import Any, Dict, Optional, List
# No Pydantic dependency here; runtime checks are performed manually.
from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import FilterValidationException
from sqlalchemy.inspection import inspect as sa_inspect
from src.contexts.seedwork.shared.adapters.repositories.filter_mapper import FilterColumnMapper

class FilterValidator:
    """
    Validates filter dictionaries for allowed keys and value types using Pydantic BaseModel.
    Intended for use at the repository layer as a second line of defense after API schema validation.
    """
    def __init__(self, allowed_keys_types: Dict[str, type], special_allowed: Optional[List[str]] = None, sa_model_type=None):
        """
        :param allowed_keys_types: Mapping of allowed filter keys (no postfix) to their expected Python types
        :param special_allowed: List of special filter keys always allowed (e.g., 'skip', 'limit', etc.)
        :param sa_model_type: SQLAlchemy model type for column inspection (used for discarded handling)
        """
        self.allowed_keys_types = allowed_keys_types
        self.special_allowed = set(special_allowed or [])
        self.sa_model_type = sa_model_type

    def remove_postfix(self, key: str) -> str:
        """
        Remove known filter postfixes (e.g., _gte, _lte, etc.) from a key.
        """
        postfixes = [
            '_gte', '_lte', '_ne', '_not_in', '_is_not', '_not_exists', '_like',
        ]
        for postfix in postfixes:
            if key.endswith(postfix):
                return key[:-len(postfix)]
        return key

    def _has_discarded_column(self) -> bool:
        """
        Check if the SQLAlchemy model has a 'discarded' column.
        """
        if not self.sa_model_type:
            return False
        try:
            inspector = sa_inspect(self.sa_model_type)
            return "discarded" in inspector.c.keys()
        except Exception:
            return False

    def _handle_discarded_filter(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically handle the 'discarded' filter:
        - If the model has a 'discarded' column AND user didn't provide 'discarded' filter,
          automatically set discarded=False
        - If user provided 'discarded' filter, respect their choice
        
        :param filter_dict: The filter dictionary to potentially modify
        :return: Modified filter dictionary with discarded handling applied
        """
        if not self._has_discarded_column():
            return filter_dict
        
        # Check if user already provided a discarded filter (with any postfix)
        has_discarded_filter = any(
            self.remove_postfix(key) == "discarded" 
            for key in filter_dict.keys()
        )
        
        # If no discarded filter provided, automatically add discarded=False
        if not has_discarded_filter:
            filter_dict = filter_dict.copy()  # Don't modify the original
            filter_dict["discarded"] = False
        
        return filter_dict

    def validate_filter_keys(self, filter_dict: Dict[str, Any], repository=None) -> None:
        """
        Ensure all filter keys are allowed (with postfixes handled).
        Raise FilterValidationException if any are invalid.
        :param repository: The repository instance (required for exception)
        """
        invalid = []
        suggestions = set(self.allowed_keys_types.keys()) | self.special_allowed
        for k in filter_dict.keys():
            base = self.remove_postfix(k)
            if base not in self.allowed_keys_types and base not in self.special_allowed:
                invalid.append(k)
        if invalid:
            if repository is None:
                raise ValueError("repository must be provided to FilterValidator for exception raising")
            raise FilterValidationException(
                message=f"Invalid filter keys: {', '.join(invalid)}",
                repository=repository,
                invalid_filters=invalid,
                suggested_filters=list(suggestions)[:10],
            )

    def validate_filter_types(self, filter_dict: Dict[str, Any], repository=None) -> None:
        """
        Use Pydantic to validate types of filter values.
        Raise FilterValidationException if any type errors are found.
        :param repository: The repository instance (required for exception)
        """
        for original_key, value in filter_dict.items():
            base_key = self.remove_postfix(original_key)
            if base_key not in self.allowed_keys_types:
                # Key validation handles this case; skip
                continue

            expected_type = self.allowed_keys_types[base_key]

            # Allow flexible numeric type checking: if expected is float, accept int as valid
            if expected_type is float:
                numeric_types: tuple[type, ...] = (int, float)
            elif expected_type is int:
                numeric_types = (int,)
            else:
                numeric_types = (expected_type,)

            # Allow list/tuple/set values where each element matches expected
            if isinstance(value, (list, set, tuple)):
                if not all(isinstance(item, numeric_types) for item in value):
                    if repository is None:
                        raise ValueError("repository must be provided to FilterValidator for exception raising")
                    raise FilterValidationException(
                        message=(
                            f"Filter type validation error: Items in list for '{original_key}'"
                            f" must be of type {', '.join(map(lambda t: t.__name__, numeric_types))}"
                        ),
                        repository=repository,
                        invalid_filters=[original_key],
                        suggested_filters=list(self.allowed_keys_types.keys())[:10],
                    )
            else:
                # Non-iterable value: direct type check; allow bool/int subclass etc.
                if value is not None and not isinstance(value, numeric_types):
                    if repository is None:
                        raise ValueError("repository must be provided to FilterValidator for exception raising")
                    raise FilterValidationException(
                        message=(
                            f"Filter type validation error: Value for '{original_key}' must be "
                            f"of type {', '.join(map(lambda t: t.__name__, numeric_types))}, got {type(value).__name__}"
                        ),
                        repository=repository,
                        invalid_filters=[original_key],
                        suggested_filters=list(self.allowed_keys_types.keys())[:10],
                    )

    def validate(self, filter_dict: Dict[str, Any], repository=None) -> Dict[str, Any]:
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
        self.validate_filter_types(processed_filter, repository=repository)
        
        return processed_filter

    # TODO: Optionally allow repository to be set on the FilterValidator instance for convenience.

    """
    Example usage/test:
    >>> allowed = {"id": int, "name": str, "active": bool}
    >>> validator = FilterValidator(allowed, special_allowed=["skip", "limit"])
    >>> validator.validate_filter_keys({"id": 1, "name": "foo", "skip": 0}, repository=object())
    >>> validator.validate_filter_types({"id": 1, "name": "foo"}, repository=object())
    >>> validator.validate({"id": 1, "name": "foo", "active": True}, repository=object())
    """

    # ------------------------------------------------------------------
    # Class helpers for building from FilterColumnMapper configurations
    # ------------------------------------------------------------------

    @classmethod
    def from_mappers(
        cls,
        mappers: List[FilterColumnMapper],
        *,
        special_allowed: Optional[List[str]] = None,
        sa_model_type=None,
    ) -> "FilterValidator":
        """Create a FilterValidator by inspecting FilterColumnMapper list."""
        combined: Dict[str, type] = {}
        for mapper in mappers:
            sa_model = mapper.sa_model_type
            sa_inspector = sa_inspect(sa_model)
            for filter_key, column_name in mapper.filter_key_to_column_name.items():
                py_type = cls._get_column_python_type(sa_inspector, column_name)
                combined[filter_key] = py_type
        return cls(combined, special_allowed=special_allowed, sa_model_type=sa_model_type)

    @staticmethod
    def _get_column_python_type(sa_inspector, column_name: str) -> type:  # type: ignore
        """Helper to get python_type for a SQLAlchemy column; defaults to str."""
        try:
            return sa_inspector.columns[column_name].type.python_type  # type: ignore[arg-type]
        except Exception:
            # Fallback to str as a safe default
            return str 