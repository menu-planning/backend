"""
Test suite for ApiAttributesToUpdateOnRecipe exclude_unset behavior.
Tests the exclude_unset=True functionality for partial field updates.
"""

from pydantic import HttpUrl

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_recipe import (
    ApiAttributesToUpdateOnRecipe
)
from src.contexts.shared_kernel.domain.enums import Privacy

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_simple_api_recipe,
    create_complex_api_recipe,
)


class TestApiAttributesToUpdateOnRecipeExcludeUnset:
    """Test suite focused on exclude_unset behavior for ApiAttributesToUpdateOnRecipe."""

    def test_exclude_unset_basic_functionality(self):
        """Test basic exclude_unset behavior with simple recipe data."""
        # Create a simple recipe to get base structure
        api_recipe = create_simple_api_recipe()
        
        # Create ApiAttributesToUpdateOnRecipe from the recipe
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name=api_recipe.name,
            description=api_recipe.description,
            ingredients=frozenset(),  # Explicit empty collection
            instructions=api_recipe.instructions,
            weight_in_grams=None,  # Explicit None - will be included
            utensils=None,  # Explicit None - will be included
            total_time=None,  # Explicit None - will be included
            notes=None,  # Explicit None - will be included
            tags=frozenset(),  # Explicit empty collection
            privacy=None,  # Explicit None - will be converted to Privacy.PRIVATE
            nutri_facts=None,  # Explicit None - will NOT be included (special handling)
            image_url=None  # Explicit None - will be included
        )
        
        # Convert to domain with exclude_unset behavior
        domain_updates = update_attributes.to_domain()
        
        # Verify only set fields are included
        assert isinstance(domain_updates, dict)
        assert "name" in domain_updates
        assert "description" in domain_updates
        assert "instructions" in domain_updates
        
        # Verify simple fields that were explicitly set to None are included
        assert "weight_in_grams" in domain_updates
        assert "utensils" in domain_updates
        assert "total_time" in domain_updates
        assert "notes" in domain_updates
        assert "image_url" in domain_updates
        
        # Verify privacy field conversion
        assert "privacy" in domain_updates
        assert domain_updates["privacy"] == Privacy.PRIVATE  # None converted to PRIVATE
        
        # Verify collection fields that were set to empty collections are included
        assert "ingredients" in domain_updates
        assert "tags" in domain_updates
        assert domain_updates["ingredients"] == []
        assert domain_updates["tags"] == frozenset()
        
        # Verify nutri_facts is NOT included when None (special handling)
        assert "nutri_facts" not in domain_updates
        
        # Verify field values match expected
        assert domain_updates["name"] == api_recipe.name
        assert domain_updates["description"] == api_recipe.description
        assert domain_updates["instructions"] == api_recipe.instructions

    def test_exclude_unset_with_minimal_fields(self):
        """Test exclude_unset with only required fields set."""
        # Create update with only name and instructions set (required for recipes)
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Test Recipe Name",
            instructions="Test instructions",
            description=None,
            ingredients=frozenset(),
            weight_in_grams=None,
            utensils=None,
            total_time=None,
            notes=None,
            tags=frozenset(),
            privacy=None,
            nutri_facts=None,
            image_url=None
        )
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Should contain all the explicitly set fields
        assert isinstance(domain_updates, dict)
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert domain_updates["name"] == "Test Recipe Name"
        assert domain_updates["instructions"] == "Test instructions"
        
        # Simple fields explicitly set to None should be included
        assert "description" in domain_updates
        assert "weight_in_grams" in domain_updates
        assert "utensils" in domain_updates
        assert "total_time" in domain_updates
        assert "notes" in domain_updates
        assert "image_url" in domain_updates
        
        # Collection fields explicitly set to empty should be included
        assert "ingredients" in domain_updates
        assert "tags" in domain_updates
        
        # Privacy field should be converted
        assert "privacy" in domain_updates
        assert domain_updates["privacy"] == Privacy.PRIVATE
        
        # nutri_facts should NOT be included when None
        assert "nutri_facts" not in domain_updates

    def test_exclude_unset_with_none_values(self):
        """Test that explicitly set None values are handled according to field type."""
        # Create update with explicit None values
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Test Recipe",
            instructions="Test instructions",
            description=None,  # Simple field - included as None
            notes=None,        # Simple field - included as None
            weight_in_grams=None,  # Simple field - included as None
            utensils=None,     # Simple field - included as None
            total_time=None,   # Simple field - included as None
            privacy=None,      # Enum field - converted to Privacy.PRIVATE
            nutri_facts=None,  # Complex field - NOT included when None
            image_url=None,    # Simple field - included as None
            ingredients=frozenset(),  # Collection - included as empty list
            tags=frozenset()   # Collection - included as empty frozenset
        )
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Verify simple fields set to None are included
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert "description" in domain_updates
        assert "notes" in domain_updates
        assert "weight_in_grams" in domain_updates
        assert "utensils" in domain_updates
        assert "total_time" in domain_updates
        assert "image_url" in domain_updates
        
        # Verify values for simple fields
        assert domain_updates["name"] == "Test Recipe"
        assert domain_updates["instructions"] == "Test instructions"
        assert domain_updates["description"] is None
        assert domain_updates["notes"] is None
        assert domain_updates["weight_in_grams"] is None
        assert domain_updates["utensils"] is None
        assert domain_updates["total_time"] is None
        assert domain_updates["image_url"] is None
        
        # Verify privacy field conversion
        assert "privacy" in domain_updates
        assert domain_updates["privacy"] == Privacy.PRIVATE
        
        # Collection fields were explicitly set and should be included
        assert "ingredients" in domain_updates
        assert "tags" in domain_updates
        assert domain_updates["ingredients"] == []
        assert domain_updates["tags"] == frozenset()
        
        # nutri_facts should NOT be included when None
        assert "nutri_facts" not in domain_updates

    def test_exclude_unset_with_collection_fields(self):
        """Test exclude_unset behavior with collection fields (ingredients, tags)."""
        # Create a recipe with collections for reference
        api_recipe = create_complex_api_recipe()
        
        # Create update with only collection fields set
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Collection Test Recipe",
            instructions="Test instructions",
            ingredients=api_recipe.ingredients,  # Set ingredients collection
            tags=api_recipe.tags,                # Set tags collection
            description=None,
            weight_in_grams=None,
            utensils=None,
            total_time=None,
            notes=None,
            privacy=None,
            nutri_facts=None,
            image_url=None
        )
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Verify set fields are included
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert "ingredients" in domain_updates
        assert "tags" in domain_updates
        
        # Verify collection conversions
        assert isinstance(domain_updates["ingredients"], list)
        assert isinstance(domain_updates["tags"], frozenset)
        assert api_recipe.ingredients is not None
        assert api_recipe.tags is not None
        assert len(domain_updates["ingredients"]) == len(api_recipe.ingredients)
        assert len(domain_updates["tags"]) == len(api_recipe.tags)
        
        # Simple fields explicitly set to None should be included
        assert "description" in domain_updates
        assert "weight_in_grams" in domain_updates
        assert "utensils" in domain_updates
        assert "total_time" in domain_updates
        assert "notes" in domain_updates
        assert "image_url" in domain_updates
        
        # Privacy should be converted
        assert "privacy" in domain_updates
        assert domain_updates["privacy"] == Privacy.PRIVATE
        
        # nutri_facts should NOT be included when None
        assert "nutri_facts" not in domain_updates

    def test_exclude_unset_field_tracking_accuracy(self):
        """Test that __pydantic_fields_set__ accurately tracks set fields."""
        # Test various combinations of set fields
        test_scenarios = [
            # Scenario 1: Only required fields
            {"name": "Test 1", "instructions": "Instructions 1", "description": None, "ingredients": frozenset(), "weight_in_grams": None, "utensils": None, "total_time": None, "notes": None, "tags": frozenset(), "privacy": None, "nutri_facts": None, "image_url": None},
            # Scenario 2: Name, instructions and description
            {"name": "Test 2", "instructions": "Instructions 2", "description": "Test description", "ingredients": frozenset(), "weight_in_grams": None, "utensils": None, "total_time": None, "notes": None, "tags": frozenset(), "privacy": None, "nutri_facts": None, "image_url": None},
            # Scenario 3: Name, instructions and numeric fields
            {"name": "Test 3", "instructions": "Instructions 3", "weight_in_grams": 500, "total_time": 30, "description": None, "ingredients": frozenset(), "utensils": None, "notes": None, "tags": frozenset(), "privacy": None, "nutri_facts": None, "image_url": None},
            # Scenario 4: Name, instructions and privacy
            {"name": "Test 4", "instructions": "Instructions 4", "privacy": Privacy.PUBLIC, "description": None, "ingredients": frozenset(), "weight_in_grams": None, "utensils": None, "total_time": None, "notes": None, "tags": frozenset(), "nutri_facts": None, "image_url": None},
            # Scenario 5: Multiple fields including None
            {"name": "Test 5", "instructions": "Instructions 5", "description": None, "notes": "Some notes", "utensils": "spoon, fork", "total_time": 45, "ingredients": frozenset(), "weight_in_grams": None, "tags": frozenset(), "privacy": None, "nutri_facts": None, "image_url": None}
        ]
        
        for i, scenario_kwargs in enumerate(test_scenarios):
            update_attributes = ApiAttributesToUpdateOnRecipe(**scenario_kwargs)
            domain_updates = update_attributes.to_domain()
            
            # Count expected fields (all except nutri_facts when None)
            expected_field_count = len(scenario_kwargs)
            if scenario_kwargs.get("nutri_facts") is None:
                expected_field_count -= 1  # nutri_facts not included when None
            
            # All explicitly set fields should be in domain updates except nutri_facts when None
            for field_name, field_value in scenario_kwargs.items():
                if field_name == "nutri_facts" and field_value is None:
                    assert field_name not in domain_updates, f"Field {field_name} should be excluded when None in scenario {i}"
                elif field_name == "privacy" and field_value is None:
                    assert field_name in domain_updates, f"Field {field_name} missing in scenario {i}"
                    assert domain_updates[field_name] == Privacy.PRIVATE, f"Privacy should be converted to PRIVATE in scenario {i}"
                else:
                    assert field_name in domain_updates, f"Field {field_name} missing in scenario {i}"
                    if field_name in ["ingredients", "tags"]:
                        # Collection fields are converted, so check type instead
                        if field_name == "ingredients":
                            assert isinstance(domain_updates[field_name], list)
                        elif field_name == "tags":
                            assert isinstance(domain_updates[field_name], frozenset)
                    else:
                        assert domain_updates[field_name] == field_value, f"Field {field_name} value mismatch in scenario {i}"
            
            # Check final count matches expectation
            assert len(domain_updates) == expected_field_count, f"Field count mismatch in scenario {i}: expected {expected_field_count}, got {len(domain_updates)}"

    def test_exclude_unset_consistency_across_instances(self):
        """Test that exclude_unset behavior is consistent across different instances."""
        # Create multiple instances with different field combinations
        instances = [
            ApiAttributesToUpdateOnRecipe(name="Instance 1", instructions="Instructions 1", description="Desc 1", weight_in_grams=None, ingredients=frozenset(), utensils=None, total_time=None, notes=None, tags=frozenset(), privacy=None, nutri_facts=None, image_url=None),
            ApiAttributesToUpdateOnRecipe(name="Instance 2", instructions="Instructions 2", privacy=Privacy.PUBLIC, description=None, ingredients=frozenset(), weight_in_grams=None, utensils=None, total_time=None, notes=None, tags=frozenset(), nutri_facts=None, image_url=None),
            ApiAttributesToUpdateOnRecipe(name="Instance 3", instructions="Instructions 3", weight_in_grams=400, notes="Notes 3", description=None, ingredients=frozenset(), utensils=None, total_time=None, tags=frozenset(), privacy=None, nutri_facts=None, image_url=None),
            ApiAttributesToUpdateOnRecipe(name="Instance 4", instructions="Instructions 4", description=None, ingredients=frozenset(), weight_in_grams=None, utensils=None, total_time=None, notes=None, tags=frozenset(), privacy=None, nutri_facts=None, image_url=None)  # Only required fields
        ]
        
        for i, instance in enumerate(instances):
            domain_updates = instance.to_domain()
            
            # All instances should have name and instructions
            assert "name" in domain_updates, f"Name missing in instance {i}"
            assert "instructions" in domain_updates, f"Instructions missing in instance {i}"
            assert domain_updates["name"] == f"Instance {i+1}"
            assert domain_updates["instructions"] == f"Instructions {i+1}"
            
            # All fields except nutri_facts should be present (nutri_facts excluded when None)
            expected_fields = {"name", "instructions", "description", "ingredients", "weight_in_grams", "utensils", "total_time", "notes", "tags", "privacy", "image_url"}
            actual_fields = set(domain_updates.keys())
            assert expected_fields == actual_fields, f"Field set mismatch in instance {i}: expected {expected_fields}, got {actual_fields}"

    # =============================================================================
    # TASK 2.2.2: Test partial field updates
    # =============================================================================

    def test_partial_update_name_only(self):
        """Test partial update with only name field set."""
        # Create update with only name - no other fields provided
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Updated Recipe Name"
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only name should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 1
        assert "name" in domain_updates
        assert domain_updates["name"] == "Updated Recipe Name"
        
        # All other fields should be excluded (truly unset)
        excluded_fields = {"instructions", "description", "ingredients", "weight_in_grams", "utensils", "total_time", "notes", "tags", "privacy", "nutri_facts", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_multiple_fields(self):
        """Test partial update with only a subset of fields set."""
        # Create update with only name, instructions and description
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Updated Name",
            instructions="Updated instructions",
            description="Updated description"
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 3
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert "description" in domain_updates
        assert domain_updates["name"] == "Updated Name"
        assert domain_updates["instructions"] == "Updated instructions"
        assert domain_updates["description"] == "Updated description"
        
        # All other fields should be excluded
        excluded_fields = {"ingredients", "weight_in_grams", "utensils", "total_time", "notes", "tags", "privacy", "nutri_facts", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_with_numeric_fields(self):
        """Test partial update with numeric fields."""
        # Create update with name, instructions and numeric fields
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Numeric Recipe",
            instructions="Instructions",
            weight_in_grams=500,
            total_time=45
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 4
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert "weight_in_grams" in domain_updates
        assert "total_time" in domain_updates
        assert domain_updates["name"] == "Numeric Recipe"
        assert domain_updates["instructions"] == "Instructions"
        assert domain_updates["weight_in_grams"] == 500
        assert domain_updates["total_time"] == 45
        
        # All other fields should be excluded
        excluded_fields = {"description", "ingredients", "utensils", "notes", "tags", "privacy", "nutri_facts", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_with_privacy_field(self):
        """Test partial update with privacy field."""
        # Create update with name, instructions and privacy
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Privacy Recipe",
            instructions="Instructions",
            privacy=Privacy.PUBLIC
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 3
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert "privacy" in domain_updates
        assert domain_updates["name"] == "Privacy Recipe"
        assert domain_updates["instructions"] == "Instructions"
        assert domain_updates["privacy"] == Privacy.PUBLIC
        
        # All other fields should be excluded
        excluded_fields = {"description", "ingredients", "weight_in_grams", "utensils", "total_time", "notes", "tags", "nutri_facts", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_with_collections(self):
        """Test partial update with collection fields."""
        # Create a complex recipe for collection data
        api_recipe = create_complex_api_recipe()
        
        # Create update with name, instructions and collections
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Collection Updated Recipe",
            instructions="Updated instructions",
            ingredients=api_recipe.ingredients,
            tags=api_recipe.tags
        ) # type: ignore
        
        # Convert to domain
        domain_updates = update_attributes.to_domain()
        
        # Only provided fields should be included
        assert isinstance(domain_updates, dict)
        assert len(domain_updates) == 4
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert "ingredients" in domain_updates
        assert "tags" in domain_updates
        
        # Verify collection conversions
        assert domain_updates["name"] == "Collection Updated Recipe"
        assert domain_updates["instructions"] == "Updated instructions"
        assert isinstance(domain_updates["ingredients"], list)
        assert isinstance(domain_updates["tags"], frozenset)
        assert api_recipe.ingredients is not None
        assert api_recipe.tags is not None
        assert len(domain_updates["ingredients"]) == len(api_recipe.ingredients)
        assert len(domain_updates["tags"]) == len(api_recipe.tags)
        
        # All other fields should be excluded
        excluded_fields = {"description", "weight_in_grams", "utensils", "total_time", "notes", "privacy", "nutri_facts", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"

    def test_partial_update_edge_cases(self):
        """Test partial update edge cases with various field combinations."""
        test_scenarios = [
            # Only instructions field
            {
                "input": {"instructions": "Only instructions"},
                "expected_count": 1,
                "expected_fields": {"instructions"}
            },
            # Only privacy field
            {
                "input": {"privacy": Privacy.PRIVATE},
                "expected_count": 1,
                "expected_fields": {"privacy"}
            },
            # Only numeric fields
            {
                "input": {"weight_in_grams": 300, "total_time": 20},
                "expected_count": 2,
                "expected_fields": {"weight_in_grams", "total_time"}
            },
            # Mixed types - check HttpUrl handling
            {
                "input": {"name": "Mixed", "privacy": Privacy.PUBLIC, "total_time": 60, "image_url": "http://example.com"},
                "expected_count": 4,
                "expected_fields": {"name", "privacy", "total_time", "image_url"}
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            update_attributes = ApiAttributesToUpdateOnRecipe(**scenario["input"])
            domain_updates = update_attributes.to_domain()
            
            # Verify only expected fields are present
            assert len(domain_updates) == scenario["expected_count"], f"Scenario {i}: Expected {scenario['expected_count']} fields, got {len(domain_updates)}"
            
            actual_fields = set(domain_updates.keys())
            assert actual_fields == scenario["expected_fields"], f"Scenario {i}: Expected fields {scenario['expected_fields']}, got {actual_fields}"
            
            # Verify values match (handle HttpUrl for image_url)
            for field_name, expected_value in scenario["input"].items():
                if field_name == "image_url":
                    # HttpUrl objects normalize URLs, so compare string representations
                    assert str(domain_updates[field_name]) == str(HttpUrl(expected_value)), f"Scenario {i}: Field {field_name} URL mismatch"
                else:
                    assert domain_updates[field_name] == expected_value, f"Scenario {i}: Field {field_name} value mismatch"

    def test_partial_update_pydantic_fields_set_tracking(self):
        """Test that __pydantic_fields_set__ correctly tracks only set fields in partial updates."""
        # Test different partial update combinations
        test_cases = [
            {"name": "Test 1"},
            {"name": "Test 2", "description": "Desc"},
            {"instructions": "Only instructions"},
            {"privacy": Privacy.PUBLIC, "notes": "Notes"},
            {"name": "Test 5", "weight_in_grams": 400, "image_url": "http://example.com"}
        ]
        
        for i, test_case in enumerate(test_cases):
            update_attributes = ApiAttributesToUpdateOnRecipe(**test_case)
            
            # Check that __pydantic_fields_set__ only contains the provided fields
            fields_set = update_attributes.__pydantic_fields_set__
            expected_fields = set(test_case.keys())
            
            assert fields_set == expected_fields, f"Test case {i}: fields_set {fields_set} != expected {expected_fields}"
            
            # Verify to_domain() respects the fields_set
            domain_updates = update_attributes.to_domain()
            domain_fields = set(domain_updates.keys())
            
            assert domain_fields == expected_fields, f"Test case {i}: domain fields {domain_fields} != expected {expected_fields}"
            
            # Verify values are correct (handle HttpUrl for image_url)
            for field_name, expected_value in test_case.items():
                if field_name == "image_url":
                    # HttpUrl objects normalize URLs, so compare string representations
                    assert str(domain_updates[field_name]) == str(HttpUrl(expected_value)), f"Test case {i}: {field_name} URL mismatch"
                else:
                    assert domain_updates[field_name] == expected_value, f"Test case {i}: {field_name} value mismatch"

    # =============================================================================
    # TASK 2.2.3: Test None vs unset field handling
    # =============================================================================

    def test_explicit_none_vs_unset_basic(self):
        """Test the difference between explicitly setting None vs not setting a field at all."""
        # Test 1: Explicitly set None for description
        update_with_explicit_none = ApiAttributesToUpdateOnRecipe(
            name="Test Recipe",
            instructions="Test instructions",
            description=None  # Explicitly set to None
        ) # type: ignore
        
        # Test 2: Don't set description at all
        update_with_unset = ApiAttributesToUpdateOnRecipe(
            name="Test Recipe",
            instructions="Test instructions"
            # description not provided at all
        ) # type: ignore
        
        # Convert both to domain
        domain_with_none = update_with_explicit_none.to_domain()
        domain_with_unset = update_with_unset.to_domain()
        
        # Explicitly set None should be included
        assert "description" in domain_with_none
        assert domain_with_none["description"] is None
        assert len(domain_with_none) == 3  # name + instructions + description
        
        # Unset field should be excluded
        assert "description" not in domain_with_unset
        assert len(domain_with_unset) == 2  # only name + instructions
        
        # Both should have name and instructions
        assert domain_with_none["name"] == "Test Recipe"
        assert domain_with_none["instructions"] == "Test instructions"
        assert domain_with_unset["name"] == "Test Recipe"
        assert domain_with_unset["instructions"] == "Test instructions"

    def test_explicit_none_vs_unset_multiple_fields(self):
        """Test None vs unset behavior across multiple fields."""
        # Create update with some explicit None values and some unset
        update_attributes = ApiAttributesToUpdateOnRecipe(
            name="Mixed Update",
            instructions="Instructions",
            description=None,      # Explicitly set to None - will be included
            notes=None,           # Explicitly set to None - will be included
            weight_in_grams=None, # Explicitly set to None - will be included
            privacy=None          # Explicitly set to None - will be converted to Privacy.PRIVATE
            # utensils, total_time, ingredients, tags, nutri_facts, image_url are not set at all
        ) # type: ignore
        
        domain_updates = update_attributes.to_domain()
        
        # Explicitly set None fields should be included
        assert "name" in domain_updates
        assert "instructions" in domain_updates
        assert "description" in domain_updates
        assert "notes" in domain_updates
        assert "weight_in_grams" in domain_updates
        assert "privacy" in domain_updates
        
        # Verify None values (except privacy which gets converted)
        assert domain_updates["name"] == "Mixed Update"
        assert domain_updates["instructions"] == "Instructions"
        assert domain_updates["description"] is None
        assert domain_updates["notes"] is None
        assert domain_updates["weight_in_grams"] is None
        assert domain_updates["privacy"] == Privacy.PRIVATE  # Converted from None
        
        # Unset fields should be excluded
        excluded_fields = {"utensils", "total_time", "ingredients", "tags", "nutri_facts", "image_url"}
        for field in excluded_fields:
            assert field not in domain_updates, f"Field {field} should be excluded but was found"
        
        # Should only have the 6 explicitly set fields
        assert len(domain_updates) == 6

    def test_explicit_none_vs_unset_for_numeric_fields(self):
        """Test None vs unset specifically for numeric fields."""
        # Test explicit None for numeric fields
        update_with_none = ApiAttributesToUpdateOnRecipe(
            name="Numeric Test",
            instructions="Instructions",
            weight_in_grams=None,  # Explicitly set to None
            total_time=None        # Explicitly set to None
        ) # type: ignore
        
        # Test unset numeric fields
        update_with_unset = ApiAttributesToUpdateOnRecipe(
            name="Numeric Test",
            instructions="Instructions"
            # weight_in_grams, total_time not provided
        ) # type: ignore
        
        domain_with_none = update_with_none.to_domain()
        domain_with_unset = update_with_unset.to_domain()
        
        # Explicit None should be included
        assert "weight_in_grams" in domain_with_none
        assert "total_time" in domain_with_none
        assert domain_with_none["weight_in_grams"] is None
        assert domain_with_none["total_time"] is None
        assert len(domain_with_none) == 4
        
        # Unset should be excluded
        assert "weight_in_grams" not in domain_with_unset
        assert "total_time" not in domain_with_unset
        assert len(domain_with_unset) == 2

    def test_explicit_none_vs_unset_for_privacy_field(self):
        """Test None vs unset specifically for privacy field."""
        # Test explicit None for privacy
        update_with_none = ApiAttributesToUpdateOnRecipe(
            name="Privacy Test",
            instructions="Instructions",
            privacy=None  # Explicitly set to None
        ) # type: ignore
        
        # Test unset privacy
        update_with_unset = ApiAttributesToUpdateOnRecipe(
            name="Privacy Test",
            instructions="Instructions"
            # privacy not provided
        ) # type: ignore
        
        domain_with_none = update_with_none.to_domain()
        domain_with_unset = update_with_unset.to_domain()
        
        # Explicit None should be included and converted to Privacy.PRIVATE
        assert "privacy" in domain_with_none
        assert domain_with_none["privacy"] == Privacy.PRIVATE  # Converted from None
        assert len(domain_with_none) == 3
        
        # Unset should be excluded
        assert "privacy" not in domain_with_unset
        assert len(domain_with_unset) == 2

    def test_explicit_none_vs_unset_for_collection_fields(self):
        """Test None vs unset for collection fields (should behave differently)."""
        # Test when not providing collections at all - they should get defaults
        update_no_collections = ApiAttributesToUpdateOnRecipe(
            name="Collection Test",
            instructions="Instructions"
            # ingredients and tags not provided - should get defaults
        ) # type: ignore
        
        # Test when explicitly setting empty collections
        update_explicit_empty = ApiAttributesToUpdateOnRecipe(
            name="Collection Test",
            instructions="Instructions",
            ingredients=frozenset(),  # Explicitly empty
            tags=frozenset()          # Explicitly empty
        ) # type: ignore
        
        domain_no_collections = update_no_collections.to_domain()
        domain_explicit_empty = update_explicit_empty.to_domain()
        
        # When not provided, collections should not be in the update (exclude_unset)
        assert "ingredients" not in domain_no_collections
        assert "tags" not in domain_no_collections
        assert len(domain_no_collections) == 2  # only name + instructions
        
        # When explicitly set to empty, they should be included
        assert "ingredients" in domain_explicit_empty
        assert "tags" in domain_explicit_empty
        assert domain_explicit_empty["ingredients"] == []
        assert domain_explicit_empty["tags"] == frozenset()
        assert len(domain_explicit_empty) == 4  # name + instructions + ingredients + tags

    def test_pydantic_fields_set_tracking_none_vs_unset(self):
        """Test that __pydantic_fields_set__ correctly distinguishes None vs unset."""
        # Test various combinations
        test_scenarios = [
            {
                "input": {"name": "Test", "instructions": "Instructions", "description": None},
                "expected_fields_set": {"name", "instructions", "description"},
                "expected_domain_fields": {"name", "instructions", "description"}
            },
            {
                "input": {"name": "Test", "instructions": "Instructions"},
                "expected_fields_set": {"name", "instructions"},
                "expected_domain_fields": {"name", "instructions"}
            },
            {
                "input": {"name": "Test", "instructions": "Instructions", "weight_in_grams": None, "notes": None},
                "expected_fields_set": {"name", "instructions", "weight_in_grams", "notes"},
                "expected_domain_fields": {"name", "instructions", "weight_in_grams", "notes"}
            },
            {
                "input": {"name": "Test", "instructions": "Instructions", "privacy": None, "image_url": None},
                "expected_fields_set": {"name", "instructions", "privacy", "image_url"},
                "expected_domain_fields": {"name", "instructions", "privacy", "image_url"}
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            update_attributes = ApiAttributesToUpdateOnRecipe(**scenario["input"])
            
            # Check __pydantic_fields_set__
            fields_set = update_attributes.__pydantic_fields_set__
            assert fields_set == scenario["expected_fields_set"], f"Scenario {i}: fields_set mismatch"
            
            # Check domain output
            domain_updates = update_attributes.to_domain()
            domain_fields = set(domain_updates.keys())
            assert domain_fields == scenario["expected_domain_fields"], f"Scenario {i}: domain fields mismatch"
            
            # Verify values are preserved (except privacy conversion)
            for field_name in scenario["expected_fields_set"]:
                expected_value = scenario["input"][field_name]
                if field_name == "privacy" and expected_value is None:
                    assert domain_updates[field_name] == Privacy.PRIVATE, f"Scenario {i}: {field_name} should be converted to Privacy.PRIVATE"
                else:
                    assert domain_updates[field_name] == expected_value, f"Scenario {i}: {field_name} value mismatch"

    def test_consistency_between_creation_methods(self):
        """Test that None vs unset behavior is consistent across different creation patterns."""
        # Method 1: Direct constructor with explicit None
        method1 = ApiAttributesToUpdateOnRecipe(
            name="Consistency Test",
            instructions="Instructions",
            description=None,
            weight_in_grams=None
        ) # type: ignore
        
        # Method 2: Create with dict that has explicit None
        data_with_none = {
            "name": "Consistency Test",
            "instructions": "Instructions",
            "description": None,
            "weight_in_grams": None
        }
        method2 = ApiAttributesToUpdateOnRecipe(**data_with_none)
        
        # Method 3: Only required fields
        method3 = ApiAttributesToUpdateOnRecipe(
            name="Consistency Test",
            instructions="Instructions"
        ) # type: ignore
        
        # All should behave the same way
        domain1 = method1.to_domain()
        domain2 = method2.to_domain()
        domain3 = method3.to_domain()
        
        # Methods 1 and 2 should be identical (explicit None)
        assert domain1 == domain2
        assert len(domain1) == 4  # name, instructions, description, weight_in_grams
        assert "description" in domain1 and domain1["description"] is None
        assert "weight_in_grams" in domain1 and domain1["weight_in_grams"] is None
        
        # Method 3 should only have required fields (unset fields excluded)
        assert len(domain3) == 2
        assert "description" not in domain3
        assert "weight_in_grams" not in domain3
        assert domain3["name"] == "Consistency Test"
        assert domain3["instructions"] == "Instructions"
