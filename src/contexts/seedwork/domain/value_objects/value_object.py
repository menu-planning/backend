"""Base class for immutable domain value objects."""

from __future__ import annotations

import inspect

from attrs import frozen


@frozen
class ValueObject:
    """Immutable base for domain value objects.

    Value objects are compared by value and are immutable by default. Use
    ``replace`` to derive a new instance with selected attributes changed.

    Invariants:
        - All attributes must be immutable.
        - Equality determined by value comparison.

    Notes:
        Immutable. Equality by value (all fields).
    """

    def replace(self, events: list | None = None, **kwargs):
        """Return a new instance with provided attributes replaced.

        Args:
            events: Optional events list override. If ``None`` and the model
                declares an ``events`` parameter, it defaults to an empty list.
            **kwargs: Attributes to override on the new instance.

        Returns:
            A new instance of the same class with updated attribute values.
        """
        cls = type(self)
        params = inspect.signature(self.__class__).parameters
        args = {name: getattr(self, name) for name in params}
        args.update(kwargs)
        if not events and "events" in params:
            args["events"] = []
        return cls(**args)
