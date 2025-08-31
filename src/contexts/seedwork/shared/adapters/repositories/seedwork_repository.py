"""
Seedwork Repository Module

This module provides the core repository infrastructure for the seedwork pattern.
The implementation has been split into focused modules for better maintainability:

- filter_mapper.py: Contains FilterColumnMapper, Filter classes and TypeVars
- protocols.py: Contains BaseRepository and CompositeRepository protocols  
- sa_generic_repository.py: Contains the main SaGenericRepository implementation

This file maintains backward compatibility by re-exporting all classes.
"""

from __future__ import annotations

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

# Export everything that was previously available in this file
__all__ = [
    "BaseRepository",
    "CompositeRepository",
    "Filter",
    "FilterColumnMapper",
    "SaGenericRepository",
]
