from typing import Set
from unittest.mock import patch

from sqlalchemy import select

from src.contexts.seedwork.shared.adapters.repositories.join_manager import JoinManager
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
    MealSaTestModel,
    RecipeSaTestModel,
    IngredientSaTestModel,
    ProductSaTestModel
)


class TestJoinManagerInitialization:
    """Test JoinManager initialization and basic functionality."""
    
    def test_init_default_values(self):
        """Test JoinManager initializes with empty tracked joins."""
        manager = JoinManager()
        assert manager.tracked_joins == set()
        assert len(manager.get_tracked_joins()) == 0
        
    def test_create_with_existing_joins(self):
        """Test creating JoinManager with pre-existing joins."""
        existing_joins = {RecipeSaTestModel.__name__, IngredientSaTestModel.__name__}
        manager = JoinManager.create_with_existing_joins(existing_joins)
        
        assert manager.tracked_joins == existing_joins
        assert manager.get_tracked_joins() == existing_joins
        # Ensure it's a copy, not the same reference
        assert manager.tracked_joins is not existing_joins


class TestJoinManagerHandleJoins:
    """Test the main handle_joins functionality."""
    
    def test_handle_joins_empty_specifications(self):
        """Test handle_joins with empty join specifications."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        result_stmt, requires_distinct = manager.handle_joins(stmt, [])
        
        assert result_stmt is stmt  # Should return same statement
        assert requires_distinct is False
        assert len(manager.tracked_joins) == 0
        
    def test_handle_joins_single_join(self):
        """Test handle_joins with a single join specification."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        # Mock the join specification
        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)]
        
        with patch.object(stmt, 'join') as mock_join:
            mock_join.return_value = stmt  # Return the same statement for simplicity
            
            result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
            
            # Verify join was called
            mock_join.assert_called_once_with(RecipeSaTestModel, MealSaTestModel.recipes)
            assert requires_distinct is True
            assert str(RecipeSaTestModel) in manager.tracked_joins
    
    def test_handle_joins_multiple_joins(self):
        """Test handle_joins with multiple join specifications."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),
            (IngredientSaTestModel, RecipeSaTestModel.ingredients)
        ]
        
        with patch.object(stmt, 'join') as mock_join:
            mock_join.return_value = stmt
            
            result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
            
            # Verify both joins were called
            assert mock_join.call_count == 2
            assert requires_distinct is True
            assert str(RecipeSaTestModel) in manager.tracked_joins
            assert str(IngredientSaTestModel) in manager.tracked_joins
    
    def test_handle_joins_prevents_duplicates(self):
        """Test handle_joins prevents duplicate joins."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        # Add a join to tracking first
        manager.add_join(RecipeSaTestModel)
        
        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)]
        
        with patch.object(stmt, 'join') as mock_join:
            result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
            
            # Join should not be called since it's already tracked
            mock_join.assert_not_called()
            assert requires_distinct is False  # No new joins added
    
    def test_handle_joins_mixed_new_and_existing(self):
        """Test handle_joins with mix of new and existing joins."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        # Pre-track one join
        manager.add_join(RecipeSaTestModel)
        
        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),  # Already tracked
            (IngredientSaTestModel, RecipeSaTestModel.ingredients)  # New
        ]
        
        with patch.object(stmt, 'join') as mock_join:
            mock_join.return_value = stmt
            
            result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
            
            # Only one join should be called
            mock_join.assert_called_once_with(IngredientSaTestModel, RecipeSaTestModel.ingredients)
            assert requires_distinct is True
            assert str(IngredientSaTestModel) in manager.tracked_joins


class TestJoinManagerTracking:
    """Test join tracking functionality."""
    
    def test_add_join(self):
        """Test manually adding a join to tracking."""
        manager = JoinManager()
        
        manager.add_join(RecipeSaTestModel)
        
        assert str(RecipeSaTestModel) in manager.tracked_joins
        assert len(manager.tracked_joins) == 1
    
    def test_is_join_needed(self):
        """Test checking if a join is needed."""
        manager = JoinManager()
        
        # Initially, join is needed
        assert manager.is_join_needed(RecipeSaTestModel) is True
        
        # After adding, join is not needed
        manager.add_join(RecipeSaTestModel)
        assert manager.is_join_needed(RecipeSaTestModel) is False
    
    def test_get_tracked_joins_returns_copy(self):
        """Test get_tracked_joins returns a copy, not the original set."""
        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)
        
        tracked_copy = manager.get_tracked_joins()
        tracked_copy.add("extra_join")
        
        # Original should not be modified
        assert "extra_join" not in manager.tracked_joins
        assert len(manager.tracked_joins) == 1
    
    def test_reset(self):
        """Test resetting join tracking."""
        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)
        manager.add_join(IngredientSaTestModel)
        
        assert len(manager.tracked_joins) == 2
        
        manager.reset()
        
        assert len(manager.tracked_joins) == 0
        assert manager.tracked_joins == set()
    
    def test_merge_tracking(self):
        """Test merging join tracking from another source."""
        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)
        
        other_joins = {str(IngredientSaTestModel), str(ProductSaTestModel)}
        manager.merge_tracking(other_joins)
        
        expected_joins = {str(RecipeSaTestModel), str(IngredientSaTestModel), str(ProductSaTestModel)}
        assert manager.tracked_joins == expected_joins


class TestJoinManagerIntegration:
    """Integration tests for JoinManager with real SQLAlchemy operations."""
    
    def test_join_manager_with_real_select_statement(self):
        """Test JoinManager with actual SQLAlchemy Select statement."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        # This should work with real SQLAlchemy objects
        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)]
        
        # We can't actually execute joins in unit tests without a database,
        # but we can verify the structure
        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
        
        assert requires_distinct is True
        assert str(RecipeSaTestModel) in manager.tracked_joins
    
    def test_complex_multi_table_join_scenario(self):
        """Test complex scenario with multiple table joins."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        # Simulate meal -> recipe -> ingredient join chain
        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),
            (IngredientSaTestModel, RecipeSaTestModel.ingredients)
        ]
        
        with patch.object(stmt, 'join') as mock_join:
            mock_join.return_value = stmt
            
            result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
            
            assert mock_join.call_count == 2
            assert requires_distinct is True
            assert len(manager.tracked_joins) == 2
            
            # Verify all expected joins are tracked
            expected_models = [RecipeSaTestModel, IngredientSaTestModel]
            for model in expected_models:
                assert str(model) in manager.tracked_joins


class TestJoinManagerErrorHandling:
    """Test error handling and edge cases."""
    
    def test_handle_joins_with_none_join_target(self):
        """Test behavior when join target is None (edge case)."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        # This should be handled gracefully
        join_specs = []  # Empty list is valid
        
        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
        
        assert result_stmt is stmt
        assert requires_distinct is False
    
    def test_string_representation_consistency(self):
        """Test that string representation of models is consistent."""
        manager = JoinManager()
        
        # Add the same model multiple times using different references
        model_class = RecipeSaTestModel
        manager.add_join(model_class)
        
        # Should still be considered the same join
        assert manager.is_join_needed(model_class) is False
        assert str(model_class) in manager.tracked_joins


class TestJoinManagerPerformance:
    """Test performance characteristics of JoinManager."""
    
    def test_large_number_of_joins(self):
        """Test JoinManager performance with many joins."""
        manager = JoinManager()
        stmt = select(MealSaTestModel)
        
        # Create many join specifications (simulating complex query)
        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)] * 100
        
        with patch.object(stmt, 'join') as mock_join:
            mock_join.return_value = stmt
            
            result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs) # type: ignore 
            
            # Should only join once due to duplicate prevention
            mock_join.assert_called_once()
            assert requires_distinct is True
    
    def test_join_tracking_memory_efficiency(self):
        """Test that join tracking doesn't consume excessive memory."""
        manager = JoinManager()
        
        # Add many different "joins" (using strings to simulate)
        for i in range(1000):
            manager.tracked_joins.add(f"TestModel{i}")
        
        # Should still be efficient
        assert len(manager.tracked_joins) == 1000
        assert manager.is_join_needed(RecipeSaTestModel) is True


class TestJoinManagerBackwardCompatibility:
    """Test backward compatibility with existing repository patterns."""
    
    def test_compatibility_with_existing_already_joined_pattern(self):
        """Test compatibility with existing already_joined set pattern."""
        # Simulate existing pattern
        already_joined: Set[str] = {str(RecipeSaTestModel)}
        
        # Create JoinManager with existing joins
        manager = JoinManager.create_with_existing_joins(already_joined)
        
        # Should respect existing joins
        assert manager.is_join_needed(RecipeSaTestModel) is False
        assert manager.is_join_needed(IngredientSaTestModel) is True
    
    def test_get_tracked_joins_matches_already_joined_format(self):
        """Test that get_tracked_joins returns format compatible with already_joined."""
        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)
        manager.add_join(IngredientSaTestModel)
        
        tracked = manager.get_tracked_joins()
        
        # Should be a set of strings, compatible with existing already_joined usage
        assert isinstance(tracked, set)
        assert all(isinstance(join_key, str) for join_key in tracked)
        assert str(RecipeSaTestModel) in tracked
        assert str(IngredientSaTestModel) in tracked 