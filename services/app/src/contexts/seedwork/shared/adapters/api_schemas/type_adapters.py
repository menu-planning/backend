from typing import Any, Callable, TypeVar, Generic, Union
from pydantic import TypeAdapter, BeforeValidator, ConfigDict
from pydantic_core import PydanticCustomError
from threading import Lock

from src.contexts.seedwork.shared.adapters.exceptions.api_schema import DuplicateItemError

T = TypeVar('T')

class UniqueCollectionAdapter(Generic[T]):
    """
    Generic adapter for list validation with uniqueness constraints.
    
    This class now **caches** the underlying `TypeAdapter` instance, following
    Pydantic's recommendation to avoid the cost of rebuilding the core schema
    on every instantiation.  A single `TypeAdapter` is reused per `(item_type, config)`
    key, giving us near-singleton behaviour while still allowing different
    configurations if ever required.
    
    Validates that all items in a collection are unique based on a specified key function.
    Provides clear error messages with details about duplicate items.
    
    Example:
        # For objects with 'id' field
        recipe_adapter = UniqueCollectionAdapter(
            item_type=ApiRecipe,
            key_func=lambda x: x.id,
            collection_name="recipes"
        )
        
        # For simple types (using identity)
        tag_adapter = UniqueCollectionAdapter(
            item_type=str,
            key_func=lambda x: x,
            collection_name="tags"
        )
    """
    
    # Cache for { (item_type, strict_flag, arbitrary_flag) : TypeAdapter }
    _adapter_cache: dict[tuple[type, bool, bool], TypeAdapter] = {}
    _cache_lock: Lock = Lock()

    def __init__(
        self,
        item_type: type[T],
        key_func: Callable[[T], Any] = lambda x: x,
        collection_name: str = "items",
        strict: bool = False,
        arbitrary_types_allowed: bool = True,
    ):
        self.item_type = item_type
        self.key_func = key_func
        self.collection_name = collection_name
        
        cache_key = (item_type, strict, arbitrary_types_allowed)

        # Retrieve or create cached TypeAdapter
        with self._cache_lock:
            adapter = self._adapter_cache.get(cache_key)
            if adapter is None:
                config = ConfigDict(
                    strict=strict,
                    arbitrary_types_allowed=arbitrary_types_allowed,
                    defer_build=False,
                )
                adapter = TypeAdapter(list[item_type], config=config)
                self._adapter_cache[cache_key] = adapter
        self._adapter = adapter
    
    def validate_uniqueness(self, items: list[T]) -> list[T]:
        """Validate that all items are unique based on the key function."""
        if not items:
            return items
            
        seen_keys = set()
        duplicates = []
        
        for i, item in enumerate(items):
            key = self.key_func(item)
            if key in seen_keys:
                duplicates.append({
                    "index": i,
                    "key": key,
                    "item": str(item)
                })
            else:
                seen_keys.add(key)
        
        if duplicates:
            first_duplicate = duplicates[0]
            raise DuplicateItemError(
                message=f"Duplicate {self.collection_name} found: {duplicates}",
                item_type=self.collection_name,
                field_name=self.collection_name,
                duplicate_key=str(first_duplicate["key"]),
                duplicate_value=first_duplicate["key"],
                duplicate_items=duplicates
            )
        
        return items
    
    def validate_python(self, value: Any) -> list[T]:
        """Validate input and ensure uniqueness."""
        # First validate the basic list structure
        validated_list = self._adapter.validate_python(value)
        
        # Then check uniqueness
        return self.validate_uniqueness(validated_list)
    
    def validate_json(self, value: Union[str, bytes]) -> list[T]:
        """Validate JSON input and ensure uniqueness."""
        validated_list = self._adapter.validate_json(value)
        return self.validate_uniqueness(validated_list)
    
    def dump_python(self, value: list[T]) -> list[dict]:
        """Dump to Python dict format."""
        return self._adapter.dump_python(value)
    
    def dump_json(self, value: list[T]) -> bytes:
        """Dump to JSON bytes."""
        return self._adapter.dump_json(value)


def create_json_safe_collection_validator() -> BeforeValidator:
    """
    Create a validator that converts sets/frozensets to lists for JSON serialization.
    
    Preserves ordering for consistent output and handles nested collections recursively.
    """
    def convert_to_json_safe(value: Any) -> Any:
        if isinstance(value, (frozenset, frozenset)):
            # Convert to sorted list for consistency
            return sorted(list(value)) if all(
                isinstance(item, (str, int, float)) for item in value
            ) else list(value)
        elif isinstance(value, dict):
            # Recursively handle nested dictionaries
            return {k: convert_to_json_safe(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            # Recursively handle nested lists/tuples
            return [convert_to_json_safe(item) for item in value]
        return value
    
    return BeforeValidator(convert_to_json_safe)


def create_percentage_sum_validator(
    field_names: list[str],
    tolerance: float = 0.01,
    required_sum: float = 100.0
) -> Callable:
    """
    Create a model validator that ensures percentage fields sum to the required total.
    
    Args:
        field_names: List of field names that should sum to required_sum
        tolerance: Acceptable deviation from required_sum (default 0.01 for 1%)
        required_sum: Expected sum of percentage fields (default 100.0)
    
    Returns:
        Model validator function to be used with @model_validator(mode='after')
    """
    def validate_percentage_sum(model_instance):
        """Validate percentage sum and return the model instance."""
        model_data = model_instance.model_dump() if hasattr(model_instance, 'model_dump') else model_instance
        
        total = sum(
            model_data.get(field, 0) for field in field_names
            if model_data.get(field) is not None
        )
        
        if abs(total - required_sum) > tolerance:
            raise PydanticCustomError(
                'percentage_sum_invalid',
                'Percentage fields {fields} must sum to {required} (±{tolerance}), got {total}',
                {
                    'fields': field_names, 
                    'total': total, 
                    'required': required_sum,
                    'tolerance': tolerance
                }
            )
        
        return model_instance  # Return the model instance, not the data dict
    
    return validate_percentage_sum


def validate_no_duplicates_by_key(key_func: Callable[[Any], Any], collection_name: str = "items") -> BeforeValidator:
    """
    Create a validator that ensures no duplicates in a collection based on a key function.
    
    Args:
        key_func: Function to extract the uniqueness key from each item
        collection_name: Name of the collection for error messages
    
    Returns:
        BeforeValidator that checks for duplicates
    """
    def check_duplicates(value: Any) -> Any:
        if not isinstance(value, (list, tuple, frozenset)):
            return value
            
        seen_keys = set()
        duplicates = []
        
        for i, item in enumerate(value):
            key = key_func(item)
            if key in seen_keys:
                duplicates.append({
                    "index": i,
                    "key": key,
                    "item": str(item)
                })
            else:
                seen_keys.add(key)
        
        if duplicates:
            first_duplicate = duplicates[0]
            raise DuplicateItemError(
                message=f"Duplicate {collection_name} found: {duplicates}",
                item_type=collection_name,
                field_name=collection_name,
                duplicate_key=str(first_duplicate["key"]),
                duplicate_value=first_duplicate["key"],
                duplicate_items=duplicates
            )
        
        return value
    
    return BeforeValidator(check_duplicates)


def validate_non_empty_string_with_trim() -> BeforeValidator:
    """
    Create a validator that trims whitespace and ensures non-empty strings.
    
    Returns:
        BeforeValidator that trims and validates string content
    """
    def trim_and_validate(value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("Input should be a string")
        
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("String must not be empty after trimming whitespace")
        
        return trimmed
    
    return BeforeValidator(trim_and_validate)