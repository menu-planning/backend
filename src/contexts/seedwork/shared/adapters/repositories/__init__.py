# Re-export all classes for backward compatibility
from src.contexts.seedwork.shared.adapters.repositories.filter_mapper import (
    Filter,
    FilterColumnMapper,
)
from src.contexts.seedwork.shared.adapters.repositories.protocols import (
    BaseRepository,
    CompositeRepository,
)
from src.contexts.seedwork.shared.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)

# Export everything that was previously available
__all__ = [
    "FilterColumnMapper",
    "Filter",
    "BaseRepository",
    "CompositeRepository",
    "SaGenericRepository"
]
