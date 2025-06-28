"""Test suite for Entity cache invalidation mechanism."""

import pytest
from functools import cached_property
from unittest.mock import Mock, patch

from src.contexts.seedwork.shared.domain.entity import Entity


class CacheTestEntity(Entity):
    """Test entity with cached properties for testing cache invalidation."""
    
    def __init__(self, id: str, name: str = "test"):
        super().__init__(id=id)
        self._name = name
        self._computation_count = 0
        
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._increment_version()
        # Invalidate caches that depend on name
        self._invalidate_caches('expensive_computation', 'another_cached_property')
    
    @cached_property
    def expensive_computation(self) -> str:
        """Simulates an expensive computation that should be cached."""
        self._computation_count += 1
        return f"computed_{self._name}_{self._computation_count}"
    
    @cached_property
    def another_cached_property(self) -> int:
        """Another cached property for testing selective invalidation."""
        return len(self._name) * 10
    
    def _update_properties(self, **kwargs) -> None:
        """Override to test cache invalidation in update flow."""
        super()._update_properties(**kwargs)


class TestEntityCacheInvalidation:
    """Test cache invalidation functionality."""
    
    def test_entity_has_cached_attrs_tracking(self):
        """Test that Entity tracks cached attributes."""
        entity = CacheTestEntity("test-id")
        
        # Should have _computed_caches property for tracking (returns frozenset)
        assert hasattr(entity, '_computed_caches')
        assert isinstance(entity._computed_caches, frozenset)
        
        # Should have class-level cached properties registry
        assert hasattr(CacheTestEntity, '_class_cached_properties')
        assert isinstance(CacheTestEntity._class_cached_properties, frozenset)
    
    def test_entity_has_invalidate_caches_method(self):
        """Test that Entity has _invalidate_caches method."""
        entity = CacheTestEntity("test-id")
        
        # Should have _invalidate_caches method
        assert hasattr(entity, '_invalidate_caches')
        assert callable(entity._invalidate_caches)
    
    def test_cached_property_gets_registered_in_cached_attrs(self):
        """Test that cached properties are automatically detected at class creation."""
        # Should automatically detect cached properties
        assert 'expensive_computation' in CacheTestEntity._class_cached_properties
        assert 'another_cached_property' in CacheTestEntity._class_cached_properties
        
        # Instance tracking starts empty
        entity = CacheTestEntity("test-id")
        assert len(entity._computed_caches) == 0
        
        # Access cached properties to trigger tracking
        _ = entity.expensive_computation
        _ = entity.another_cached_property
        
        # Should track that these have been computed
        assert 'expensive_computation' in entity._computed_caches
        assert 'another_cached_property' in entity._computed_caches
    
    def test_cached_property_actually_caches(self):
        """Test that cached properties work correctly."""
        entity = CacheTestEntity("test-id", "original")
        
        # First access should compute
        result1 = entity.expensive_computation
        assert result1 == "computed_original_1"
        assert entity._computation_count == 1
        
        # Second access should use cache
        result2 = entity.expensive_computation
        assert result2 == "computed_original_1"  # Same result
        assert entity._computation_count == 1  # No additional computation
    
    def test_invalidate_caches_clears_specific_cache(self):
        """Test that _invalidate_caches clears specified cached properties."""
        entity = CacheTestEntity("test-id", "original")
        
        # Cache both properties
        _ = entity.expensive_computation
        cached_result = entity.another_cached_property
        
        # Invalidate only expensive_computation
        entity._invalidate_caches('expensive_computation')
        
        # Change underlying data
        entity._name = "changed"
        
        # expensive_computation should recompute
        new_result = entity.expensive_computation
        assert new_result == "computed_changed_2"  # New computation
        
        # another_cached_property should still be cached
        still_cached = entity.another_cached_property
        assert still_cached == cached_result  # Same old result
    
    def test_invalidate_caches_clears_all_when_no_attrs_specified(self):
        """Test that _invalidate_caches clears all caches when no attrs specified."""
        entity = CacheTestEntity("test-id", "original")
        
        # Cache both properties
        _ = entity.expensive_computation
        _ = entity.another_cached_property
        
        # Change underlying data
        entity._name = "changed"
        
        # Invalidate all caches
        entity._invalidate_caches()
        
        # Both should recompute
        new_expensive = entity.expensive_computation
        new_another = entity.another_cached_property
        
        assert new_expensive == "computed_changed_2"  # Recomputed
        assert new_another == 70  # Recomputed: len("changed") * 10
    
    def test_invalidate_caches_logs_debug_message(self):
        """Test that _invalidate_caches logs debug messages when clearing caches."""
        entity = CacheTestEntity("test-id")
        
        # Cache a property
        _ = entity.expensive_computation
        
        # Mock the logger at the module level where it's imported
        with patch('src.contexts.seedwork.shared.domain.entity.logger') as mock_logger:
            entity._invalidate_caches('expensive_computation')
            
            # Should log cache invalidation
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert 'Invalidated' in call_args
            assert 'expensive_computation' in call_args
    
    def test_mutator_methods_should_invalidate_related_caches(self):
        """Test that mutator methods invalidate related cached properties."""
        entity = CacheTestEntity("test-id", "original")
        
        # Cache properties
        original_expensive = entity.expensive_computation
        original_another = entity.another_cached_property
        
        # Mutate through setter (should invalidate caches)
        entity.name = "changed"
        
        # Properties should recompute
        new_expensive = entity.expensive_computation
        new_another = entity.another_cached_property
        
        assert new_expensive != original_expensive
        assert new_another != original_another
        assert new_expensive == "computed_changed_2"
        assert new_another == 70  # len("changed") * 10
    
    def test_update_properties_invalidates_caches(self):
        """Test that _update_properties invalidates caches after successful update."""
        entity = CacheTestEntity("test-id", "original")
        
        # Cache properties
        _ = entity.expensive_computation
        original_another = entity.another_cached_property
        
        # Update properties (this will call name setter + _invalidate_caches)
        entity._update_properties(name="updated")
        
        # Properties should recompute due to cache invalidation
        new_expensive = entity.expensive_computation
        new_another = entity.another_cached_property
        
        # After update_properties: computation count should be 2
        # 1. First access during cache: "computed_original_1"  
        # 2. After invalidation by name setter: "computed_updated_2"
        assert new_expensive == "computed_updated_2"
        assert new_another != original_another
        assert new_another == 70  # len("updated") * 10
    
    def test_nonexistent_cache_invalidation_handles_gracefully(self):
        """Test that invalidating non-existent cache attributes handles gracefully."""
        entity = CacheTestEntity("test-id")
        
        # Should not raise error when trying to invalidate non-existent cache
        entity._invalidate_caches('nonexistent_property')
        
        # Should still work normally
        _ = entity.expensive_computation
        assert entity._computation_count == 1 