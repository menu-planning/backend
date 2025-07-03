import inspect
import uuid

from src.contexts.iam.core.domain.entities.user import User
from tests.utils import check_missing_attributes

# def _class_attributes(cls) -> list[str]:
#     attributes = [
#         attr
#         for attr in inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
#         if not (attr[0].startswith("_") or attr[0] == "instance_id")
#     ]
#     return [i[0] for i in attributes]


# def _class_method_attributes(method) -> list[str]:
#     if not inspect.ismethod(method):
#         raise TypeError("The argument must be a class method.")

#     sig = inspect.signature(method)
#     return [param.name for param in sig.parameters.values() if param.name != "cls"]


# def _missing_attributes(cls_or_method, kwargs) -> list[str]:
#     if inspect.isclass(cls_or_method):
#         attribute_names = _class_attributes(cls_or_method)
#     elif inspect.ismethod(cls_or_method):
#         attribute_names = _class_method_attributes(cls_or_method)
#     else:
#         raise TypeError("The first argument must be a class or a class method.")

#     return [attr for attr in attribute_names if attr not in kwargs]


def random_suffix(module_name: str = ""):
    return f"{uuid.uuid4().hex[:6]}{module_name}"


def random_attr(attr=""):
    return f"{attr}-{random_suffix()}"


def random_create_user_classmethod_kwargs(**kwargs) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "id": kwargs.get("id") if "id" in kwargs else random_attr(f"{prefix}id"),
    }
    missing = check_missing_attributes(User.create_user, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_user(**kwargs) -> User:
    return User.create_user(**random_create_user_classmethod_kwargs(**kwargs))
