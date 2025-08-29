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
from .filter_mapper import FilterColumnMapper, Filter, E, S
from .protocols import BaseRepository, CompositeRepository
from .sa_generic_repository import SaGenericRepository

# Export everything that was previously available in this file
__all__ = [
    "FilterColumnMapper",
    "Filter", 
    "BaseRepository",
    "CompositeRepository",
    "SaGenericRepository",
    "E",
    "S",
]
