from __future__ import annotations

import abc
from itertools import count

from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.shared_kernel.domain.exceptions import (
    BusinessRuleValidationException,
    DiscardedEntityException,
)


class Entity(abc.ABC):
    """The base class of all entities.

    Attriburtes:
        id: A uniteques identifier
        version: An integer version
        discarded: True if this entity is marked as discarded, otherwise False
    """

    _instance_id_generator = count()

    @abc.abstractmethod
    def __init__(self, id: str, discarded: bool = False, version: int = 1):
        self._id = id
        self._discarded = discarded
        self._version = version
        self._instance_id = next(Entity._instance_id_generator)

    def _increment_version(self):
        self._version += 1

    @property
    def id(self):
        """A string unique identifier for the entity."""
        return self._id

    @property
    def discarded(self):
        """True if this entity is marked as discarded, otherwise False."""
        return self._discarded

    @property
    def version(self):
        """An integer version for the entity."""
        return self._version

    @property
    def instance_id(self):
        """An integer instance id for the entity."""
        return self._instance_id

    def _discard(self):
        self._check_not_discarded()
        self._discarded = True
        self._increment_version()

    def _check_not_discarded(self):
        if self._discarded:
            raise DiscardedEntityException(
                f"Attempt to use discared ententiy {self.__class__.__name__}(id={self._id}, version={self._version})"
            )

    @staticmethod
    def check_rule(rule: BusinessRule):
        if rule.is_broken():
            raise BusinessRuleValidationException(rule)

    @abc.abstractmethod
    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        if not kwargs:
            return
        for key, value in kwargs.items():
            if key[0] == "_":
                raise AttributeError(f"{key} is private.")
            if not isinstance(getattr(self.__class__, key), property):
                raise TypeError(f"{key} is not a property.")
            if getattr(self.__class__, key).fset is None:
                raise AttributeError(f"{key} has no setter.")
            # if not isinstance(value, get_type_hints(self.__class__.__init__)[key]):
            #     raise TypeError(f"Invalid type for {key}. {type(value)} != {type(key)}")
            # if issubclass(
            #     collections_abc.Sequence, get_type_hints(self.__class__.__init__)[key]
            # ) and not isinstance(str, get_type_hints(self.__class__.__init__)[key]):
            #     raise TypeError("Cannot update iterable directly.")
            # try:
            #     iter(value)
            #     raise TypeError("Cannot update iterable directly.")
            # except TypeError:
            #     pass
        for key, value in kwargs.items():
            getattr(self.__class__, key).fset(self, value)
            self._version -= 1
        else:
            self._increment_version()

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._id}, version={self._version})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, __o: object) -> bool:
        return type(self) == type(__o) and self.id == __o.id
