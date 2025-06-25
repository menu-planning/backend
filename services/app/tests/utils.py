import dataclasses
import inspect
from enum import Enum
from typing import Any

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
