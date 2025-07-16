"""
Test suite for ApiAttributesToUpdateOnMeal exclude_unset behavior.
Tests the exclude_unset=True functionality for partial field updates.
"""

import pytest
from uuid import uuid4
from typing import Dict, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import (
    ApiUpdateMeal,
    ApiAttributesToUpdateOnMeal
)
from src.contexts.recipes_catalog.core.domain.meal.commands.update_meal import UpdateMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal

# Import the required types for model rebuild
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal,
    create_simple_api_meal,
    create_complex_api_meal,
    create_minimal_api_meal,
    create_boundary_value_test_cases,
    reset_api_meal_counters
)

class TestApiAttributesToUpdateOnMealExcludeUnset:
    """Test suite focused on exclude_unset behavior for ApiAttributesToUpdateOnMeal."""

    def setup_method(self):
        """Reset counters before each test for deterministic results."""
        reset_api_meal_counters()

    def test_exclude_unset_basic_functionality(self):
        """Test basic exclude_unset behavior with simple meal data."""
        # Create a simple meal to get base structure
        api_meal = create_simple_api_meal()
        
        # Create ApiAttributesToUpdateOnMeal from the meal
        update_attributes = ApiAttributesToUpdateOnMeal(
            name=api_meal.name,
            menu_id=api_meal.menu_id,
            description=api_meal.description,
            recipes=[],  # Explicit empty default to satisfy linter
            tags=frozenset(),  # Explicit empty default to satisfy linter
            notes=None,  # Explicit None default to satisfy linter
            like=None,  # Explicit None default to satisfy linter  
            image_url=None  # Explicit None default to satisfy linter
            # Note: deliberately not setting other fields like notes, like, image_url, etc.
        )
        
        # Convert to domain with exclude_unset behavior
        domain_updates = update_attributes.to_domain()
        
        # Verify only set fields are included
        assert isinstance(domain_updates, dict)
        assert "name" in domain_updates
        assert "menu_id" in domain_updates  
        assert "description" in domain_updates
        
        # Verify unset fields are excluded (these were explicitly set to None/empty)
        assert "notes" in domain_updates  # Explicitly set to None
        assert "like" in domain_updates   # Explicitly set to None
        assert "image_url" in domain_updates  # Explicitly set to None
        assert "recipes" in domain_updates    # Explicitly set to []
        assert "tags" in domain_updates       # Explicitly set to frozenset()
        
        # Verify field values match expected
        assert domain_updates["name"] == api_meal.name
        assert domain_updates["menu_id"] == api_meal.menu_id
        assert domain_updates["description"] == api_meal.description

    def test_exclude_unset_with_minimal_fields(self):
        """Test exclude_unset with only required fields set."""
        # Create update with only name set (which is required for meals)
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Test Meal Name",
            menu_id=None,
            description=None,
            recipes=[],
            tags=frozenset(),
            notes=None,
            like=None,
            image_url=None
        )
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Should contain all the explicitly set fields
        assert isinstance(domain_updates, dict)
        assert "name" in domain_updates
        assert domain_updates["name"] == "Test Meal Name"
        
        # All fields were explicitly set (even if to None/empty), so they should all be present
        assert "menu_id" in domain_updates
        assert "description" in domain_updates
        assert "recipes" in domain_updates  
        assert "tags" in domain_updates
        assert "notes" in domain_updates
        assert "like" in domain_updates
        assert "image_url" in domain_updates

    def test_exclude_unset_with_none_values(self):
        """Test that explicitly set None values are included in domain updates."""
        # Create update with explicit None values
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Test Meal",
            description=None,  # Explicitly set to None
            notes=None,        # Explicitly set to None  
            menu_id=None,      # Explicitly set to None
            recipes=[],        # Explicit empty default to satisfy linter
            tags=frozenset(),  # Explicit empty default to satisfy linter
            like=None,         # Explicit None default to satisfy linter
            image_url=None     # Explicit None default to satisfy linter
        )
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Verify explicitly set None values are included
        assert "name" in domain_updates
        assert "description" in domain_updates
        assert "notes" in domain_updates
        assert "menu_id" in domain_updates
        
        # Verify values
        assert domain_updates["name"] == "Test Meal"
        assert domain_updates["description"] is None
        assert domain_updates["notes"] is None
        assert domain_updates["menu_id"] is None
        
        # All other fields were explicitly set too
        assert "like" in domain_updates
        assert "image_url" in domain_updates
        assert "recipes" in domain_updates
        assert "tags" in domain_updates

    def test_exclude_unset_with_collection_fields(self):
        """Test exclude_unset behavior with collection fields (recipes, tags)."""
        # Create a meal with collections for reference
        api_meal = create_complex_api_meal()
        
        # Create update with only collection fields set
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Collection Test Meal",
            recipes=api_meal.recipes,  # Set recipes collection
            tags=api_meal.tags,        # Set tags collection
            menu_id=None,
            description=None,
            notes=None,
            like=None,
            image_url=None
        )
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Verify set fields are included
        assert "name" in domain_updates
        assert "recipes" in domain_updates
        assert "tags" in domain_updates
        
        # Verify collection conversions
        assert isinstance(domain_updates["recipes"], list)
        assert isinstance(domain_updates["tags"], set)
        assert api_meal.recipes is not None
        assert api_meal.tags is not None
        assert len(domain_updates["recipes"]) == len(api_meal.recipes)
        assert len(domain_updates["tags"]) == len(api_meal.tags)
        
        # All fields were explicitly set
        assert "description" in domain_updates
        assert "notes" in domain_updates
        assert "menu_id" in domain_updates
        assert "like" in domain_updates
        assert "image_url" in domain_updates

    def test_exclude_unset_field_tracking_accuracy(self):
        """Test that __pydantic_fields_set__ accurately tracks set fields."""
        # Test various combinations of set fields
        test_scenarios = [
            # Scenario 1: Only name
            {"name": "Test 1", "menu_id": None, "description": None, "recipes": [], "tags": frozenset(), "notes": None, "like": None, "image_url": None},
            # Scenario 2: Name and description
            {"name": "Test 2", "description": "Test description", "menu_id": None, "recipes": [], "tags": frozenset(), "notes": None, "like": None, "image_url": None},
            # Scenario 3: Name and boolean field
            {"name": "Test 3", "like": True, "menu_id": None, "description": None, "recipes": [], "tags": frozenset(), "notes": None, "image_url": None},
            # Scenario 4: Name and UUID field
            {"name": "Test 4", "menu_id": str(uuid4()), "description": None, "recipes": [], "tags": frozenset(), "notes": None, "like": None, "image_url": None},
            # Scenario 5: Multiple fields including None
            {"name": "Test 5", "description": None, "notes": "Some notes", "like": False, "menu_id": None, "recipes": [], "tags": frozenset(), "image_url": None}
        ]
        
        for i, scenario_kwargs in enumerate(test_scenarios):
            update_attributes = ApiAttributesToUpdateOnMeal(**scenario_kwargs)
            domain_updates = update_attributes.to_domain()
            
            # All fields are explicitly set, so all should be in domain updates
            for field_name, field_value in scenario_kwargs.items():
                assert field_name in domain_updates, f"Field {field_name} missing in scenario {i}"
                if field_name in ["recipes", "tags"]:
                    # Collection fields are converted, so check type instead
                    if field_name == "recipes":
                        assert isinstance(domain_updates[field_name], list)
                    elif field_name == "tags":
                        assert isinstance(domain_updates[field_name], set)
                else:
                    assert domain_updates[field_name] == field_value, f"Field {field_name} value mismatch in scenario {i}"
            
            # All fields were explicitly provided, so count should match
            assert len(domain_updates) == len(scenario_kwargs), f"Field count mismatch in scenario {i}"

    def test_exclude_unset_consistency_across_instances(self):
        """Test that exclude_unset behavior is consistent across different instances."""
        # Create multiple instances with different field combinations
        instances = [
            ApiAttributesToUpdateOnMeal(name="Instance 1", description="Desc 1", menu_id=None, recipes=[], tags=frozenset(), notes=None, like=None, image_url=None),
            ApiAttributesToUpdateOnMeal(name="Instance 2", like=True, menu_id=None, description=None, recipes=[], tags=frozenset(), notes=None, image_url=None),
            ApiAttributesToUpdateOnMeal(name="Instance 3", menu_id=str(uuid4()), notes="Notes 3", description=None, recipes=[], tags=frozenset(), like=None, image_url=None),
            ApiAttributesToUpdateOnMeal(name="Instance 4", menu_id=None, description=None, recipes=[], tags=frozenset(), notes=None, like=None, image_url=None)  # Only name
        ]
        
        for i, instance in enumerate(instances):
            domain_updates = instance.to_domain()
            
            # All instances should have name
            assert "name" in domain_updates, f"Name missing in instance {i}"
            assert domain_updates["name"] == f"Instance {i+1}"
            
            # Since all fields are explicitly set, all should be present
            expected_fields = {"name", "menu_id", "description", "recipes", "tags", "notes", "like", "image_url"}
            actual_fields = set(domain_updates.keys())
            assert expected_fields == actual_fields, f"Field set mismatch in instance {i}: expected {expected_fields}, got {actual_fields}"

    # =============================================================================
    # TASK 2.2.2: Test partial field updates
    # =============================================================================

    def test_partial_update_name_only(self):
        """Test partial update with only name field set."""
        # Create update with only name - no other fields provided
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Updated Meal Name"
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only name should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 1
        assert "name" in domain_updates
        assert domain_updates["name"] == "Updated Meal Name"
        
        # All other fields should be excluded (truly unset)
        excluded_fields = {"menu_id", "description", "recipes", "tags", "notes", "like", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_multiple_fields(self):
        """Test partial update with only a subset of fields set."""
        # Create update with only name and description
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Updated Name",
            description="Updated description"
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 2
        assert "name" in domain_updates
        assert "description" in domain_updates
        assert domain_updates["name"] == "Updated Name"
        assert domain_updates["description"] == "Updated description"
        
        # All other fields should be excluded
        excluded_fields = {"menu_id", "recipes", "tags", "notes", "like", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_with_boolean_field(self):
        """Test partial update with boolean field."""
        # Create update with name and like field
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Liked Meal",
            like=True
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 2
        assert "name" in domain_updates
        assert "like" in domain_updates
        assert domain_updates["name"] == "Liked Meal"
        assert domain_updates["like"] is True
        
        # All other fields should be excluded
        excluded_fields = {"menu_id", "description", "recipes", "tags", "notes", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_with_uuid_field(self):
        """Test partial update with UUID field."""
        menu_id = str(uuid4())
        
        # Create update with name and menu_id
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Menu Associated Meal",
            menu_id=menu_id
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 2
        assert "name" in domain_updates
        assert "menu_id" in domain_updates
        assert domain_updates["name"] == "Menu Associated Meal"
        assert domain_updates["menu_id"] == menu_id
        
        # All other fields should be excluded
        excluded_fields = {"description", "recipes", "tags", "notes", "like", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_with_collections(self):
        """Test partial update with collection fields."""
        # Create a complex meal for collection data
        api_meal = create_complex_api_meal()
        
        # Create update with name and collections
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Collection Updated Meal",
            recipes=api_meal.recipes,
            tags=api_meal.tags
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 3
        assert "name" in domain_updates
        assert "recipes" in domain_updates
        assert "tags" in domain_updates
        
        # Verify collection conversions
        assert domain_updates["name"] == "Collection Updated Meal"
        assert isinstance(domain_updates["recipes"], list)
        assert isinstance(domain_updates["tags"], set)
        assert api_meal.recipes is not None
        assert api_meal.tags is not None
        assert len(domain_updates["recipes"]) == len(api_meal.recipes)
        assert len(domain_updates["tags"]) == len(api_meal.tags)
        
        # All other fields should be excluded
        excluded_fields = {"menu_id", "description", "notes", "like", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_edge_cases(self):
        """Test partial update edge cases with various field combinations."""
        test_scenarios = [
            # Only boolean field
            {
                "input": {"like": False},
                "expected_count": 1,
                "expected_fields": {"like"}
            },
            # Only UUID field
            {
                "input": {"menu_id": str(uuid4())},
                "expected_count": 1,
                "expected_fields": {"menu_id"}
            },
            # Only string fields
            {
                "input": {"name": "Test", "notes": "Some notes"},
                "expected_count": 2,
                "expected_fields": {"name", "notes"}
            },
            # Mixed types
            {
                "input": {"name": "Mixed", "like": True, "image_url": "http://example.com"},
                "expected_count": 3,
                "expected_fields": {"name", "like", "image_url"}
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            update_attributes = ApiAttributesToUpdateOnMeal(**scenario["input"])
            domain_updates = update_attributes.to_domain()
            
            # Verify only expected fields are present
            assert len(domain_updates) == scenario["expected_count"], f"Scenario {i}: Expected {scenario['expected_count']} fields, got {len(domain_updates)}"
            
            actual_fields = set(domain_updates.keys())
            assert actual_fields == scenario["expected_fields"], f"Scenario {i}: Expected fields {scenario['expected_fields']}, got {actual_fields}"
            
            # Verify values match
            for field_name, expected_value in scenario["input"].items():
                assert domain_updates[field_name] == expected_value, f"Scenario {i}: Field {field_name} value mismatch"

    def test_partial_update_pydantic_fields_set_tracking(self):
        """Test that __pydantic_fields_set__ correctly tracks only set fields in partial updates."""
        # Test different partial update combinations
        test_cases = [
            {"name": "Test 1"},
            {"name": "Test 2", "description": "Desc"},
            {"like": True},
            {"menu_id": str(uuid4()), "notes": "Notes"},
            {"name": "Test 5", "like": False, "image_url": "http://example.com"}
        ]
        
        for i, test_case in enumerate(test_cases):
            update_attributes = ApiAttributesToUpdateOnMeal(**test_case)
            
            # Check that __pydantic_fields_set__ only contains the provided fields
            fields_set = update_attributes.__pydantic_fields_set__
            expected_fields = set(test_case.keys())
            
            assert fields_set == expected_fields, f"Test case {i}: fields_set {fields_set} != expected {expected_fields}"
            
            # Verify to_domain() respects the fields_set
            domain_updates = update_attributes.to_domain()
            domain_fields = set(domain_updates.keys())
            
            assert domain_fields == expected_fields, f"Test case {i}: domain fields {domain_fields} != expected {expected_fields}"
            
            # Verify values are correct
            for field_name, expected_value in test_case.items():
                assert domain_updates[field_name] == expected_value, f"Test case {i}: {field_name} value mismatch"

    # =============================================================================
    # TASK 2.2.3: Test None vs unset field handling
    # =============================================================================

    def test_explicit_none_vs_unset_basic(self):
        """Test the difference between explicitly setting None vs not setting a field at all."""
        # Test 1: Explicitly set None for description
        update_with_explicit_none = ApiAttributesToUpdateOnMeal(
            name="Test Meal",
            description=None  # Explicitly set to None
        ) # type: ignore
        
        # Test 2: Don't set description at all
        update_with_unset = ApiAttributesToUpdateOnMeal(
            name="Test Meal"
            # description not provided at all
        ) # type: ignore
        
        # Convert both to domain
        domain_with_none = update_with_explicit_none.to_domain()
        domain_with_unset = update_with_unset.to_domain()
        
        # Explicitly set None should be included
        assert "description" in domain_with_none
        assert domain_with_none["description"] is None
        assert len(domain_with_none) == 2  # name + description
        
        # Unset field should be excluded
        assert "description" not in domain_with_unset
        assert len(domain_with_unset) == 1  # only name
        
        # Both should have name
        assert domain_with_none["name"] == "Test Meal"
        assert domain_with_unset["name"] == "Test Meal"

    def test_explicit_none_vs_unset_multiple_fields(self):
        """Test None vs unset behavior across multiple fields."""
        # Create update with some explicit None values and some unset
        update_attributes = ApiAttributesToUpdateOnMeal(
            name="Mixed Update",
            description=None,      # Explicitly set to None
            notes=None,           # Explicitly set to None
            like=None             # Explicitly set to None
            # menu_id, recipes, tags, image_url are not set at all
        ) # type: ignore
        
        domain_updates = update_attributes.to_domain()
        
        # Explicitly set None fields should be included
        assert "name" in domain_updates
        assert "description" in domain_updates
        assert "notes" in domain_updates 
        assert "like" in domain_updates
        
        # Verify None values
        assert domain_updates["name"] == "Mixed Update"
        assert domain_updates["description"] is None
        assert domain_updates["notes"] is None
        assert domain_updates["like"] is None
        
        # Unset fields should be excluded
        excluded_fields = {"menu_id", "recipes", "tags", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"
        
        # Should only have the 4 explicitly set fields
        assert len(domain_updates) == 4

    def test_explicit_none_vs_unset_for_boolean_field(self):
        """Test None vs unset specifically for boolean fields."""
        # Test explicit None for boolean
        update_with_none = ApiAttributesToUpdateOnMeal(
            name="Boolean Test",
            like=None  # Explicitly set to None
        ) # type: ignore
        
        # Test unset boolean
        update_with_unset = ApiAttributesToUpdateOnMeal(
            name="Boolean Test"
            # like not provided
        ) # type: ignore
        
        domain_with_none = update_with_none.to_domain()
        domain_with_unset = update_with_unset.to_domain()
        
        # Explicit None should be included
        assert "like" in domain_with_none
        assert domain_with_none["like"] is None
        assert len(domain_with_none) == 2
        
        # Unset should be excluded
        assert "like" not in domain_with_unset
        assert len(domain_with_unset) == 1

    def test_explicit_none_vs_unset_for_uuid_field(self):
        """Test None vs unset specifically for UUID fields."""
        # Test explicit None for UUID
        update_with_none = ApiAttributesToUpdateOnMeal(
            name="UUID Test",
            menu_id=None  # Explicitly set to None
        ) # type: ignore
        
        # Test unset UUID
        update_with_unset = ApiAttributesToUpdateOnMeal(
            name="UUID Test"
            # menu_id not provided
        ) # type: ignore
        
        domain_with_none = update_with_none.to_domain()
        domain_with_unset = update_with_unset.to_domain()
        
        # Explicit None should be included
        assert "menu_id" in domain_with_none
        assert domain_with_none["menu_id"] is None
        assert len(domain_with_none) == 2
        
        # Unset should be excluded
        assert "menu_id" not in domain_with_unset
        assert len(domain_with_unset) == 1

    def test_explicit_none_vs_unset_for_collection_fields(self):
        """Test None vs unset for collection fields (should behave differently)."""
        # Collections have default_factory, so they behave differently
        # Test with minimal data
        api_meal = create_minimal_api_meal()
        
        # Test when not providing collections at all - they should get defaults
        update_no_collections = ApiAttributesToUpdateOnMeal(
            name="Collection Test"
            # recipes and tags not provided - should get defaults
        ) # type: ignore
        
        # Test when explicitly setting empty collections
        update_explicit_empty = ApiAttributesToUpdateOnMeal(
            name="Collection Test",
            recipes=[],           # Explicitly empty
            tags=frozenset()      # Explicitly empty
        ) # type: ignore
        
        domain_no_collections = update_no_collections.to_domain()
        domain_explicit_empty = update_explicit_empty.to_domain()
        
        # When not provided, collections should not be in the update (exclude_unset)
        assert "recipes" not in domain_no_collections
        assert "tags" not in domain_no_collections
        assert len(domain_no_collections) == 1  # only name
        
        # When explicitly set to empty, they should be included
        assert "recipes" in domain_explicit_empty
        assert "tags" in domain_explicit_empty
        assert domain_explicit_empty["recipes"] == []
        assert domain_explicit_empty["tags"] == set()
        assert len(domain_explicit_empty) == 3  # name + recipes + tags

    def test_pydantic_fields_set_tracking_none_vs_unset(self):
        """Test that __pydantic_fields_set__ correctly distinguishes None vs unset."""
        # Test various combinations
        test_scenarios = [
            {
                "input": {"name": "Test", "description": None},
                "expected_fields_set": {"name", "description"},
                "expected_domain_fields": {"name", "description"}
            },
            {
                "input": {"name": "Test"},
                "expected_fields_set": {"name"},
                "expected_domain_fields": {"name"}
            },
            {
                "input": {"name": "Test", "like": None, "notes": None},
                "expected_fields_set": {"name", "like", "notes"},
                "expected_domain_fields": {"name", "like", "notes"}
            },
            {
                "input": {"name": "Test", "menu_id": None, "image_url": None},
                "expected_fields_set": {"name", "menu_id", "image_url"},
                "expected_domain_fields": {"name", "menu_id", "image_url"}
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            update_attributes = ApiAttributesToUpdateOnMeal(**scenario["input"])
            
            # Check __pydantic_fields_set__
            fields_set = update_attributes.__pydantic_fields_set__
            assert fields_set == scenario["expected_fields_set"], f"Scenario {i}: fields_set mismatch"
            
            # Check domain output
            domain_updates = update_attributes.to_domain()
            domain_fields = set(domain_updates.keys())
            assert domain_fields == scenario["expected_domain_fields"], f"Scenario {i}: domain fields mismatch"
            
            # Verify None values are preserved
            for field_name in scenario["expected_fields_set"]:
                expected_value = scenario["input"][field_name]
                assert domain_updates[field_name] == expected_value, f"Scenario {i}: {field_name} value mismatch"

    def test_consistency_between_creation_methods(self):
        """Test that None vs unset behavior is consistent across different creation patterns."""
        # Method 1: Direct constructor with explicit None
        method1 = ApiAttributesToUpdateOnMeal(
            name="Consistency Test",
            description=None,
            like=None
        ) # type: ignore
        
        # Method 2: Create with dict that has explicit None
        data_with_none = {
            "name": "Consistency Test",
            "description": None,
            "like": None
        }
        method2 = ApiAttributesToUpdateOnMeal(**data_with_none)
        
        # Method 3: Only required fields
        method3 = ApiAttributesToUpdateOnMeal(
            name="Consistency Test"
        ) # type: ignore
        
        # All should behave the same way
        domain1 = method1.to_domain()
        domain2 = method2.to_domain()
        domain3 = method3.to_domain()
        
        # Methods 1 and 2 should be identical (explicit None)
        assert domain1 == domain2
        assert len(domain1) == 3  # name, description, like
        assert "description" in domain1 and domain1["description"] is None
        assert "like" in domain1 and domain1["like"] is None
        
        # Method 3 should only have name (unset fields excluded)
        assert len(domain3) == 1
        assert "description" not in domain3
        assert "like" not in domain3
        assert domain3["name"] == "Consistency Test" 