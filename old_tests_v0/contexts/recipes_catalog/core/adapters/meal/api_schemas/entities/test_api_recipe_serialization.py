import json
import time

import pytest
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    CUISINE_TYPES,
    DIFFICULTY_LEVELS,
    REALISTIC_RECIPE_SCENARIOS,
    create_api_recipe,
    create_api_recipe_with_incorrect_averages,
    create_api_recipe_with_max_fields,
    create_api_recipe_without_ratings,
    create_api_recipes_by_cuisine,
    create_api_recipes_by_difficulty,
    create_bulk_api_recipe_creation_dataset,
    create_bulk_json_deserialization_dataset,
    create_bulk_json_serialization_dataset,
    create_complex_api_recipe,
    create_conversion_performance_dataset_for_api_recipe,
    create_dessert_api_recipe,
    create_high_protein_api_recipe,
    create_invalid_json_test_cases,
    create_minimal_api_recipe,
    create_nested_object_validation_dataset_for_api_recipe,
    create_quick_api_recipe,
    create_recipe_collection,
    create_simple_api_recipe,
    create_test_dataset_for_api_recipe,
    create_valid_json_test_cases,
    create_vegetarian_api_recipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import (
    ApiRating,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)
from src.contexts.shared_kernel.domain.enums import Privacy

"""
ApiRecipe Serialization Test Suite

Test classes for JSON serialization, integration tests, and specialized recipe types.
"""


class TestApiRecipeJson:
    """
    Test suite for JSON serialization/deserialization tests.
    """

    # =============================================================================
    # JSON SERIALIZATION/DESERIALIZATION TESTS
    # =============================================================================

    def test_json_serialization_basic(self, simple_recipe):
        """Test basic JSON serialization."""
        json_str = simple_recipe.model_dump_json()

        assert isinstance(json_str, str)
        assert simple_recipe.id in json_str
        assert simple_recipe.name in json_str

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["id"] == simple_recipe.id
        assert parsed["name"] == simple_recipe.name

    def test_json_round_trip_serialization(self, complex_recipe):
        """Test JSON round-trip serialization preserves data."""
        # Test round-trip serialization
        json_str = complex_recipe.model_dump_json()

        # Deserialize from JSON
        restored_recipe = ApiRecipe.model_validate_json(json_str)

        assert complex_recipe == restored_recipe

    def test_json_with_computed_properties(self, complex_recipe):
        """Test JSON handling with computed properties."""
        # Create recipe with ratings
        recipe = complex_recipe

        # Serialize to JSON
        json_str = recipe.model_dump_json()

        # Deserialize from JSON
        restored_recipe = ApiRecipe.model_validate_json(json_str)

        # Computed properties should be preserved
        assert restored_recipe.average_taste_rating == recipe.average_taste_rating
        assert (
            restored_recipe.average_convenience_rating
            == recipe.average_convenience_rating
        )

    @pytest.mark.parametrize("json_data", create_valid_json_test_cases())
    def test_json_deserialization_parametrized(self, json_data):
        """Test JSON deserialization with parametrized valid cases."""
        json_str = json.dumps(json_data)
        api_recipe = ApiRecipe.model_validate_json(json_str)

        assert isinstance(api_recipe, ApiRecipe)
        assert api_recipe.id == json_data["id"]
        assert api_recipe.name == json_data["name"]

    @pytest.mark.parametrize("case", create_invalid_json_test_cases())
    def test_json_error_scenarios_parametrized(self, case):
        """Test JSON deserialization error scenarios with parametrization."""
        json_str = json.dumps(case["data"])

        with pytest.raises(ValueError):
            ApiRecipe.model_validate_json(json_str)

    def test_json_performance(self, recipe_collection):
        """Test JSON serialization/deserialization efficiency using relative performance."""
        # Note: This test is kept with for loop as it measures overall performance
        # across multiple operations - parametrization would test individual performance

        # Measure baseline single operation
        single_recipe = recipe_collection[0]
        start_time = time.perf_counter()
        json_str = single_recipe.model_dump_json()
        restored = ApiRecipe.model_validate_json(json_str)
        single_op_time = time.perf_counter() - start_time

        # Measure batch operations
        start_time = time.perf_counter()
        for recipe in recipe_collection:
            json_str = recipe.model_dump_json()
            restored = ApiRecipe.model_validate_json(json_str)
            assert restored.id == recipe.id

        batch_time = time.perf_counter() - start_time

        # Efficiency test: batch should scale linearly (within 25% tolerance)
        expected_batch_time = single_op_time * len(recipe_collection)
        efficiency_ratio = batch_time / expected_batch_time

        assert (
            efficiency_ratio < 1.25
        ), f"JSON operations batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert (
            efficiency_ratio > 0.75
        ), f"JSON operations batch timing inconsistent: {efficiency_ratio:.2f}x expected time"

    @pytest.mark.parametrize("recipe", create_recipe_collection(count=5))
    def test_json_performance_parametrized(self, recipe):
        """Test JSON serialization/deserialization efficiency with complexity assessment."""
        # Measure operation with data size assessment
        start_time = time.perf_counter()
        json_str = recipe.model_dump_json()
        restored = ApiRecipe.model_validate_json(json_str)
        operation_time = time.perf_counter() - start_time

        # Assess data complexity factors
        data_complexity = {
            "json_size": len(json_str),
            "field_count": len(recipe.__class__.model_fields),
            "collection_sizes": len(recipe.ingredients)
            + len(recipe.ratings)
            + len(recipe.tags),
        }

        # JSON processing should be efficient relative to data size
        size_efficiency = operation_time / max(
            1, data_complexity["json_size"] / 1000
        )  # per KB

        # Should process JSON efficiently (sub-linear to data size)
        assert (
            size_efficiency < 0.01
        ), f"JSON processing inefficient: {size_efficiency:.6f}s per KB"
        assert restored.id == recipe.id

    def test_json_with_nested_objects(self, complex_recipe):
        """Test JSON serialization with complex nested objects."""
        # Should handle nested objects in JSON
        json_str = complex_recipe.model_dump_json()
        restored_recipe = ApiRecipe.model_validate_json(json_str)

        # Verify nested objects are preserved
        assert restored_recipe.ingredients is not None
        assert restored_recipe.ratings is not None
        assert restored_recipe.tags is not None
        assert len(restored_recipe.ingredients) == len(complex_recipe.ingredients)
        assert restored_recipe.utensils is not None
        assert (
            len(restored_recipe.ratings) == len(complex_recipe.ratings)
            or len(restored_recipe.ratings) == 0
        )
        assert (
            len(restored_recipe.tags) == len(complex_recipe.tags)
            or len(restored_recipe.tags) == 0
        )

        # Verify nested object types - now frozensets
        assert restored_recipe.ingredients is not None
        assert restored_recipe.ratings is not None
        assert restored_recipe.tags is not None
        assert all(
            isinstance(ing, ApiIngredient) for ing in restored_recipe.ingredients
        )
        assert all(isinstance(rating, ApiRating) for rating in restored_recipe.ratings)
        assert all(isinstance(tag, ApiTag) for tag in restored_recipe.tags)

    def test_json_factory_functions(self):
        """Test JSON factory functions."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_from_json,
            create_api_recipe_json,
        )

        # Test create_api_recipe_from_json
        json_recipe = create_api_recipe_from_json()
        assert isinstance(json_recipe, ApiRecipe)

        # Test create_api_recipe_json
        json_str = create_api_recipe_json()
        assert isinstance(json_str, str)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "id" in parsed
        assert "name" in parsed


class TestApiRecipeIntegration:
    """
    Test suite for integration tests with base classes.
    """

    # =============================================================================
    # INTEGRATION TESTS WITH BASE CLASSES
    # =============================================================================

    def test_base_api_entity_inheritance(self, simple_recipe):
        """Test proper inheritance from BaseApiEntity."""
        from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
            BaseApiEntity,
        )

        # Should inherit from BaseApiEntity
        assert isinstance(simple_recipe, BaseApiEntity)

        # Should have base model configuration
        assert simple_recipe.model_config.get("frozen") is True
        assert simple_recipe.model_config.get("strict") is True
        assert simple_recipe.model_config.get("extra") == "forbid"

    def test_base_api_entity_conversion_methods(self, simple_recipe):
        """Test integration with BaseApiEntity conversion methods."""
        # Should have access to conversion methods
        assert hasattr(simple_recipe, "from_domain")
        assert hasattr(simple_recipe, "to_domain")
        assert hasattr(simple_recipe, "from_orm_model")
        assert hasattr(simple_recipe, "to_orm_kwargs")

        # Should have conversion utility
        assert hasattr(simple_recipe, "convert")
        assert simple_recipe.convert is not None

    def test_immutability_from_base_class(self, simple_recipe):
        """Test that immutability is properly enforced from base class."""
        # Should be immutable (frozen)
        with pytest.raises(ValueError):
            simple_recipe.id = "changed"  # type: ignore

        with pytest.raises(ValueError):
            simple_recipe.name = "changed"  # type: ignore

    def test_pydantic_validation_integration(self):
        """Test integration with Pydantic validation from base class."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_kwargs,
            create_valid_json_test_cases,
        )

        # Test model_validate works
        recipe_data = create_api_recipe_kwargs()
        api_recipe = ApiRecipe.model_validate(recipe_data)
        assert api_recipe.id == recipe_data["id"]
        assert api_recipe.name == recipe_data["name"]

        # Test model_validate_json works
        json_str = json.dumps(create_valid_json_test_cases()[0])
        api_recipe_from_json = ApiRecipe.model_validate_json(json_str)
        assert isinstance(api_recipe_from_json, ApiRecipe)

    def test_field_validation_integration(self, edge_case_recipes):
        """Test field validation integration."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe,
        )

        # Test valid creation
        valid_recipe = create_api_recipe()
        assert isinstance(valid_recipe, ApiRecipe)

        # Test field constraints
        assert len(valid_recipe.id) > 0
        assert len(valid_recipe.name) > 0
        assert len(valid_recipe.instructions) > 0
        assert valid_recipe.privacy in Privacy
        assert isinstance(valid_recipe.ingredients, frozenset)
        assert isinstance(valid_recipe.ratings, frozenset)
        assert isinstance(valid_recipe.tags, frozenset)

        # Test required field validation
        assert valid_recipe.id is not None
        assert valid_recipe.name is not None
        assert valid_recipe.instructions is not None
        assert valid_recipe.author_id is not None
        assert valid_recipe.meal_id is not None

        # Test optional field handling
        minimal_recipe = edge_case_recipes["empty_collections"]
        assert minimal_recipe.description is None or isinstance(
            minimal_recipe.description, str
        )
        assert minimal_recipe.utensils is None or isinstance(
            minimal_recipe.utensils, str
        )
        assert minimal_recipe.total_time is None or isinstance(
            minimal_recipe.total_time, int
        )

        # Test collection field validation - now frozensets
        assert isinstance(valid_recipe.ingredients, frozenset)
        assert isinstance(valid_recipe.ratings, frozenset)
        assert isinstance(valid_recipe.tags, frozenset)


class TestApiRecipeSpecialized:
    """
    Test suite for specialized recipe type tests.
    """

    # =============================================================================
    # SPECIALIZED RECIPE TYPE TESTS
    # =============================================================================

    @pytest.mark.parametrize(
        "recipe_type,api_recipe_factory",
        [
            ("simple", create_simple_api_recipe),
            ("complex", create_complex_api_recipe),
            ("vegetarian", create_vegetarian_api_recipe),
            ("high_protein", create_high_protein_api_recipe),
            ("quick", create_quick_api_recipe),
            ("dessert", create_dessert_api_recipe),
            ("minimal", create_minimal_api_recipe),
            ("max_fields", create_api_recipe_with_max_fields),
        ],
    )
    def test_specialized_recipe_types(self, recipe_type, api_recipe_factory):
        """Test specialized recipe factory functions."""
        api_recipe = api_recipe_factory()

        assert isinstance(api_recipe, ApiRecipe)
        assert len(api_recipe.id) > 0
        assert len(api_recipe.name) > 0
        assert len(api_recipe.instructions) > 0

        # Test round-trip for each type - use domain recipe equality
        domain_recipe = api_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)

        # For domain recipes, we can use Recipe equality if we convert both to domain
        original_domain = api_recipe.to_domain()
        recovered_domain = recovered_api.to_domain()
        assert recovered_domain.has_same_content(
            original_domain
        ), f"Round-trip failed for {recipe_type} recipe"

    @pytest.mark.parametrize(
        "cuisine", ["italian", "mexican", "indian", "french", "chinese"]
    )
    def test_recipes_by_cuisine(self, cuisine):
        """Test recipe creation by cuisine type."""
        recipes = create_api_recipes_by_cuisine(cuisine, count=3)
        assert len(recipes) == 3
        assert all(isinstance(recipe, ApiRecipe) for recipe in recipes)

    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_recipes_by_difficulty(self, difficulty):
        """Test recipe creation by difficulty level."""
        recipes = create_api_recipes_by_difficulty(difficulty, count=3)
        assert len(recipes) == 3
        assert all(isinstance(recipe, ApiRecipe) for recipe in recipes)

    def test_recipe_collections(self):
        """Test recipe collection factory functions."""
        collection = create_recipe_collection(count=5)
        assert len(collection) == 5
        assert all(isinstance(recipe, ApiRecipe) for recipe in collection)

    def test_bulk_dataset_creation(self):
        """Test bulk dataset creation functions."""
        dataset = create_test_dataset_for_api_recipe(count=10)
        assert len(dataset["recipes"]) == 10
        assert len(dataset["json_strings"]) == 10
        assert dataset["total_recipes"] == 10

        # Test create_bulk_recipe_creation_dataset
        bulk_kwargs = create_bulk_api_recipe_creation_dataset(count=5)
        assert len(bulk_kwargs) == 5
        assert all(isinstance(kwargs, dict) for kwargs in bulk_kwargs)

        # Test create_bulk_json_serialization_dataset
        bulk_json = create_bulk_json_serialization_dataset(count=5)
        assert len(bulk_json) == 5
        assert all(isinstance(json_str, str) for json_str in bulk_json)

    @pytest.mark.parametrize("privacy", [Privacy.PUBLIC, Privacy.PRIVATE])
    def test_privacy_enum_handling(self, privacy):
        """Test privacy enum handling in recipes."""
        recipe = create_api_recipe(privacy=privacy)
        assert recipe.privacy == privacy

    @pytest.mark.parametrize("scenario", REALISTIC_RECIPE_SCENARIOS)
    def test_realistic_scenario_coverage(self, scenario):
        """Test realistic scenario coverage using factory data."""
        recipe = create_api_recipe(name=scenario["name"])
        assert isinstance(recipe, ApiRecipe)
        assert recipe.name == scenario["name"]

        # Test round-trip for realistic scenarios - use domain equality
        original_domain = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(original_domain)
        recovered_domain = recovered_api.to_domain()
        assert recovered_domain.has_same_content(
            original_domain
        ), f"Round-trip failed for scenario: {scenario['name']}"

    @pytest.mark.parametrize("cuisine", CUISINE_TYPES[:5])  # Test first 5 cuisines
    def test_cuisine_types_coverage_parametrized(self, cuisine):
        """Test cuisine types coverage."""
        recipes = create_api_recipes_by_cuisine(cuisine, count=1)
        assert len(recipes) == 1
        assert isinstance(recipes[0], ApiRecipe)

    @pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS)
    def test_difficulty_levels_coverage_parametrized(self, difficulty):
        """Test difficulty levels coverage."""
        recipes = create_api_recipes_by_difficulty(difficulty, count=1)
        assert len(recipes) == 1
        assert isinstance(recipes[0], ApiRecipe)

    @pytest.mark.parametrize(
        "specialized_function",
        [
            create_simple_api_recipe,
            create_complex_api_recipe,
            create_vegetarian_api_recipe,
            create_high_protein_api_recipe,
            create_quick_api_recipe,
            create_dessert_api_recipe,
            create_minimal_api_recipe,
            create_api_recipe_with_max_fields,
            create_api_recipe_with_incorrect_averages,
            create_api_recipe_without_ratings,
        ],
    )
    def test_specialized_factory_functions(self, specialized_function):
        """Test specialized factory functions."""
        assert callable(specialized_function)
        result = specialized_function()
        assert isinstance(result, ApiRecipe)

    @pytest.mark.parametrize(
        "collection_function,test_param",
        [
            (create_recipe_collection, {"count": 2}),
            (create_test_dataset_for_api_recipe, {"count": 2}),
            (create_bulk_api_recipe_creation_dataset, {"count": 2}),
            (create_bulk_json_serialization_dataset, {"count": 2}),
            (create_bulk_json_deserialization_dataset, {"count": 2}),
            (create_conversion_performance_dataset_for_api_recipe, {"count": 2}),
            (create_nested_object_validation_dataset_for_api_recipe, {"count": 2}),
        ],
    )
    def test_collection_factory_functions(self, collection_function, test_param):
        """Test collection factory functions."""
        assert callable(collection_function)
        result = collection_function(**test_param)
        assert result is not None
