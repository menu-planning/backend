"""Test suite for Enhanced Entity update_properties - TDD approach.

This test suite validates the enhanced Entity update_properties that supports:
- Standard property setters (current pattern)
- Protected setter methods (_set_* pattern like Recipe)  
- Optional post-update hooks (_post_update_hook)
- Standardized public update_properties API
- All current validation and cache invalidation logic
"""

import pytest
from functools import cached_property
from unittest.mock import Mock, patch, call
from copy import copy

from src.contexts.seedwork.shared.domain.entity import Entity


class TestStandardEntity(Entity):
    """Test entity with standard property setters."""
    
    def __init__(self, id: str, name: str = "test", description: str = "desc"):
        super().__init__(id=id)
        self._name = name
        self._description = description
        self._computation_count = 0
        
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._increment_version()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        self._description = value
        self._increment_version()
    
    @cached_property
    def expensive_computation(self) -> str:
        """Cached property to test cache invalidation."""
        self._computation_count += 1
        return f"computed_{self._name}_{self._computation_count}"


class TestEntityWithHooks(Entity):
    """Test entity with post-update hooks for domain events."""
    
    def __init__(self, id: str, name: str = "test"):
        super().__init__(id=id)
        self._name = name
        self._domain_events_fired = []
        
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._increment_version()
    
    def _post_update_hook(self, **kwargs) -> None:
        """Custom hook for domain-specific logic after updates."""
        self._domain_events_fired.append(f"Updated: {list(kwargs.keys())}")


class TestEntityWithProtectedSetters(Entity):
    """Test entity with protected setter pattern like Recipe."""
    
    def __init__(self, id: str, name: str = "test", description: str = "desc"):
        super().__init__(id=id)
        self._name = name
        self._description = description
        
    @property
    def name(self) -> str:
        return self._name
    
    def _set_name(self, value: str) -> None:
        """Protected setter following Recipe pattern."""
        self._name = value
        self._increment_version()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        """Mixed pattern: standard setter for some properties."""
        self._description = value
        self._increment_version()


class TestEnhancedEntityUpdateProperties:
    """Test enhanced Entity update_properties behavior."""
    
    def test_standard_entity_update_properties_flow(self):
        """Test standard update_properties flow with property setters."""
        entity = TestStandardEntity("test-id", "original", "original_desc")
        original_version = entity.version
        
        # Cache a property
        _ = entity.expensive_computation
        
        # Update properties using enhanced Entity
        entity.update_properties(name="updated", description="updated_desc")
        
        # Verify updates applied
        assert entity.name == "updated"
        assert entity.description == "updated_desc"
        
        # Verify version incremented once (enhanced behavior)
        assert entity.version == original_version + 1
        
        # Verify cache invalidated
        new_computation = entity.expensive_computation
        assert "updated" in new_computation
        assert entity._computation_count == 2  # Recomputed after cache invalidation
    
    def test_entity_with_post_update_hooks(self):
        """Test that post-update hooks are called when present."""
        entity = TestEntityWithHooks("test-id", "original")
        
        # Update property
        entity.update_properties(name="updated")
        
        # Verify hook was called
        assert "Updated: ['name']" in entity._domain_events_fired
        assert entity.name == "updated"
    
    def test_entity_with_protected_setters(self):
        """Test enhanced Entity supports protected setter pattern."""
        entity = TestEntityWithProtectedSetters("test-id", "original", "original_desc")
        
        # Update using protected setter (name) and standard setter (description)
        entity.update_properties(name="updated_name", description="updated_desc")
        
        assert entity.name == "updated_name"  # Via _set_name
        assert entity.description == "updated_desc"  # Via standard setter
    
    def test_entity_validates_private_properties(self):
        """Test that private properties are rejected."""
        entity = TestStandardEntity("test-id")
        
        with pytest.raises(AttributeError, match="_private_prop is private"):
            entity.update_properties(_private_prop="value")
    
    def test_entity_validates_property_exists(self):
        """Test that non-existent properties are rejected."""
        entity = TestStandardEntity("test-id")
        
        with pytest.raises(TypeError, match="nonexistent is not a property"):
            entity.update_properties(nonexistent="value")
    
    def test_entity_validates_property_has_setter(self):
        """Test that read-only properties are rejected."""
        entity = TestStandardEntity("test-id")
        
        # Mock a read-only property
        with patch.object(entity.__class__, 'id', create=True, 
                         new_callable=lambda: property(lambda self: self._id)):
            with pytest.raises(AttributeError, match="id has no setter"):
                entity.update_properties(id="new-id")
    
    def test_entity_handles_empty_kwargs(self):
        """Test that empty kwargs are handled gracefully."""
        entity = TestStandardEntity("test-id")
        original_version = entity.version
        
        entity.update_properties()
        
        # Version should not change for empty updates
        assert entity.version == original_version
    
    def test_entity_invalidates_all_caches_after_update(self):
        """Test that all caches are invalidated after successful update."""
        entity = TestStandardEntity("test-id", "original")
        
        # Cache the property
        original_computation = entity.expensive_computation
        
        # Mock _invalidate_caches to verify it's called
        with patch.object(entity, '_invalidate_caches') as mock_invalidate:
            entity.update_properties(name="updated")
            
            # Verify _invalidate_caches was called once
            mock_invalidate.assert_called_once_with()
    
    def test_entity_version_increment_only_once(self):
        """Test that version is incremented only once, not per property."""
        entity = TestStandardEntity("test-id")
        original_version = entity.version
        
        # Update multiple properties
        entity.update_properties(name="new_name", description="new_desc")
        
        # Version should increment only once (enhanced behavior)
        assert entity.version == original_version + 1
    
    def test_entity_rollback_on_validation_failure(self):
        """Test that no changes are applied if validation fails."""
        entity = TestStandardEntity("test-id", "original", "original_desc")
        original_version = entity.version
        
        with pytest.raises(AttributeError):
            entity.update_properties(name="valid", _invalid="private")
        
        # No changes should be applied (enhanced behavior)
        assert entity.name == "original"
        assert entity.description == "original_desc"
        assert entity.version == original_version
    
    def test_entity_respects_discarded_check(self):
        """Test that discarded entities cannot be updated."""
        entity = TestStandardEntity("test-id")
        entity._discard()
        
        with pytest.raises(Exception):  # Should raise discarded exception
            entity.update_properties(name="updated")
    
    def test_entity_post_update_hook_optional(self):
        """Test that post_update hook is optional."""
        # TestStandardEntity doesn't have _post_update_hook
        entity = TestStandardEntity("test-id")
        
        # Should work without _post_update_hook
        entity.update_properties(name="updated")
        assert entity.name == "updated"
    
    def test_entity_protected_setter_priority(self):
        """Test that protected setters take priority over standard setters."""
        class MixedEntity(Entity):
            def __init__(self, id: str, name: str = "test"):
                super().__init__(id=id)
                self._name = name
                self._protected_calls = 0
                self._standard_calls = 0
            
            @property  
            def name(self) -> str:
                return self._name
            
            @name.setter
            def name(self, value: str) -> None:
                """Standard setter - should NOT be called if _set_name exists."""
                self._standard_calls += 1
                self._name = value
                self._increment_version()
            
            def _set_name(self, value: str) -> None:
                """Protected setter - should be called instead of standard setter."""
                self._protected_calls += 1
                self._name = value
                self._increment_version()
        
        entity = MixedEntity("test-id")
        entity.update_properties(name="updated")
        
        # Protected setter should be used
        assert entity._protected_calls == 1
        assert entity._standard_calls == 0
        assert entity.name == "updated"


class TestEnhancedEntityBackwardCompatibility:
    """Test that enhanced Entity maintains backward compatibility."""
    
    def test_existing_update_properties_patterns_still_work(self):
        """Test that existing entity patterns are not broken."""
        
        # Pattern 1: Entities that override update_properties (like Meal)
        class MealLikeEntity(Entity):
            def __init__(self, id: str, name: str = "test"):
                super().__init__(id=id)
                self._name = name
                self._custom_logic_called = False
            
            @property
            def name(self) -> str:
                return self._name
            
            @name.setter  
            def name(self, value: str) -> None:
                self._name = value
                self._increment_version()
            
            def update_properties(self, **kwargs) -> None:
                """Custom update_properties like Meal has."""
                self._custom_logic_called = True
                # Call enhanced Entity logic
                super().update_properties(**kwargs)
        
        entity = MealLikeEntity("test-id")
        entity.update_properties(name="updated")
        
        assert entity._custom_logic_called
        assert entity.name == "updated"
    
    def test_existing_private_update_properties_still_work(self):
        """Test that entities calling _update_properties directly still work."""
        
        class LegacyEntity(Entity):
            def __init__(self, id: str, name: str = "test"):
                super().__init__(id=id)
                self._name = name
            
            @property
            def name(self) -> str:
                return self._name
                
            @name.setter
            def name(self, value: str) -> None:
                self._name = value
                self._increment_version()
            
            def some_method(self):
                """Legacy method that calls _update_properties directly."""
                self._update_properties(name="legacy_updated")
        
        entity = LegacyEntity("test-id")
        entity.some_method()
        
        assert entity.name == "legacy_updated"
    
    def test_enhanced_entity_integration_with_existing_entities(self):
        """Test enhanced Entity works with real entity patterns."""
        
        # Simulate Recipe-like pattern 
        class RecipeLikeEntity(Entity):
            def __init__(self, id: str, name: str = "test"):
                super().__init__(id=id)
                self._name = name
            
            @property
            def name(self) -> str:
                return self._name
            
            def _set_name(self, value: str) -> None:
                """Protected setter like Recipe."""
                self._name = value
                self._increment_version()
        
        entity = RecipeLikeEntity("test-id")
        
        # Should work with enhanced Entity update_properties
        entity.update_properties(name="updated_via_protected")
        assert entity.name == "updated_via_protected" 