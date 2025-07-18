import dataclasses
import inspect
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from unittest.mock import Mock

from attrs import asdict
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


def _class_attributes(cls) -> list[str]:
    attributes = [
        attr
        for attr in inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
        if not (attr[0].startswith("_") or attr[0] == "instance_id")
    ]
    return [i[0] for i in attributes]


def _get_computed_properties(cls) -> set[str]:
    """Get all computed properties (decorated with @property) from a class."""
    properties = []
    for name, value in inspect.getmembers(cls):
        if isinstance(value, property):
            properties.append(name)
    return set(properties)


def _get_sqlalchemy_internals(cls) -> set[str]:
    """Get SQLAlchemy internal attributes that shouldn't be in constructor."""
    sqlalchemy_internals = set()
    
    # Check if this is a SQLAlchemy model
    if hasattr(cls, '__tablename__') or hasattr(cls, 'metadata'):
        # Common SQLAlchemy internal attributes
        common_internals = {'metadata', 'registry', 'type_annotation_map'}
        
        # Check which ones actually exist on this class
        for attr in common_internals:
            if hasattr(cls, attr):
                sqlalchemy_internals.add(attr)
        
        # Auto-increment primary key 'id' is typically not passed to constructor
        if hasattr(cls, 'id') and hasattr(cls, '__table__'):
            # Check if id is auto-increment primary key
            try:
                id_column = getattr(cls.__table__.c, 'id', None)
                if id_column is not None and id_column.primary_key and id_column.autoincrement:
                    sqlalchemy_internals.add('id')
            except:
                # If we can't determine, assume auto-increment id should be excluded
                sqlalchemy_internals.add('id')
    
    return sqlalchemy_internals


def _class_method_attributes(method) -> list[str]:
    if not inspect.ismethod(method):
        raise TypeError("The argument must be a class method.")

    sig = inspect.signature(method)
    return [param.name for param in sig.parameters.values() if param.name != "cls"]


def check_missing_attributes(cls_or_method, kwargs) -> list[str]:
    if inspect.isclass(cls_or_method):
        attribute_names = _class_attributes(cls_or_method)
        
        # Automatically exclude computed properties and SQLAlchemy internals
        computed_props = _get_computed_properties(cls_or_method)
        sqlalchemy_internals = _get_sqlalchemy_internals(cls_or_method)
        excluded_attrs = computed_props | sqlalchemy_internals
        
        # Filter out excluded attributes
        attribute_names = [attr for attr in attribute_names if attr not in excluded_attrs]
        
    elif inspect.ismethod(cls_or_method):
        attribute_names = _class_method_attributes(cls_or_method)
    else:
        raise TypeError("The first argument must be a class or a class method.")

    return [attr for attr in attribute_names if attr not in kwargs]


def enum_value_serializer(instance, attribute, value):
    if isinstance(value, Enum):
        return value.value
    return value


def build_dict_from_instance(instance) -> dict[str, Any]:
    result = {}
    if isinstance(instance, ValueObject):
        return asdict(instance, value_serializer=enum_value_serializer)
    if dataclasses.is_dataclass(instance):
        return dataclasses.asdict(instance) # type: ignore
    try:
        for attr, value in vars(instance).items():
            if attr.startswith("_"):
                attr = attr[1:]
            if attr == "sa_instance_state":
                continue
            if isinstance(value, list) or isinstance(value, set):
                result[attr] = [build_dict_from_instance(i) for i in value]
            elif (
                isinstance(value, Entity)
                or isinstance(value, ValueObject)
                or dataclasses.is_dataclass(value)
            ):
                result[attr] = build_dict_from_instance(value)
            elif isinstance(value, Enum):
                result[attr] = value.value
            else:
                result[attr] = value
    except Exception:
        return instance
    return result


# =============================================================================
# DYNAMIC MODEL COMPARISON UTILITIES
# =============================================================================

def compare_api_to_domain(api_model: Any, domain_obj: Any, excluded_fields: Optional[Set[str]] = None) -> List[str]:
    """
    Compare API model to domain object using dynamic field iteration.
    
    Args:
        api_model: API model instance with model_fields attribute
        domain_obj: Domain object instance  
        excluded_fields: Fields to exclude from comparison
        
    Returns:
        List of differences found, empty if objects match
        
    Example:
        differences = compare_api_to_domain(api_meal, domain_meal)
        assert not differences, f"API/Domain mismatch: {differences}"
    """
    if not hasattr(api_model.__class__, 'model_fields'):
        raise ValueError(f"API model {type(api_model)} does not have model_fields attribute")
    
    excluded_fields = excluded_fields or set()
    differences = []
    
    for field_name in api_model.__class__.model_fields.keys():
        if field_name in excluded_fields:
            continue
            
        try:
            api_value = getattr(api_model, field_name)
            domain_value = getattr(domain_obj, field_name, None)
            
            if not _values_are_equivalent(api_value, domain_value, field_name):
                differences.append(f"Field '{field_name}': API({api_value}) != Domain({domain_value})")
                
        except AttributeError as e:
            differences.append(f"Field '{field_name}': AttributeError - {e}")
        except Exception as e:
            differences.append(f"Field '{field_name}': Unexpected error - {e}")
    
    return differences


def compare_api_to_orm_kwargs(api_model: Any, orm_kwargs: Dict[str, Any], excluded_fields: Optional[Set[str]] = None) -> List[str]:
    """
    Compare API model to ORM kwargs using dynamic field iteration.
    
    Args:
        api_model: API model instance with model_fields attribute
        orm_kwargs: Dictionary of ORM kwargs
        excluded_fields: Fields to exclude from comparison
        
    Returns:
        List of differences found, empty if objects match
        
    Example:
        orm_kwargs = api_meal.to_orm_kwargs()
        differences = compare_api_to_orm_kwargs(original_api, orm_kwargs)
        assert not differences, f"API/ORM kwargs mismatch: {differences}"
    """
    if not hasattr(api_model.__class__, 'model_fields'):
        raise ValueError(f"API model {type(api_model)} does not have model_fields attribute")
    
    excluded_fields = excluded_fields or set()
    differences = []
    
    for field_name in api_model.__class__.model_fields.keys():
        if field_name in excluded_fields:
            continue
            
        try:
            api_value = getattr(api_model, field_name)
            orm_value = orm_kwargs.get(field_name)
            
            if not _values_are_equivalent(api_value, orm_value, field_name):
                differences.append(f"Field '{field_name}': API({api_value}) != ORM({orm_value})")
                
        except Exception as e:
            differences.append(f"Field '{field_name}': Unexpected error - {e}")
    
    return differences


def compare_orm_to_domain(orm_obj: Any, domain_obj: Any, field_names: Optional[List[str]] = None, excluded_fields: Optional[Set[str]] = None) -> List[str]:
    """
    Compare ORM object to domain object using dynamic field iteration.
    
    Args:
        orm_obj: ORM model instance or Mock object
        domain_obj: Domain object instance
        field_names: Specific fields to compare (if None, attempts to infer from domain_obj)
        excluded_fields: Fields to exclude from comparison
        
    Returns:
        List of differences found, empty if objects match
        
    Example:
        differences = compare_orm_to_domain(real_orm_meal, domain_meal)
        assert not differences, f"ORM/Domain mismatch: {differences}"
    """
    excluded_fields = excluded_fields or set()
    differences = []
    
    # Auto-detect field names if not provided
    if field_names is None:
        if hasattr(domain_obj, '__dict__'):
            field_names = [name for name in domain_obj.__dict__.keys() if not name.startswith('_')]
        else:
            # Fallback for value objects or dataclasses
            field_names = _get_object_field_names(domain_obj)
    
    for field_name in field_names:
        if field_name in excluded_fields:
            continue
            
        try:
            orm_value = getattr(orm_obj, field_name, None)
            domain_value = getattr(domain_obj, field_name, None)
            
            if not _values_are_equivalent(orm_value, domain_value, field_name):
                differences.append(f"Field '{field_name}': ORM({orm_value}) != Domain({domain_value})")
                
        except AttributeError as e:
            differences.append(f"Field '{field_name}': AttributeError - {e}")
        except Exception as e:
            differences.append(f"Field '{field_name}': Unexpected error - {e}")
    
    return differences


def assert_api_domain_match(api_model: Any, domain_obj: Any, excluded_fields: Optional[Set[str]] = None, custom_message: str = "") -> None:
    """
    Assert that API model matches domain object with detailed error reporting.
    
    Args:
        api_model: API model instance
        domain_obj: Domain object instance
        excluded_fields: Fields to exclude from comparison
        custom_message: Custom error message prefix
        
    Raises:
        AssertionError: If objects don't match
        
    Example:
        assert_api_domain_match(api_meal, domain_meal, excluded_fields={'created_at'})
    """
    differences = compare_api_to_domain(api_model, domain_obj, excluded_fields)
    if differences:
        error_msg = f"API model does not match domain object"
        if custom_message:
            error_msg = f"{custom_message}: {error_msg}"
        error_msg += f"\nDifferences found:\n" + "\n".join(f"  - {diff}" for diff in differences)
        raise AssertionError(error_msg)


def assert_api_orm_kwargs_match(api_model: Any, orm_kwargs: Dict[str, Any], excluded_fields: Optional[Set[str]] = None, custom_message: str = "") -> None:
    """
    Assert that API model matches ORM kwargs with detailed error reporting.
    
    Args:
        api_model: API model instance
        orm_kwargs: Dictionary of ORM kwargs
        excluded_fields: Fields to exclude from comparison
        custom_message: Custom error message prefix
        
    Raises:
        AssertionError: If objects don't match
        
    Example:
        orm_kwargs = api_meal.to_orm_kwargs()
        assert_api_orm_kwargs_match(api_meal, orm_kwargs)
    """
    differences = compare_api_to_orm_kwargs(api_model, orm_kwargs, excluded_fields)
    if differences:
        error_msg = f"API model does not match ORM kwargs"
        if custom_message:
            error_msg = f"{custom_message}: {error_msg}"
        error_msg += f"\nDifferences found:\n" + "\n".join(f"  - {diff}" for diff in differences)
        raise AssertionError(error_msg)


def assert_orm_domain_match(orm_obj: Any, domain_obj: Any, field_names: Optional[List[str]] = None, excluded_fields: Optional[Set[str]] = None, custom_message: str = "") -> None:
    """
    Assert that ORM object matches domain object with detailed error reporting.
    
    Args:
        orm_obj: ORM model instance or Mock object
        domain_obj: Domain object instance
        field_names: Specific fields to compare
        excluded_fields: Fields to exclude from comparison
        custom_message: Custom error message prefix
        
    Raises:
        AssertionError: If objects don't match
        
    Example:
        assert_orm_domain_match(real_orm_meal, domain_meal, excluded_fields={'version'})
    """
    differences = compare_orm_to_domain(orm_obj, domain_obj, field_names, excluded_fields)
    if differences:
        error_msg = f"ORM object does not match domain object"
        if custom_message:
            error_msg = f"{custom_message}: {error_msg}"
        error_msg += f"\nDifferences found:\n" + "\n".join(f"  - {diff}" for diff in differences)
        raise AssertionError(error_msg)


def create_mock_orm_from_api(api_model: Any, excluded_fields: Optional[Set[str]] = None) -> Mock:
    """
    Create a Mock ORM object from API model using all model fields.
    
    Args:
        api_model: API model instance with model_fields attribute
        excluded_fields: Fields to exclude from the mock
        
    Returns:
        Mock object with attributes set from API model
        
    Example:
        mock_orm = create_mock_orm_from_api(api_meal)
        # Use mock_orm in tests that need ORM objects
    """
    if not hasattr(api_model.__class__, 'model_fields'):
        raise ValueError(f"API model {type(api_model)} does not have model_fields attribute")
    
    excluded_fields = excluded_fields or set()
    mock_orm = Mock()
    
    for field_name in api_model.__class__.model_fields.keys():
        if field_name not in excluded_fields:
            setattr(mock_orm, field_name, getattr(api_model, field_name))
    
    return mock_orm


def create_mock_orm_from_kwargs(orm_kwargs: Dict[str, Any]) -> Mock:
    """
    Create a Mock ORM object from ORM kwargs dictionary.
    
    Args:
        orm_kwargs: Dictionary of ORM field values
        
    Returns:
        Mock object with attributes set from kwargs
        
    Example:
        orm_kwargs = api_meal.to_orm_kwargs()
        mock_orm = create_mock_orm_from_kwargs(orm_kwargs)
    """
    mock_orm = Mock()
    for key, value in orm_kwargs.items():
        setattr(mock_orm, key, value)
    return mock_orm


# =============================================================================
# ROUND-TRIP CONVERSION TESTING
# =============================================================================

def test_api_domain_roundtrip(api_model: Any, excluded_fields: Optional[Set[str]] = None) -> None:
    """
    Test API → Domain → API round-trip conversion maintains data integrity.
    
    Args:
        api_model: Original API model instance
        excluded_fields: Fields to exclude from comparison
        
    Raises:
        AssertionError: If round-trip doesn't preserve data
        
    Example:
        test_api_domain_roundtrip(api_meal)
    """
    # API → Domain
    domain_obj = api_model.to_domain()
    
    # Domain → API  
    roundtrip_api = type(api_model).from_domain(domain_obj)
    
    # Compare original API with round-trip API
    differences = compare_api_to_api(api_model, roundtrip_api, excluded_fields)
    if differences:
        raise AssertionError(f"API → Domain → API round-trip failed:\n" + 
                           "\n".join(f"  - {diff}" for diff in differences))


def test_api_orm_roundtrip(api_model: Any, excluded_fields: Optional[Set[str]] = None) -> None:
    """
    Test API → ORM kwargs → Mock ORM → API round-trip conversion.
    
    Args:
        api_model: Original API model instance
        excluded_fields: Fields to exclude from comparison
        
    Raises:
        AssertionError: If round-trip doesn't preserve data
        
    Example:
        test_api_orm_roundtrip(api_meal)
    """
    # API → ORM kwargs
    orm_kwargs = api_model.to_orm_kwargs()
    
    # ORM kwargs → Mock ORM → API
    mock_orm = create_mock_orm_from_kwargs(orm_kwargs)
    roundtrip_api = type(api_model).from_orm_model(mock_orm)
    
    # Compare original API with round-trip API
    differences = compare_api_to_api(api_model, roundtrip_api, excluded_fields)
    if differences:
        raise AssertionError(f"API → ORM → API round-trip failed:\n" + 
                           "\n".join(f"  - {diff}" for diff in differences))


def compare_api_to_api(api_model1: Any, api_model2: Any, excluded_fields: Optional[Set[str]] = None) -> List[str]:
    """
    Compare two API model instances using dynamic field iteration.
    
    Args:
        api_model1: First API model instance
        api_model2: Second API model instance
        excluded_fields: Fields to exclude from comparison
        
    Returns:
        List of differences found, empty if objects match
    """
    if type(api_model1) != type(api_model2):
        return [f"Type mismatch: {type(api_model1)} != {type(api_model2)}"]
    
    if not hasattr(api_model1, 'model_fields'):
        raise ValueError(f"API model {type(api_model1)} does not have model_fields attribute")
    
    excluded_fields = excluded_fields or set()
    differences = []
    
    for field_name in api_model1.model_fields.keys():
        if field_name in excluded_fields:
            continue
            
        try:
            value1 = getattr(api_model1, field_name)
            value2 = getattr(api_model2, field_name)
            
            if not _values_are_equivalent(value1, value2, field_name):
                differences.append(f"Field '{field_name}': API1({value1}) != API2({value2})")
                
        except Exception as e:
            differences.append(f"Field '{field_name}': Unexpected error - {e}")
    
    return differences


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _values_are_equivalent(value1: Any, value2: Any, field_name: str) -> bool:
    """
    Check if two values are equivalent, handling special cases like collections, None values, nested objects, etc.
    """
    # Handle None values
    if value1 is None and value2 is None:
        return True
    if value1 is None or value2 is None:
        return False
    
    # Handle exact equality first
    if value1 == value2:
        return True
    
    # Handle collection type conversions (set ↔ frozenset ↔ list)
    if _are_equivalent_collections(value1, value2):
        return True
    
    # Handle float comparisons with tolerance
    if isinstance(value1, float) and isinstance(value2, float):
        return abs(value1 - value2) < 1e-10
    
    # Handle enum vs string comparisons (check for value attribute existence)
    if (hasattr(value1, 'value') and not isinstance(value1, (int, float, str)) and 
        hasattr(value2, 'value') and not isinstance(value2, (int, float, str))):
        return value1.value == value2.value
    if (hasattr(value1, 'value') and not isinstance(value1, (int, float, str)) and 
        isinstance(value2, str)):
        return value1.value == value2
    if (isinstance(value1, str) and 
        hasattr(value2, 'value') and not isinstance(value2, (int, float, str))):
        return value1 == value2.value
    
    # Handle nested objects
    if _are_nested_objects_equivalent(value1, value2):
        return True
    
    return False


def _are_nested_objects_equivalent(value1: Any, value2: Any, visited: Optional[Set[int]] = None) -> bool:
    """
    Check if two nested objects are equivalent by recursively comparing their attributes.
    Handles circular references with a visited set.
    """
    if visited is None:
        visited = set()
    
    # Check for circular references
    obj1_id = id(value1)
    obj2_id = id(value2)
    if obj1_id in visited or obj2_id in visited:
        return obj1_id == obj2_id
    
    visited.add(obj1_id)
    visited.add(obj2_id)
    
    try:
        # Handle primitive types - if we get here, they're not equivalent
        if isinstance(value1, (int, float, str, bool, type(None))):
            return False
        if isinstance(value2, (int, float, str, bool, type(None))):
            return False
        
        # Check if both are the same type or compatible types
        if not _are_compatible_nested_types(value1, value2):
            return False
        
        # Get field names from both objects
        fields1 = _get_object_field_names(value1)
        fields2 = _get_object_field_names(value2)
        
        # If objects have different field sets, they're not equivalent
        if set(fields1) != set(fields2):
            return False
        
        # Compare each field recursively
        for field_name in fields1:
            try:
                attr1 = getattr(value1, field_name)
                attr2 = getattr(value2, field_name)
                
                # Recursively compare nested attributes
                if not _values_are_equivalent(attr1, attr2, field_name):
                    return False
                    
            except AttributeError:
                # If one object has the field and the other doesn't, they're not equivalent
                return False
        
        return True
        
    finally:
        visited.discard(obj1_id)
        visited.discard(obj2_id)


def _are_compatible_nested_types(value1: Any, value2: Any) -> bool:
    """Check if two values are compatible nested object types."""
    # Same type
    if type(value1) == type(value2):
        return True
    
    # Both are dataclasses
    if dataclasses.is_dataclass(value1) and dataclasses.is_dataclass(value2):
        return True
    
    # Both are attrs objects
    if hasattr(value1, '__attrs_attrs__') and hasattr(value2, '__attrs_attrs__'):
        return True
    
    # Both are ValueObjects
    if isinstance(value1, ValueObject) and isinstance(value2, ValueObject):
        return True
    
    # Both are Entities
    if isinstance(value1, Entity) and isinstance(value2, Entity):
        return True
    
    # Both have __dict__ (regular objects)
    if hasattr(value1, '__dict__') and hasattr(value2, '__dict__'):
        return True
    
    return False


def _are_equivalent_collections(value1: Any, value2: Any) -> bool:
    """Check if two collections are equivalent despite different types, handling nested objects."""
    collection_types = (list, set, frozenset, tuple)
    
    if not (isinstance(value1, collection_types) and isinstance(value2, collection_types)):
        return False
    
    try:
        # Convert to lists first to handle nested comparisons
        list1 = list(value1) if hasattr(value1, '__iter__') else [value1]
        list2 = list(value2) if hasattr(value2, '__iter__') else [value2]
        
        # Check if lengths match
        if len(list1) != len(list2):
            return False
        
        # For sets/frozensets, try to match elements without regard to order
        if isinstance(value1, (set, frozenset)) or isinstance(value2, (set, frozenset)):
            return _are_equivalent_unordered_collections(list1, list2)
        
        # For ordered collections (list, tuple), compare element by element
        for item1, item2 in zip(list1, list2):
            if not _values_are_equivalent(item1, item2, "collection_item"):
                return False
        
        return True
        
    except (TypeError, ValueError):
        return False


def _are_equivalent_unordered_collections(list1: List[Any], list2: List[Any]) -> bool:
    """Check if two unordered collections are equivalent by matching each element."""
    if len(list1) != len(list2):
        return False
    
    # Try to match each element in list1 with an element in list2
    used_indices = set()
    
    for item1 in list1:
        found_match = False
        for i, item2 in enumerate(list2):
            if i in used_indices:
                continue
            if _values_are_equivalent(item1, item2, "collection_item"):
                used_indices.add(i)
                found_match = True
                break
        
        if not found_match:
            return False
    
    return True


def _get_object_field_names(obj: Any) -> List[str]:
    """Get field names from an object (handles dataclasses, attrs, regular objects)."""
    if dataclasses.is_dataclass(obj):
        return [field.name for field in dataclasses.fields(obj)]
    elif hasattr(obj, '__attrs_attrs__'):  # attrs class
        return [attr.name for attr in obj.__attrs_attrs__]
    elif hasattr(obj, '__dict__'):
        return [name for name in obj.__dict__.keys() if not name.startswith('_')]
    else:
        return []
