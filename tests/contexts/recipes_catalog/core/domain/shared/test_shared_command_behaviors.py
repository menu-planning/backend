"""
Behavior-focused tests for shared domain commands.
Tests focus on command creation behaviors and immutability.
"""

import pytest
import attrs

from src.contexts.recipes_catalog.core.domain.shared.commands.create import CreateTag
from src.contexts.recipes_catalog.core.domain.shared.commands.delete import DeleteTag


class TestCreateTagCommandBehaviors:
    """Test CreateTag command instantiation and validation behaviors."""
    
    def test_create_tag_with_required_fields(self):
        """CreateTag should accept all required fields."""
        command = CreateTag(
            key="diet",
            value="vegan",
            author_id="user-123", 
            type="dietary"
        )
        
        assert command.key == "diet"
        assert command.value == "vegan"
        assert command.author_id == "user-123"
        assert command.type == "dietary"
    
    def test_create_tag_command_is_immutable(self):
        """CreateTag should be immutable (frozen)."""
        command = CreateTag(
            key="diet",
            value="vegan",
            author_id="user-123",
            type="dietary"
        )
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.key = "modified-key" # type: ignore
    
    def test_create_tag_requires_essential_fields(self):
        """CreateTag should require key, value, author_id, and type."""
        with pytest.raises(TypeError):  # Missing required arguments
            CreateTag() # type: ignore
        
        with pytest.raises(TypeError):  # Missing some required arguments  
            CreateTag(key="diet") # type: ignore


class TestDeleteTagCommandBehaviors:
    """Test DeleteTag command behaviors."""
    
    def test_delete_tag_with_id(self):
        """DeleteTag should accept id."""
        command = DeleteTag(id="tag-123")
        
        assert command.id == "tag-123"
    
    def test_delete_tag_command_is_immutable(self):
        """DeleteTag should be immutable (frozen)."""
        command = DeleteTag(id="tag-123")
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.id = "modified-tag-id" # type: ignore
    
    def test_delete_tag_requires_id_field(self):
        """DeleteTag should require id."""
        with pytest.raises(TypeError):  # Missing required arguments
            DeleteTag() # type: ignore  


class TestSharedCommandValidationBehaviors:
    """Test shared command field validation and edge cases."""
    
    def test_commands_handle_various_data_types(self):
        """Shared commands should handle different string values correctly."""
        # Test CreateTag with various values
        command = CreateTag(
            key="category",
            value="quick-meal",
            author_id="user-456",
            type="preparation"
        )
        
        assert command.key == "category"
        assert command.value == "quick-meal"
        assert command.author_id == "user-456"
        assert command.type == "preparation"
        
        # Test DeleteTag with UUID-like string
        delete_command = DeleteTag(id="550e8400-e29b-41d4-a716-446655440000")
        assert delete_command.id == "550e8400-e29b-41d4-a716-446655440000" 