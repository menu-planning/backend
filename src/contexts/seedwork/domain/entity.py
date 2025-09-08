from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from src.contexts.seedwork.domain.rules import BusinessRule

import abc
import functools
from copy import copy
from typing import Any

from src.contexts.shared_kernel.domain.exceptions import (
    BusinessRuleValidationError,
    DiscardedEntityError,
)
from src.logging.logger import StructlogFactory


class Entity(abc.ABC):
    """Base entity with instance-level caching and update contract.

    Provides:
    - Automatic discovery of cached properties at class creation.
    - Targeted or full cache invalidation on mutation.
    - A standardized multi-property update flow with a single version bump.

    Caching Strategy:
        - PRIMARY: Uses @cached_property for instance-level caching (thread-safe)
        - BACKWARD COMPATIBILITY: Supports @lru_cache detection/invalidation (not used)
        - Thread Safety: @cached_property is thread-safe for both Lambda and FastAPI

    Invariants:
        - Entity ID must be unique and immutable.
        - Version must increment on each update.
        - Discarded entities cannot be modified.

    Notes:
        - Support both standard property setters and protected setters named
          ``_set_<property>``. If both exist for a property, the protected setter
          takes precedence. This helps maintain aggregate boundaries without
          runtime-heavy enforcement.
        - After successful updates, all computed caches are invalidated to keep
          derived values consistent.
        - Allowed transitions: ACTIVE -> DISCARDED (one-way).
    """

    # Class attribute to store cached property names
    _class_cached_properties: set[str]

    def __init_subclass__(cls, **kwargs):
        """Automatically detect and register cached properties at class creation time.

        Detects:
            - @cached_property (PRIMARY - instance-level, thread-safe)
            - @lru_cache decorated methods (BACKWARD COMPATIBILITY - not currently used)
            - Custom caching descriptors

        Notes:
            Runs during class creation. Registers all cached properties from
            this class and its base classes.
        """
        super().__init_subclass__(**kwargs)

        # Find all cached properties in this class and its bases
        cached_properties = set()

        for base in cls.__mro__:
            for name, attr in base.__dict__.items():
                if cls._is_cached_property(attr):
                    cached_properties.add(name)

        # Store as class attribute for efficiency
        cls._class_cached_properties = set(cached_properties)

    @staticmethod
    def _is_cached_property(attr: Any) -> bool:
        """Detect if an attribute is a cached property or similar caching descriptor.

        Supports:
            - functools.cached_property (PRIMARY - instance-level, thread-safe)
            - Custom cached_property implementations
            - lru_cache decorated methods (BACKWARD COMPATIBILITY - not currently used)

        Args:
            attr: Attribute to check for caching behavior.

        Returns:
            True if the attribute is a cached property, False otherwise.
        """
        # functools.cached_property (Python 3.8+)
        if hasattr(functools, "cached_property") and isinstance(
            attr, functools.cached_property
        ):
            return True

        # Custom cached_property implementations often have these characteristics
        if (
            hasattr(attr, "__get__")
            and hasattr(attr, "__set_name__")
            and hasattr(attr, "func")
        ):
            return True

        # lru_cache decorated methods (backward compatibility support - not currently used)
        return hasattr(attr, "__wrapped__") and hasattr(attr, "cache_info")

    @abc.abstractmethod
    def __init__(
        self,
        *,
        id: str,
        discarded: bool = False,
        version: int = 1,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize entity with identity and metadata.

        Args:
            id: Unique identifier for the entity.
            discarded: Whether the entity is marked as discarded.
            version: Version number for optimistic locking.
            created_at: Timestamp when entity was created.
            updated_at: Timestamp when entity was last updated.
        """
        self._id = id
        self._discarded = discarded
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at

        # Instance-level tracking of which caches have been computed
        self.__computed_caches: set[str] = set()

    def _increment_version(self):
        """Increment the entity version number.

        Notes:
            Called automatically during property updates.
        """
        self._version += 1

    def _invalidate_caches(self, *attrs: str) -> None:
        """Invalidate cached properties.

        Args:
            *attrs: Specific attribute names to invalidate. If none provided,
                   invalidates all cached properties that have been computed.

        Notes:
            This method works with:
            - functools.cached_property (deletes from instance __dict__) - PRIMARY USAGE
            - lru_cache decorated methods (calls cache_clear) - BACKWARD COMPATIBILITY ONLY
            - Any custom caching that stores in instance __dict__
        """
        if attrs:
            # Validate that requested attributes are actually cached properties
            class_cached = getattr(self.__class__, "_class_cached_properties", set())
            invalid_attrs = set(attrs) - class_cached
            if invalid_attrs:
                logger = StructlogFactory.get_logger("entity.cache")
                logger.warning(
                    "Attempted to invalidate non-cached properties",
                    entity_class=self.__class__.__name__,
                    id=self._id,
                    invalid_properties=list(invalid_attrs),
                    valid_cached_properties=list(class_cached),
                )

            attrs_to_invalidate = set(attrs) & class_cached
        else:
            # Invalidate all computed caches
            attrs_to_invalidate = getattr(
                self.__class__, "_class_cached_properties", set()
            )

        invalidated_count = 0

        for attr_name in attrs_to_invalidate:
            if self._invalidate_single_cache(attr_name):
                invalidated_count += 1
                self.__computed_caches.discard(attr_name)

        # Only log cache invalidation when it's significant (multiple caches or all caches)
        if invalidated_count > 2 or (not attrs and invalidated_count > 0):
            logger = StructlogFactory.get_logger("entity.cache")
            logger.debug(
                "Significant cache invalidation completed",
                entity_class=self.__class__.__name__,
                id=self._id,
                entity_version=self._version,
                invalidated_count=invalidated_count,
                invalidated_properties=sorted(attrs_to_invalidate),
                is_full_invalidation=not bool(attrs),
            )

    def _invalidate_single_cache(self, attr_name: str) -> bool:
        """Invalidate a single cached property.

        Args:
            attr_name: Name of the cached property to invalidate.

        Returns:
            True if cache was cleared, False otherwise.
        """
        # Method 1: cached_property stores values in instance __dict__
        if attr_name in self.__dict__:
            del self.__dict__[attr_name]
            return True

        # Method 2: lru_cache decorated methods (backward compatibility support)
        attr = getattr(self.__class__, attr_name, None)
        if attr and hasattr(attr, "cache_clear"):
            try:
                attr.cache_clear()
            except Exception as e:
                logger = StructlogFactory.get_logger("entity.cache")
                logger.warning(
                    "Failed to clear lru_cache (backward compatibility)",
                    entity_class=self.__class__.__name__,
                    id=self._id,
                    cache_property=attr_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
            else:
                return True

        # Method 3: Try standard descriptor deletion
        if hasattr(self, attr_name):
            attr_descriptor = getattr(type(self), attr_name, None)
            if attr_descriptor and hasattr(attr_descriptor, "__delete__"):
                try:
                    attr_descriptor.__delete__(self)
                except AttributeError:
                    # Cache wasn't set, nothing to clear
                    pass
                except Exception as e:
                    logger = StructlogFactory.get_logger("entity.cache")
                    logger.warning(
                        "Failed to delete cache descriptor",
                        entity_class=self.__class__.__name__,
                        id=self._id,
                        cache_property=attr_name,
                        error_type=type(e).__name__,
                        error_message=str(e),
                    )
                else:
                    return True

        return False

    def __getattribute__(self, name: str):
        """Track when cached properties are accessed for the first time.

        Args:
            name: Name of the attribute being accessed.

        Returns:
            The attribute value.

        Notes:
            Automatically tracks first access to cached properties for
            efficient invalidation later.
        """
        value = super().__getattribute__(name)

        # Only track if this is a known cached property and we haven't seen it before
        # Optimize by checking _class_cached_properties existence once
        if name not in (
            "_Entity__computed_caches",
            "_class_cached_properties",
            "_computed_caches",
        ):
            class_cached = getattr(type(self), "_class_cached_properties", None)
            if (
                class_cached
                and name in class_cached
                and hasattr(self, "_Entity__computed_caches")
                and name not in self.__computed_caches
            ):
                self.__computed_caches.add(name)

        return value

    @property
    def _computed_caches(self) -> set[str]:
        """Read-only view of computed caches.

        Returns:
            Set of cache property names that have been computed on this instance.
        """
        return set(self.__computed_caches)

    def get_cache_info(self) -> dict[str, Any]:
        """Return information about cached properties.

        Returns:
            Dictionary containing:
            - total_cached_properties: Total number of cached properties in the class
            - computed_caches: Number of caches that have been computed on this instance
            - cache_names: Sorted list of computed cache names
        """
        return {
            "total_cached_properties": len(
                getattr(self.__class__, "_class_cached_properties", set())
            ),
            "computed_caches": len(self.__computed_caches),
            "cache_names": sorted(self.__computed_caches),
        }

    @property
    def id(self):
        """A string unique identifier for the entity.

        Returns:
            Unique identifier string.
        """
        return self._id

    @property
    def discarded(self):
        """True if this entity is marked as discarded, otherwise False.

        Returns:
            True if entity is discarded, False otherwise.
        """
        return self._discarded

    @property
    def version(self):
        """An integer version for the entity.

        Returns:
            Current version number for optimistic locking.
        """
        return self._version

    @property
    def created_at(self):
        """The datetime when the entity was created.

        Returns:
            Creation timestamp or None if not set.
        """
        return self._created_at

    @property
    def updated_at(self):
        """The datetime when the entity was updated.

        Returns:
            Last update timestamp or None if not set.
        """
        return self._updated_at

    def _discard(self):
        """Mark the entity as discarded and increment version.

        Raises:
            DiscardedEntityError: If entity is already discarded.
        """
        self._check_not_discarded()
        self._discarded = True
        self._increment_version()

    def _check_not_discarded(self):
        """Raise error if entity is discarded.

        Raises:
            DiscardedEntityError: If entity is discarded.
        """
        if self._discarded:
            class_name = self.__class__.__name__
            id = self._id
            version = self._version
            message = (
                f"Attempt to use discarded entity {class_name}"
                f"(id={id}, version={version})"
            )
            raise DiscardedEntityError(message)

    @staticmethod
    def check_rule(rule: BusinessRule):
        """Check if a business rule is broken and raise error if so.

        Args:
            rule: Business rule to validate.

        Raises:
            BusinessRuleValidationError: If the rule is broken.
        """
        if rule.is_broken():
            raise BusinessRuleValidationError(rule)

    @staticmethod
    def check_multiple_rules(rules: list[BusinessRule]):
        """Check multiple business rules and raise error if any are broken.

        Args:
            rules: List of business rules to validate.

        Raises:
            BusinessRuleValidationError: If any rule is broken.
        """
        for rule in rules:
            Entity.check_rule(rule)

    def update_properties(self, **kwargs) -> None:
        """Update multiple properties following standardized contract.

        This is the public API for property updates. Delegates to _update_properties
        which now supports:
        - Standard property setters (existing pattern)
        - Protected setter methods (_set_* pattern like Recipe)
        - Optional post-update hooks (_post_update_hook)
        - Single version increment per update operation
        - Cache invalidation after successful updates

        Args:
            **kwargs: Property names and values to update.

        Raises:
            AttributeError: If property is private, doesn't exist, or has no setter.
            TypeError: If property is not a valid property descriptor.
            DiscardedEntityError: If entity is discarded.
        """
        self._update_properties(**kwargs)

    def _update_properties(self, **kwargs) -> None:
        """Enhanced implementation supporting standardized update contract.

        Contract Flow:
        1. **Validate**: Check all properties exist, are settable, and not private
        2. **Apply**: Update all properties using setters or protected methods
        3. **Post-update**: Call optional _post_update_hook for domain-specific logic
        4. **Version bump**: Increment version exactly once per update operation
        5. **Cache invalidate**: Clear all cached properties to maintain consistency

        Supported Patterns:
        - Standard property setters (most entities): Uses property.fset
        - Protected setter methods (Recipe pattern): Uses _set_property_name methods
        - Mixed patterns: Protected setters take priority over standard setters

        Args:
            **kwargs: Property names and values to update.
        """
        self._check_not_discarded()
        if not kwargs:
            return

        # Only log property updates when updating multiple properties or for debugging
        if len(kwargs) > 1:
            logger = StructlogFactory.get_logger("entity.update")
            logger.debug(
                "Starting multi-property update operation",
                entity_class=self.__class__.__name__,
                id=self._id,
                current_version=self._version,
                properties_to_update=list(kwargs.keys()),
                property_count=len(kwargs),
            )

        # Store original version for single increment
        original_version = copy(self.version)

        # Phase 1: Validate all properties before making any changes
        self._validate_update_properties(**kwargs)

        # Phase 2: Apply all property updates
        self._apply_property_updates(original_version, **kwargs)

        # Phase 3: Post-update processing
        self._post_update_processing(**kwargs)

        # Only log completion for multi-property updates
        if len(kwargs) > 1:
            logger = StructlogFactory.get_logger("entity.update")
            logger.debug(
                "Multi-property update operation completed",
                entity_class=self.__class__.__name__,
                id=self._id,
                previous_version=original_version,
                new_version=self._version,
                updated_properties=list(kwargs.keys()),
            )

    def _validate_update_properties(self, **kwargs) -> None:
        """Validate all properties can be updated before making changes.

        Args:
            **kwargs: Property names and values to validate.

        Raises:
            AttributeError: If property is private or has no setter.
            TypeError: If property doesn't exist or is not a property.
        """
        for key in kwargs:
            # Check for private properties
            if key.startswith("_"):
                message = f"{key} is private."
                raise AttributeError(message)

            # Check if property exists and is valid
            if not hasattr(self.__class__, key):
                # Check for protected setter method (Recipe pattern)
                if not hasattr(self, f"_set_{key}"):
                    message = f"{key} is not a property."
                    raise TypeError(message)
            else:
                # Standard property validation
                property_descriptor = getattr(self.__class__, key)
                if not isinstance(property_descriptor, property):
                    message = f"{key} is not a property."
                    raise TypeError(message)
                if property_descriptor.fset is None and not hasattr(
                    self, f"_set_{key}"
                ):
                    message = f"{key} has no setter."
                    raise AttributeError(message)

    def _apply_property_updates(self, original_version: int, **kwargs) -> None:
        """Apply all property updates using appropriate setters.

        Args:
            original_version: Version number before updates.
            **kwargs: Property names and values to update.
        """
        for key, value in kwargs.items():
            # Check for protected setter method first (Recipe pattern)
            protected_setter = f"_set_{key}"
            if hasattr(self, protected_setter):
                # Use protected setter method
                setter_method = getattr(self, protected_setter)
                setter_method(value)
            else:
                # Use standard property setter
                property_descriptor = getattr(self.__class__, key)
                property_descriptor.fset(self, value)

        # Set version manually to original + 1 to avoid multiple increments
        # This ensures version increments exactly once per update operation
        self._version = original_version + 1

    def _post_update_processing(self, **kwargs) -> None:
        """Handle post-update processing: cache invalidation and hooks.

        Args:
            **kwargs: Property names and values that were updated.
        """
        # Phase 1: Cache invalidation (always happens)
        self._invalidate_caches()

        # Phase 2: Optional domain-specific post-update hook
        if hasattr(self, "_post_update_hook"):
            self._post_update_hook(**kwargs)

    def __repr__(self):
        """Return string representation of the entity.

        Returns:
            String representation in format "{ClassName}(id={id}, version={version})".
        """
        return f"{self.__class__.__name__}(id={self._id}, version={self._version})"

    def __hash__(self) -> int:
        """Return hash value for the entity.

        Returns:
            Hash value based on entity ID.
        """
        return hash(self._id)

    def __eq__(self, __o: Entity, /) -> bool:
        """Check if this entity equals another entity.

        Args:
            __o: Entity to compare with.

        Returns:
            True if entities have the same type and ID, False otherwise.
        """
        return isinstance(__o, type(self)) and self.id == __o.id
