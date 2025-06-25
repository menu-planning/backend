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


def _class_method_attributes(method) -> list[str]:
    if not inspect.ismethod(method):
        raise TypeError("The argument must be a class method.")

    sig = inspect.signature(method)
    return [param.name for param in sig.parameters.values() if param.name != "cls"]


def check_missing_attributes(cls_or_method, kwargs) -> list[str]:
    if inspect.isclass(cls_or_method):
        attribute_names = _class_attributes(cls_or_method)
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
