from __future__ import annotations

import abc
import inspect
from attrs import frozen

@frozen
class ValueObject(abc.ABC):
    """The base class of all value objects.

    Method:
        replace: return a new instance of ValueObjetcs with attributes equal
        to those passed as kwargs to the method. Attributes not passed as
        kwargs will be copied from the ValueObject instance that called the
        method.
    """

    def replace(self, events: list | None = None, **kwargs):
        cls = type(self)
        params = inspect.signature(self.__class__).parameters
        args = {name: getattr(self, name) for name in params}
        args.update(kwargs)
        if not events and "events" in params:
            args["events"] = []
        return cls(**args)
