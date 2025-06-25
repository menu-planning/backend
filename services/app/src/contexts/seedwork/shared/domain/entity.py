from __future__ import annotations

import abc
import functools
from copy import copy
from datetime import datetime
from typing import Any

from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.shared_kernel.domain.exceptions import (
    BusinessRuleValidationException,
    DiscardedEntityException,
)
from src.logging.logger import logger


class Entity(abc.ABC):
    """The base class of all entities.

    Attributes:
        id: A unique identifier
        version: An integer version
        discarded: True if this entity is marked as discarded, otherwise False
        _computed_caches: Read-only frozenset of cached property names that have been computed on this instance
    """

    # Class attribute to store cached property names
    _class_cached_properties: frozenset[str]
    
    # _instance_id_generator = count()

    def __init_subclass__(cls, **kwargs):
        """Automatically detect and register cached properties at class creation time."""
        super().__init_subclass__(**kwargs)
        
        # Find all cached properties in this class and its bases
        cached_properties = set()
        
        for base in cls.__mro__:
            for name, attr in base.__dict__.items():
                if cls._is_cached_property(attr):
                    cached_properties.add(name)
        
        # Store as class attribute for efficiency
        cls._class_cached_properties = frozenset(cached_properties)

    @staticmethod
    def _is_cached_property(attr: Any) -> bool:
        """Detect if an attribute is a cached property or similar caching descriptor."""
        # functools.cached_property (Python 3.8+)
        if hasattr(functools, 'cached_property') and isinstance(attr, functools.cached_property):
            return True
        
        # Custom cached_property implementations often have these characteristics
        if (hasattr(attr, '__get__') and 
            hasattr(attr, '__set_name__') and 
            hasattr(attr, 'func')):
            return True
            
        # lru_cache decorated methods (for backward compatibility during transition)
        if hasattr(attr, '__wrapped__') and hasattr(attr, 'cache_info'):
            return True
            
        return False

    @abc.abstractmethod
    def __init__(self, id: str, discarded: bool = False, version: int = 1, created_at: datetime | None = None, updated_at: datetime | None = None):
        self._id = id
        self._discarded = discarded
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at
        
        # Instance-level tracking of which caches have been computed
        self.__computed_caches: set[str] = set()
        # self._instance_id = next(Entity._instance_id_generator)

    def _increment_version(self):
        self._version += 1

    def _invalidate_caches(self, *attrs: str) -> None:
        """Invalidate cached properties.
        
        Args:
            *attrs: Specific attribute names to invalidate. If none provided,
                   invalidates all cached properties that have been computed.
                   
        This method works with:
        - functools.cached_property (deletes from instance __dict__)
        - lru_cache decorated methods (calls cache_clear)
        - Any custom caching that stores in instance __dict__
        """
        if attrs:
            # Validate that requested attributes are actually cached properties
            class_cached = getattr(self.__class__, '_class_cached_properties', set())
            invalid_attrs = set(attrs) - class_cached
            if invalid_attrs:
                logger.warning(f"Attempted to invalidate non-cached properties: {invalid_attrs}")
            
            attrs_to_invalidate = set(attrs) & class_cached
        else:
            # Invalidate all computed caches
            attrs_to_invalidate = getattr(self.__class__, '_class_cached_properties', set())
        
        invalidated_count = 0
        
        for attr_name in attrs_to_invalidate:
            if self._invalidate_single_cache(attr_name):
                invalidated_count += 1
                self.__computed_caches.discard(attr_name)
        
        if invalidated_count > 0:
            logger.debug(f"Invalidated {invalidated_count} cache(s) for {self.__class__.__name__}: {sorted(attrs_to_invalidate)}")

    def _invalidate_single_cache(self, attr_name: str) -> bool:
        """Invalidate a single cached property. Returns True if cache was cleared."""
        # Method 1: cached_property stores values in instance __dict__
        if attr_name in self.__dict__:
            del self.__dict__[attr_name]
            return True
        
        # Method 2: lru_cache decorated methods
        attr = getattr(self.__class__, attr_name, None)
        if attr and hasattr(attr, 'cache_clear'):
            try:
                attr.cache_clear()
                return True
            except Exception as e:
                logger.warning(f"Failed to clear lru_cache for {attr_name}: {e}")
        
        # Method 3: Try standard descriptor deletion
        if hasattr(self, attr_name):
            attr_descriptor = getattr(type(self), attr_name, None)
            if attr_descriptor and hasattr(attr_descriptor, '__delete__'):
                try:
                    attr_descriptor.__delete__(self)
                    return True
                except AttributeError:
                    # Cache wasn't set, nothing to clear
                    pass
                except Exception as e:
                    logger.warning(f"Failed to delete cache for {attr_name}: {e}")
        
        return False

    def __getattribute__(self, name: str):
        """Track when cached properties are accessed for the first time."""
        value = super().__getattribute__(name)
        
        # Only track if this is a known cached property and we haven't seen it before
        # Optimize by checking _class_cached_properties existence once
        if name not in ('_Entity__computed_caches', '_class_cached_properties', '_computed_caches'):
            class_cached = getattr(type(self), '_class_cached_properties', None)
            if (class_cached and 
                name in class_cached and 
                hasattr(self, '_Entity__computed_caches') and 
                name not in self.__computed_caches):
                self.__computed_caches.add(name)
        
        return value

    @property
    def _computed_caches(self) -> frozenset[str]:
        """Read-only view of computed caches."""
        return frozenset(self.__computed_caches)

    def get_cache_info(self) -> dict[str, Any]:
        """Return information about cached properties.
        
        Returns:
            Dictionary containing:
            - total_cached_properties: Total number of cached properties in the class
            - computed_caches: Number of caches that have been computed on this instance
            - cache_names: Sorted list of computed cache names
        """
        return {
            'total_cached_properties': len(getattr(self.__class__, '_class_cached_properties', set())),
            'computed_caches': len(self.__computed_caches),
            'cache_names': sorted(self.__computed_caches)
        }

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
    def created_at(self):
        """The datetime when the entity was created."""
        return self._created_at
    
    @property
    def updated_at(self):
        """The datetime when the entity was updated."""
        return self._updated_at

    # @property
    # def instance_id(self):
    #     """An integer instance id for the entity."""
    #     return self._instance_id

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

    @staticmethod
    def check_multiple_rules(rules: list[BusinessRule]):
        for rule in rules:
            Entity.check_rule(rule)

    @abc.abstractmethod
    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        if not kwargs:
            return
        version = copy(self.version)
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
        # else:
        self._version = version + 1
        # Invalidate all caches after successful property updates
        self._invalidate_caches()

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._id}, version={self._version})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, __o: Entity) -> bool:
        return type(self) == type(__o) and self.id == __o.id
