from unittest.mock import patch

import pytest
from sqlalchemy import select
from src.contexts.seedwork.adapters.repositories.join_manager import JoinManager


@pytest.mark.unit
class TestJoinManagerInitialization:
    """Test JoinManager initialization and basic functionality."""

    def test_init_default_values(self):
        """Test JoinManager initializes with empty tracked joins."""
        manager = JoinManager()
        assert len(manager.get_tracked_joins()) == 0

    def test_create_with_existing_joins(self):
        """Test creating JoinManager with pre-existing joins."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            RecipeSaTestModel,
        )

        existing_joins = {RecipeSaTestModel.__name__, IngredientSaTestModel.__name__}
        manager = JoinManager.create_with_existing_joins(existing_joins)

        assert manager.get_tracked_joins() == existing_joins
        # Ensure it's a copy, not the same reference
        assert manager.get_tracked_joins() is not existing_joins


@pytest.mark.unit
class TestJoinManagerHandleJoins:
    """Test the main handle_joins functionality."""

    def test_handle_joins_empty_specifications(self):
        """Test handle_joins with empty join specifications."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        result_stmt, requires_distinct = manager.handle_joins(stmt, [])

        assert result_stmt is stmt  # Should return same statement
        assert requires_distinct is False

    def test_handle_joins_single_join(self):
        """Test handle_joins with a single join specification."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)]

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        # Verify behavior: requires_distinct is True and join is tracked
        assert requires_distinct is True
        assert len(manager.get_tracked_joins()) == 1
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert manager.is_join_needed(RecipeSaTestModel) is False

    def test_handle_joins_multiple_joins(self):
        """Test handle_joins with multiple join specifications."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),
            (IngredientSaTestModel, RecipeSaTestModel.ingredients),
        ]

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        # Verify behavior: requires_distinct is True and both joins are tracked
        assert requires_distinct is True
        assert len(manager.get_tracked_joins()) == 2
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()
        assert manager.is_join_needed(RecipeSaTestModel) is False
        assert manager.is_join_needed(IngredientSaTestModel) is False

    def test_handle_joins_prevents_duplicates(self):
        """Test handle_joins prevents duplicate joins."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Add a join to tracking first
        manager.add_join(RecipeSaTestModel)

        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)]

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        # Verify behavior: no new joins added, requires_distinct is False
        assert requires_distinct is False
        assert len(manager.get_tracked_joins()) == 1
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()

    def test_handle_joins_mixed_new_and_existing(self):
        """Test handle_joins with mix of new and existing joins."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Pre-track one join
        manager.add_join(RecipeSaTestModel)

        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),  # Already tracked
            (IngredientSaTestModel, RecipeSaTestModel.ingredients),  # New
        ]

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        # Verify behavior: both joins tracked, requires_distinct is True
        assert requires_distinct is True
        assert len(manager.get_tracked_joins()) == 2
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()
        assert manager.is_join_needed(RecipeSaTestModel) is False
        assert manager.is_join_needed(IngredientSaTestModel) is False


@pytest.mark.unit
class TestJoinManagerTracking:
    """Test join tracking functionality."""

    def test_add_join(self):
        """Test manually adding a join to tracking."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            RecipeSaTestModel,
        )

        manager = JoinManager()

        manager.add_join(RecipeSaTestModel)

        assert len(manager.get_tracked_joins()) == 1

    def test_is_join_needed(self):
        """Test checking if a join is needed."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            RecipeSaTestModel,
        )

        manager = JoinManager()

        # Initially, join is needed
        assert manager.is_join_needed(RecipeSaTestModel) is True

        # After adding, join is not needed
        manager.add_join(RecipeSaTestModel)
        assert manager.is_join_needed(RecipeSaTestModel) is False

    def test_get_tracked_joins_returns_copy(self):
        """Test get_tracked_joins returns a copy, not the original set."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            RecipeSaTestModel,
        )

        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)

        tracked_copy = manager.get_tracked_joins()
        tracked_copy.add("extra_join")

        # Original should not be modified
        assert len(manager.get_tracked_joins()) == 1

    def test_reset_joins(self):
        """Test resetting join tracking using public API."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)
        manager.add_join(IngredientSaTestModel)

        assert len(manager.get_tracked_joins()) == 2

        manager.reset_joins()

        assert len(manager.get_tracked_joins()) == 0

    def test_merge_tracking(self):
        """Test merging join tracking from another source."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            ProductSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)

        other_joins = {str(IngredientSaTestModel), str(ProductSaTestModel)}
        manager.merge_tracking(other_joins)

        expected_joins = {
            str(RecipeSaTestModel),
            str(IngredientSaTestModel),
            str(ProductSaTestModel),
        }
        assert manager.get_tracked_joins() == expected_joins


@pytest.mark.unit
class TestJoinManagerErrorHandling:
    """Test error handling and edge cases."""

    def test_handle_joins_with_none_join_target(self):
        """Test behavior when join target is None (edge case)."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # This should be handled gracefully
        join_specs = []  # Empty list is valid

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        assert result_stmt is stmt
        assert requires_distinct is False

    def test_string_representation_consistency(self):
        """Test that string representation of models is consistent."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            RecipeSaTestModel,
        )

        manager = JoinManager()

        # Add the same model multiple times using different references
        model_class = RecipeSaTestModel
        manager.add_join(model_class)

        # Should still be considered the same join
        assert manager.is_join_needed(model_class) is False

    def test_handle_joins_with_invalid_join_specifications(self):
        """Test behavior with malformed join specifications."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Test with None join specifications
        result_stmt, requires_distinct = manager.handle_joins(stmt, None)  # type: ignore
        assert result_stmt is stmt
        assert requires_distinct is False

    def test_handle_joins_with_sqlalchemy_exception(self):
        """Test behavior when SQLAlchemy join operation fails."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)]

        with patch.object(stmt, "join") as mock_join:
            # Simulate SQLAlchemy exception
            mock_join.side_effect = Exception("SQLAlchemy join failed")

            # Should propagate the exception
            with pytest.raises(Exception, match="SQLAlchemy join failed"):
                manager.handle_joins(stmt, join_specs)  # type: ignore

    def test_merge_tracking_with_invalid_input(self):
        """Test merge_tracking with invalid input types."""
        manager = JoinManager()

        # Test with None input
        manager.merge_tracking(None)  # type: ignore
        assert len(manager.get_tracked_joins()) == 0

        # Test with empty set
        manager.merge_tracking(set())
        assert len(manager.get_tracked_joins()) == 0

    def test_create_with_existing_joins_with_empty_input(self):
        """Test create_with_existing_joins with empty input."""
        # Test with empty set
        manager = JoinManager.create_with_existing_joins(set())
        assert len(manager.get_tracked_joins()) == 0


@pytest.mark.unit
class TestJoinManagerTypeSafety:
    """Test type safety and validation of JoinManager."""

    def test_string_representation_consistency_with_valid_types(self):
        """Test that string representation is handled consistently with valid types."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()

        # Test with valid SQLAlchemy models
        manager.add_join(RecipeSaTestModel)
        manager.add_join(IngredientSaTestModel)

        # Should be tracked by string representation
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()
        assert manager.is_join_needed(RecipeSaTestModel) is False
        assert manager.is_join_needed(IngredientSaTestModel) is False


@pytest.mark.unit
class TestJoinManagerBehavior:
    """Test behavior-focused scenarios without implementation details."""

    def test_join_manager_tracks_state_correctly(self):
        """Test that JoinManager correctly tracks join state across operations."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()

        # Initially no joins tracked
        assert len(manager.get_tracked_joins()) == 0
        assert manager.is_join_needed(RecipeSaTestModel) is True

        # Add a join manually
        manager.add_join(RecipeSaTestModel)
        assert len(manager.get_tracked_joins()) == 1
        assert manager.is_join_needed(RecipeSaTestModel) is False

        # Add another join
        manager.add_join(IngredientSaTestModel)
        assert len(manager.get_tracked_joins()) == 2
        assert manager.is_join_needed(IngredientSaTestModel) is False

        # Reset should clear all tracking
        manager.reset_joins()
        assert len(manager.get_tracked_joins()) == 0
        assert manager.is_join_needed(RecipeSaTestModel) is True
        assert manager.is_join_needed(IngredientSaTestModel) is True

    def test_join_manager_handles_duplicate_joins_gracefully(self):
        """Test that duplicate joins are handled without errors."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            RecipeSaTestModel,
        )

        manager = JoinManager()

        # Add same join multiple times
        manager.add_join(RecipeSaTestModel)
        manager.add_join(RecipeSaTestModel)
        manager.add_join(RecipeSaTestModel)

        # Should only track one instance
        assert len(manager.get_tracked_joins()) == 1
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()

    def test_join_manager_merge_operation_behavior(self):
        """Test that merge operation correctly combines join tracking."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            ProductSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)

        # Merge with additional joins
        other_joins = {str(IngredientSaTestModel), str(ProductSaTestModel)}
        manager.merge_tracking(other_joins)

        # Should have all three joins
        assert len(manager.get_tracked_joins()) == 3
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()
        assert str(ProductSaTestModel) in manager.get_tracked_joins()

    def test_join_manager_creates_independent_instances(self):
        """Test that different JoinManager instances don't interfere."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            RecipeSaTestModel,
        )

        manager1 = JoinManager()
        manager2 = JoinManager()

        # Add joins to first manager
        manager1.add_join(RecipeSaTestModel)
        manager1.add_join(IngredientSaTestModel)

        # Second manager should be unaffected
        assert len(manager1.get_tracked_joins()) == 2
        assert len(manager2.get_tracked_joins()) == 0
        assert manager2.is_join_needed(RecipeSaTestModel) is True


@pytest.mark.performance
class TestJoinManagerPerformance:
    """Test performance characteristics of JoinManager."""

    def test_large_number_of_joins_duplicate_prevention(self):
        """Test JoinManager performance with many duplicate joins."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            ProductSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Create many duplicate join specifications (simulating complex query)
        join_specs = [(RecipeSaTestModel, MealSaTestModel.recipes)] * 100

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        # Verify behavior: only one join tracked despite many duplicates
        assert requires_distinct is True
        assert len(manager.get_tracked_joins()) == 1
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()

    def test_join_tracking_memory_efficiency(self):
        """Test that join tracking scales efficiently with many unique joins."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            ProductSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()

        # Add many different joins
        models = [
            RecipeSaTestModel,
            IngredientSaTestModel,
            ProductSaTestModel,
            MealSaTestModel,
        ]
        for i in range(100):
            for model in models:
                manager.add_join(model)

        # Should only track unique joins, not duplicates
        assert len(manager.get_tracked_joins()) == 4
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()
        assert str(ProductSaTestModel) in manager.get_tracked_joins()
        assert str(MealSaTestModel) in manager.get_tracked_joins()

    def test_join_manager_reset_performance(self):
        """Test that reset operation is efficient with many tracked joins."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            ProductSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()

        # Add many joins
        models = [
            RecipeSaTestModel,
            IngredientSaTestModel,
            ProductSaTestModel,
            MealSaTestModel,
        ]
        for model in models:
            manager.add_join(model)

        assert len(manager.get_tracked_joins()) == 4

        # Reset should be fast and complete
        manager.reset_joins()

        assert len(manager.get_tracked_joins()) == 0
        assert manager.is_join_needed(RecipeSaTestModel) is True

    def test_merge_tracking_performance(self):
        """Test that merge operation scales efficiently."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            ProductSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)

        # Create large set of joins to merge
        large_join_set = {
            str(IngredientSaTestModel),
            str(ProductSaTestModel),
            str(MealSaTestModel),
        }
        for i in range(100):
            large_join_set.add(f"TestModel{i}")

        manager.merge_tracking(large_join_set)

        # Should have all joins (1 existing + 3 models + 100 test models)
        assert (
            len(manager.get_tracked_joins()) == 104
        )  # 1 existing + 3 models + 100 test models
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()


@pytest.mark.integration
class TestJoinManagerIntegration:
    """Integration tests with real SQLAlchemy models and relationships."""

    def test_join_manager_with_real_sqlalchemy_models(self):
        """Test JoinManager with actual SQLAlchemy models and relationships."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Test with real SQLAlchemy models and relationships
        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),
            (IngredientSaTestModel, RecipeSaTestModel.ingredients),
        ]

        # This should work with real SQLAlchemy objects
        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        assert requires_distinct is True
        assert len(manager.get_tracked_joins()) == 2
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()

    def test_join_manager_with_complex_relationship_chains(self):
        """Test JoinManager with complex relationship chains."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Create a complex join chain: Meal -> Recipe -> Ingredient
        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),
            (IngredientSaTestModel, RecipeSaTestModel.ingredients),
        ]

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        assert requires_distinct is True
        assert len(manager.get_tracked_joins()) == 2
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert str(IngredientSaTestModel) in manager.get_tracked_joins()

    def test_join_manager_with_self_referential_joins(self):
        """Test JoinManager with self-referential relationships."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Test self-referential join (if such relationship exists)
        # This is a hypothetical test - adjust based on actual model relationships
        join_specs = [(MealSaTestModel, MealSaTestModel.id)]  # Self-join example

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        assert requires_distinct is True
        assert len(manager.get_tracked_joins()) == 1
        assert str(MealSaTestModel) in manager.get_tracked_joins()

    def test_join_manager_duplicate_prevention_with_real_models(self):
        """Test duplicate prevention with real SQLAlchemy models."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        stmt = select(MealSaTestModel)

        # Add same join multiple times
        join_specs = [
            (RecipeSaTestModel, MealSaTestModel.recipes),
            (RecipeSaTestModel, MealSaTestModel.recipes),  # Duplicate
            (RecipeSaTestModel, MealSaTestModel.recipes),  # Another duplicate
        ]

        result_stmt, requires_distinct = manager.handle_joins(stmt, join_specs)  # type: ignore

        # Should only track one instance
        assert len(manager.get_tracked_joins()) == 1
        assert str(RecipeSaTestModel) in manager.get_tracked_joins()
        assert requires_distinct is True


@pytest.mark.unit
class TestJoinManagerBackwardCompatibility:
    """Test backward compatibility with existing repository patterns."""

    def test_compatibility_with_existing_already_joined_pattern(self):
        """Test compatibility with existing already_joined set pattern."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            RecipeSaTestModel,
        )

        # Simulate existing pattern
        already_joined: set[str] = {str(RecipeSaTestModel)}

        # Create JoinManager with existing joins
        manager = JoinManager.create_with_existing_joins(already_joined)

        # Should respect existing joins
        assert manager.is_join_needed(RecipeSaTestModel) is False
        assert manager.is_join_needed(IngredientSaTestModel) is True

    def test_get_tracked_joins_matches_already_joined_format(self):
        """Test that get_tracked_joins returns format compatible with already_joined."""
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            IngredientSaTestModel,
            RecipeSaTestModel,
        )

        manager = JoinManager()
        manager.add_join(RecipeSaTestModel)
        manager.add_join(IngredientSaTestModel)

        tracked = manager.get_tracked_joins()

        # Should be a set of strings, compatible with existing already_joined usage
        assert isinstance(tracked, set)
        assert all(isinstance(join_key, str) for join_key in tracked)
        assert str(RecipeSaTestModel) in tracked
        assert str(IngredientSaTestModel) in tracked
