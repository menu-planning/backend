"""
ApiMeal Core Functionality Test Suite

Test classes for core ApiMeal functionality including basic conversions,
round-trip validations, and computed properties.

Following the same pattern as test_api_recipe_core.py but adapted for ApiMeal.
"""

import pytest

# Import test data factories
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal_with_incorrect_computed_properties,
    create_api_meal_with_max_recipes,
    create_api_meal_without_recipes,
    create_complex_api_meal,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)


class TestApiMealBasics:
    """
    Test suite for basic ApiMeal conversion methods (>95% coverage target).
    """

    # =============================================================================
    # UNIT TESTS FOR ALL CONVERSION METHODS (>95% COVERAGE TARGET)
    # =============================================================================

    def test_from_domain_basic_conversion(self, domain_meal):
        """Test from_domain basic conversion functionality."""
        api_meal = ApiMeal.from_domain(domain_meal)

        # Get all ApiMeal model fields to test basic conversion comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define fields to exclude from basic conversion test (tested in other specific tests)
        excluded_fields = {
            "recipes",
            "tags",
            "nutri_facts",  # Tested in nested objects test
            "weight_in_grams",
            "calorie_density",
            "carbo_percentage",
            "protein_percentage",
            "total_fat_percentage",  # Tested in computed properties test
        }

        assert isinstance(api_meal, ApiMeal)

        for field_name in api_model_fields:
            if field_name in excluded_fields:
                continue

            # Check if this field exists in the domain Meal class
            if not hasattr(domain_meal, field_name):
                continue

            # Get values from both API and domain
            api_value = getattr(api_meal, field_name)
            domain_value = getattr(domain_meal, field_name)

            # Basic scalar fields should match directly
            if (
                isinstance(domain_value, (str, int, float, bool))
                or domain_value is None
            ):
                assert (
                    api_value == domain_value
                ), f"Basic field '{field_name}' mismatch: API({api_value}) != Domain({domain_value})"
            elif hasattr(domain_value, "value"):  # Enum-like objects
                assert (
                    api_value == domain_value.value
                ), f"Enum field '{field_name}' mismatch: API({api_value}) != Domain({domain_value.value})"
            else:
                # For other types, ensure conversion happened
                assert (
                    api_value is not None or domain_value is None
                ), f"Field '{field_name}' conversion failed: API({api_value}) from Domain({domain_value})"

        # Use deterministic comparison as additional validation
        expected_api = ApiMeal.from_domain(domain_meal)
        assert api_meal == expected_api, "API meal conversion should be deterministic"

    def test_from_domain_nested_objects_conversion(self, domain_meal):
        """Test from_domain properly converts nested objects."""
        api_meal = ApiMeal.from_domain(domain_meal)

        # Get all ApiMeal model fields to test nested objects comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define known nested object fields based on domain analysis
        known_nested_objects = {"recipes", "tags", "nutri_facts"}

        for field_name in api_model_fields:
            api_value = getattr(api_meal, field_name)
            domain_value = getattr(domain_meal, field_name, None)

            if field_name == "recipes":
                known_nested_objects.remove("recipes")
                # Test recipes conversion
                domain_recipes = domain_value or []
                assert len(api_value) == len(domain_recipes)
                assert all(isinstance(recipe, ApiRecipe) for recipe in api_value)
                assert isinstance(api_value, list)

            elif field_name == "tags":
                known_nested_objects.remove("tags")
                # Test tags conversion - should be frozenset
                domain_tags = domain_value or set()
                assert len(api_value) == len(domain_tags)
                assert all(isinstance(tag, ApiTag) for tag in api_value)
                assert isinstance(api_value, frozenset)

            elif field_name == "nutri_facts":
                known_nested_objects.remove("nutri_facts")
                # Test nutri_facts conversion
                if domain_value:
                    assert isinstance(api_value, ApiNutriFacts)
                    # Verify nested nutritional values are properly converted
                    for nutri_field in ApiNutriFacts.model_fields.keys():
                        api_nutri_value = getattr(api_value, nutri_field)
                        domain_nutri_value = getattr(domain_value, nutri_field)
                        if (
                            api_nutri_value is not None
                            and domain_nutri_value is not None
                        ):
                            assert api_nutri_value.value == domain_nutri_value.value
                            assert api_nutri_value.unit == domain_nutri_value.unit.value
                else:
                    assert api_value is None

        # Ensure we tested all known nested objects
        assert (
            len(known_nested_objects) == 0
        ), f"All nested objects should be tested, but these were missed: {known_nested_objects}"

    def test_from_domain_computed_properties(self, complex_meal):
        """Test from_domain correctly handles computed properties."""
        api_meal = ApiMeal.from_domain(complex_meal)

        # Get all ApiMeal model fields
        api_model_fields = ApiMeal.model_fields.keys()

        # Define known computed properties based on domain analysis
        # These are properties that are computed/derived rather than stored directly
        known_computed_properties = {
            "nutri_facts",
            "weight_in_grams",
            "calorie_density",
            "carbo_percentage",
            "protein_percentage",
            "total_fat_percentage",
        }

        for field_name in api_model_fields:
            # Check if this field exists in the domain Meal class
            if not hasattr(complex_meal, field_name):
                assert False, f"{field_name} (not in domain)"

            # Get values from both API and domain
            api_value = getattr(api_meal, field_name)
            domain_value = getattr(complex_meal, field_name)

            # Compare the computed property values
            if field_name == "nutri_facts":
                known_computed_properties.remove("nutri_facts")
                # Special handling for nutri_facts
                if api_value is not None and domain_value is not None:
                    # Compare nutritional values
                    for name in ApiNutriFacts.model_fields.keys():
                        api_nutri_fact = getattr(api_value, name)
                        domain_nutri_fact = getattr(domain_value, name)
                        assert api_nutri_fact.value == domain_nutri_fact.value
                        assert domain_nutri_fact.unit.value == api_nutri_fact.unit
                else:
                    assert (
                        False
                    ), f"nutri_facts null: API={api_value}, Domain={domain_value}"

            elif field_name in known_computed_properties:
                known_computed_properties.remove(field_name)
                # Special handling for float values - use approximate comparison
                if api_value is not None and domain_value is not None:
                    assert (
                        abs(api_value - domain_value) < 0.001
                    ), f"{field_name} mismatch: API={api_value}, Domain={domain_value}"
                else:
                    assert (
                        False
                    ), f"{field_name} null: API={api_value}, Domain={domain_value}"

            elif isinstance(api_value, (list, set, frozenset)):
                continue

            else:
                # Direct comparison for other computed properties
                # Handle HttpUrl types - compare string representations
                if hasattr(api_value, "__class__") and "HttpUrl" in str(
                    type(api_value)
                ):
                    assert str(api_value) == str(
                        domain_value
                    ), f"{field_name} mismatch: API={api_value}, Domain={domain_value}"
                else:
                    assert (
                        api_value == domain_value
                    ), f"{field_name} mismatch: API={api_value}, Domain={domain_value}"

        # Ensure we compared the expected computed properties
        assert (
            len(known_computed_properties) == 0
        ), f"All computed properties should be compared, but"

    def test_from_domain_with_empty_collections(self, domain_meal):
        """Test from_domain handles empty collections correctly."""
        # Use the existing domain meal but ensure collections are empty
        domain_meal._recipes = []
        domain_meal._tags = set()
        api_meal = ApiMeal.from_domain(domain_meal)

        assert api_meal.recipes == []
        assert api_meal.tags == frozenset()

    def test_to_domain_basic_conversion(self, simple_api_meal):
        """Test to_domain basic conversion functionality."""
        domain_meal = simple_api_meal.to_domain()

        # Get all ApiMeal model fields to test basic conversion comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define fields to exclude from basic conversion test (tested in other specific tests)
        excluded_fields = {
            "recipes",
            "tags",  # Tested in collection conversion test
            "nutri_facts",  # Tested in nutrition facts conversion test
            "weight_in_grams",
            "calorie_density",
            "carbo_percentage",
            "protein_percentage",
            "total_fat_percentage",  # Computed properties
        }

        assert isinstance(domain_meal, Meal)

        for field_name in api_model_fields:
            if field_name in excluded_fields:
                continue

            # Check if this field exists in both API and domain
            if not hasattr(simple_api_meal, field_name) or not hasattr(
                domain_meal, field_name
            ):
                continue

            # Get values from both API and domain
            api_value = getattr(simple_api_meal, field_name)
            domain_value = getattr(domain_meal, field_name)

            # Basic scalar fields should match directly
            if isinstance(api_value, (str, int, float, bool)) or api_value is None:
                assert (
                    api_value == domain_value
                ), f"Basic field '{field_name}' mismatch: API({api_value}) != Domain({domain_value})"
            elif hasattr(api_value, "value"):  # Enum-like objects from API
                assert (
                    api_value.value == domain_value.value
                    if hasattr(domain_value, "value")
                    else domain_value
                ), f"Enum field '{field_name}' mismatch: API({api_value}) != Domain({domain_value})"
            else:
                # For other types, ensure conversion happened properly
                assert (
                    domain_value is not None or api_value is None
                ), f"Field '{field_name}' conversion failed: Domain({domain_value}) from API({api_value})"

        # Use comprehensive content comparison as additional validation
        expected_domain = simple_api_meal.to_domain()
        assert domain_meal.has_same_content(
            expected_domain
        ), "Domain meal conversion should be deterministic"

    def test_to_domain_collection_type_conversion(self, complex_api_meal):
        """Test to_domain converts collections correctly."""
        domain_meal = complex_api_meal.to_domain()

        # Get all ApiMeal model fields to test collection conversions comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define known collection fields based on domain analysis
        known_collections = {"recipes", "tags"}

        for field_name in api_model_fields:
            if field_name not in known_collections:
                continue

            api_value = getattr(complex_api_meal, field_name)
            domain_value = getattr(domain_meal, field_name)

            if field_name == "recipes":
                known_collections.remove("recipes")
                # Recipes should be converted from list to list (same type)
                assert isinstance(api_value, list), f"API recipes should be list"
                assert isinstance(domain_value, list), f"Domain recipes should be list"
                assert len(domain_value) == len(
                    api_value
                ), f"Recipes count should match"

                # Each recipe should be properly converted to domain Recipe
                for i, (api_recipe, domain_recipe) in enumerate(
                    zip(api_value, domain_value, strict=False)
                ):
                    assert isinstance(
                        api_recipe, ApiRecipe
                    ), f"API recipe[{i}] should be ApiRecipe"
                    # Domain recipe type checking depends on the domain implementation
                    assert (
                        domain_recipe is not None
                    ), f"Domain recipe[{i}] should not be None"

            elif field_name == "tags":
                known_collections.remove("tags")
                # Tags should be converted from frozenset to set
                assert isinstance(api_value, frozenset), f"API tags should be frozenset"
                assert isinstance(domain_value, set), f"Domain tags should be set"
                assert len(domain_value) == len(api_value), f"Tags count should match"

                # Tag content should be preserved across conversion
                api_tag_contents = {(tag.key, tag.value, tag.type) for tag in api_value}
                domain_tag_contents = {
                    (tag.key, tag.value, tag.type) for tag in domain_value
                }
                assert (
                    api_tag_contents == domain_tag_contents
                ), f"Tag contents should be preserved across conversion"

        # Ensure we tested all known collections
        assert (
            len(known_collections) == 0
        ), f"All collections should be tested, but these were missed: {known_collections}"

    def test_to_domain_nutrition_facts_conversion(self, complex_api_meal):
        """Test that computed nutrition facts are recalculated by domain, ignoring API values."""
        domain_meal = complex_api_meal.to_domain()

        # The domain should ignore API computed properties and calculate its own values
        # This tests that the domain is the source of truth for computed properties
        assert domain_meal.nutri_facts is not None

        # Verify that domain values are calculated from recipes, not taken from API
        # This might be different from the original API values (which is correct behavior)
        expected_calories = sum(
            recipe.nutri_facts.calories.value if recipe.nutri_facts else 0
            for recipe in complex_api_meal.recipes
        )
        expected_protein = sum(
            recipe.nutri_facts.protein.value if recipe.nutri_facts else 0
            for recipe in complex_api_meal.recipes
        )
        expected_carbs = sum(
            recipe.nutri_facts.carbohydrate.value if recipe.nutri_facts else 0
            for recipe in complex_api_meal.recipes
        )

        # Domain should have computed correct values from recipes
        assert abs(domain_meal.nutri_facts.calories.value - expected_calories) < 0.1
        assert abs(domain_meal.nutri_facts.protein.value - expected_protein) < 0.1
        assert abs(domain_meal.nutri_facts.carbohydrate.value - expected_carbs) < 0.1

        # Verify units are correctly converted
        assert domain_meal.nutri_facts.calories.unit.value == "kcal"
        assert domain_meal.nutri_facts.protein.unit.value == "g"
        assert domain_meal.nutri_facts.carbohydrate.unit.value == "g"

    def test_from_orm_model_basic_conversion(self, real_orm_meal):
        """Test from_orm_model basic conversion functionality."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)

        # Get all ApiMeal model fields to test basic conversion comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define fields to exclude from basic conversion test (tested in other specific tests)
        excluded_fields = {
            "recipes",
            "tags",
            "nutri_facts",  # Tested in nested objects test
            "weight_in_grams",
            "calorie_density",
            "carbo_percentage",
            "protein_percentage",
            "total_fat_percentage",  # Tested in computed properties test
        }

        assert isinstance(api_meal, ApiMeal)

        for field_name in api_model_fields:
            if field_name in excluded_fields:
                continue

            # Check if this field exists in the ORM model
            if not hasattr(real_orm_meal, field_name):
                continue

            # Get values from both API and ORM
            api_value = getattr(api_meal, field_name)
            orm_value = getattr(real_orm_meal, field_name)

            # Basic scalar fields should match directly
            if isinstance(orm_value, (str, int, float, bool)) or orm_value is None:
                assert (
                    api_value == orm_value
                ), f"Basic field '{field_name}' mismatch: API({api_value}) != ORM({orm_value})"
            elif hasattr(orm_value, "value"):  # Enum-like objects
                assert (
                    api_value == orm_value.value
                ), f"Enum field '{field_name}' mismatch: API({api_value}) != ORM({orm_value.value})"
            else:
                # For other types, ensure conversion happened
                assert (
                    api_value is not None or orm_value is None
                ), f"Field '{field_name}' conversion failed: API({api_value}) from ORM({orm_value})"

        # Use deterministic comparison as additional validation
        expected_api = ApiMeal.from_orm_model(real_orm_meal)
        assert api_meal == expected_api, "ORM to API conversion should be deterministic"

    def test_from_orm_model_nested_objects_conversion(self, real_orm_meal):
        """Test from_orm_model handles nested objects."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)

        # Get all ApiMeal model fields to test nested objects comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define known nested object fields based on domain analysis
        known_nested_objects = {"recipes", "tags", "nutri_facts"}

        for field_name in api_model_fields:
            if field_name not in known_nested_objects:
                continue

            api_value = getattr(api_meal, field_name)
            orm_value = getattr(real_orm_meal, field_name, None)

            if field_name == "recipes":
                known_nested_objects.remove("recipes")
                # Should handle collections properly
                assert isinstance(api_value, list), f"API recipes should be list"
                if orm_value is not None:
                    assert len(api_value) == len(
                        orm_value
                    ), f"Recipes count should match ORM"
                    # Each recipe should be converted to ApiRecipe
                    assert all(
                        isinstance(recipe, ApiRecipe) for recipe in api_value
                    ), f"All recipes should be ApiRecipe instances"
                else:
                    assert (
                        api_value == []
                    ), f"API recipes should be empty list when ORM is None"

            elif field_name == "tags":
                known_nested_objects.remove("tags")
                # Should handle collections properly
                assert isinstance(api_value, frozenset), f"API tags should be frozenset"
                if orm_value is not None:
                    assert len(api_value) == len(
                        orm_value
                    ), f"Tags count should match ORM"
                    # Each tag should be converted to ApiTag
                    assert all(
                        isinstance(tag, ApiTag) for tag in api_value
                    ), f"All tags should be ApiTag instances"
                else:
                    assert (
                        api_value == frozenset()
                    ), f"API tags should be empty frozenset when ORM is None"

            elif field_name == "nutri_facts":
                known_nested_objects.remove("nutri_facts")
                # Should handle nutrition facts conversion properly
                if orm_value is not None:
                    assert isinstance(
                        api_value, ApiNutriFacts
                    ), f"API nutri_facts should be ApiNutriFacts"
                    # Verify nested nutritional values are properly converted
                    for nutri_field in ApiNutriFacts.model_fields.keys():
                        api_nutri_value = getattr(api_value, nutri_field)
                        orm_nutri_value = getattr(orm_value, nutri_field, None)
                        if orm_nutri_value is not None:
                            assert (
                                api_nutri_value is not None
                            ), f"API nutri_facts.{nutri_field} should not be None when ORM has value"
                            assert (
                                api_nutri_value.value == orm_nutri_value
                            ), f"API nutri_facts.{nutri_field} value should match ORM"
                else:
                    assert (
                        api_value is None
                    ), f"API nutri_facts should be None when ORM is None"

        # Ensure we tested all known nested objects
        assert (
            len(known_nested_objects) == 0
        ), f"All nested objects should be tested, but these were missed: {known_nested_objects}"

    def test_from_orm_model_computed_properties(self, real_orm_meal):
        """Test from_orm_model correctly handles computed properties."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)

        # Get all ApiMeal model fields
        api_model_fields = ApiMeal.model_fields.keys()

        # Define known computed properties based on domain analysis
        known_computed_properties = {
            "nutri_facts",
            "weight_in_grams",
            "calorie_density",
            "carbo_percentage",
            "protein_percentage",
            "total_fat_percentage",
        }

        for field_name in api_model_fields:
            # Check if this field exists in the ORM model
            if not hasattr(real_orm_meal, field_name):
                continue

            # Get values from both API and ORM
            api_value = getattr(api_meal, field_name)
            orm_value = getattr(real_orm_meal, field_name, None)

            # Compare the computed property values
            if field_name == "nutri_facts":
                known_computed_properties.remove("nutri_facts")
                # Special handling for nutri_facts - test comprehensive conversion
                if api_value is not None and orm_value is not None:
                    # The ORM nutri_facts should have been converted to ApiNutriFacts
                    assert isinstance(api_value, ApiNutriFacts)
                    # Compare each nutritional component
                    for nutri_field in ApiNutriFacts.model_fields.keys():
                        api_nutri_value = getattr(api_value, nutri_field)
                        orm_nutri_value = getattr(orm_value, nutri_field, None)
                        if api_nutri_value is not None and orm_nutri_value is not None:
                            assert api_nutri_value.value == orm_nutri_value
                            # API should have proper unit enum values
                            assert hasattr(api_nutri_value, "unit")
                elif api_value is None and orm_value is None:
                    # Both None is acceptable
                    pass
                else:
                    assert (
                        False
                    ), f"nutri_facts mismatch: API={api_value}, ORM={orm_value}"

            elif field_name in known_computed_properties:
                known_computed_properties.remove(field_name)
                # Special handling for float computed properties - use approximate comparison
                if api_value is not None and orm_value is not None:
                    assert (
                        abs(api_value - orm_value) < 0.001
                    ), f"{field_name} mismatch: API={api_value}, ORM={orm_value}"
                elif api_value is None and orm_value is None:
                    # Both None is acceptable
                    pass
                else:
                    assert (
                        False
                    ), f"{field_name} null mismatch: API={api_value}, ORM={orm_value}"

            elif isinstance(api_value, (list, set, frozenset)):
                continue

            else:
                # Direct comparison for other properties
                assert (
                    api_value == orm_value
                ), f"{field_name} mismatch: API={api_value}, ORM={orm_value}"

        # Ensure we compared all expected computed properties that exist in ORM
        remaining_computed_props = {
            prop for prop in known_computed_properties if hasattr(real_orm_meal, prop)
        }
        assert (
            len(remaining_computed_props) == 0
        ), f"All computed properties should be compared, but these were missed: {remaining_computed_props}"

    def test_to_orm_kwargs_basic_conversion(self, simple_api_meal):
        """Test to_orm_kwargs basic conversion functionality."""
        kwargs = simple_api_meal.to_orm_kwargs()

        # Get all ApiMeal model fields to test basic conversion comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define fields to exclude from basic conversion test (complex nested objects)
        excluded_fields = {"recipes", "tags", "nutri_facts"}

        assert isinstance(kwargs, dict)

        for field_name in api_model_fields:
            if field_name in excluded_fields:
                continue

            # Get values from both API and ORM kwargs
            api_value = getattr(simple_api_meal, field_name)
            orm_value = kwargs.get(field_name)

            # Basic scalar fields should match directly
            if isinstance(api_value, (str, int, float, bool)) or api_value is None:
                assert (
                    api_value == orm_value
                ), f"Basic field '{field_name}' mismatch: API({api_value}) != ORM({orm_value})"
            elif hasattr(api_value, "value"):  # Enum-like objects
                assert (
                    api_value.value == orm_value
                ), f"Enum field '{field_name}' mismatch: API({api_value.value}) != ORM({orm_value})"
            else:
                # For other types, ensure they're present in kwargs
                assert (
                    field_name in kwargs
                ), f"Field '{field_name}' should be present in ORM kwargs"

    def test_to_orm_kwargs_nested_objects_conversion(self, complex_api_meal):
        """Test to_orm_kwargs converts nested objects correctly."""
        kwargs = complex_api_meal.to_orm_kwargs()

        # Get all ApiMeal model fields to test nested objects comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define known nested object fields based on domain analysis
        known_nested_objects = {"recipes", "tags", "nutri_facts"}

        for field_name in api_model_fields:
            api_value = getattr(complex_api_meal, field_name)

            if field_name == "recipes":
                known_nested_objects.remove("recipes")
                # Recipes should be converted to list of kwargs
                assert isinstance(
                    kwargs[field_name], list
                ), f"recipes should be list in ORM kwargs"
                assert len(kwargs[field_name]) == len(
                    api_value
                ), f"recipes count should match"

                # Each recipe should be converted to dict/kwargs format
                for i, recipe_kwargs in enumerate(kwargs[field_name]):
                    assert isinstance(
                        recipe_kwargs, dict
                    ), f"recipe[{i}] should be dict in ORM kwargs"
                    # Basic structure check - should have key fields
                    assert "id" in recipe_kwargs, f"recipe[{i}] should have 'id' field"
                    assert (
                        "name" in recipe_kwargs
                    ), f"recipe[{i}] should have 'name' field"

            elif field_name == "tags":
                known_nested_objects.remove("tags")
                # Tags should be converted from frozenset to list of kwargs
                assert isinstance(
                    kwargs[field_name], list
                ), f"tags should be list in ORM kwargs"
                assert len(kwargs[field_name]) == len(
                    api_value
                ), f"tags count should match"

                # Each tag should be converted to dict/kwargs format
                for i, tag_kwargs in enumerate(kwargs[field_name]):
                    assert isinstance(
                        tag_kwargs, dict
                    ), f"tag[{i}] should be dict in ORM kwargs"
                    # Basic structure check - should have key fields
                    assert "key" in tag_kwargs, f"tag[{i}] should have 'key' field"
                    assert "value" in tag_kwargs, f"tag[{i}] should have 'value' field"

            elif field_name == "nutri_facts":
                known_nested_objects.remove("nutri_facts")
                # nutri_facts should be converted to ORM model instance
                if api_value is not None:
                    from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
                        NutriFactsSaModel,
                    )

                    assert isinstance(
                        kwargs[field_name], NutriFactsSaModel
                    ), f"nutri_facts should be NutriFactsSaModel in ORM kwargs"

                    # Verify that nutritional values are properly converted
                    orm_nutri_facts = kwargs[field_name]
                    for nutri_field in ApiNutriFacts.model_fields.keys():
                        api_nutri_value = getattr(api_value, nutri_field)
                        orm_nutri_value = getattr(orm_nutri_facts, nutri_field, None)
                        if api_nutri_value is not None:
                            assert (
                                orm_nutri_value == api_nutri_value.value
                            ), f"nutri_facts.{nutri_field} should be extracted from ApiNutriValue"
                else:
                    assert (
                        kwargs[field_name] is None
                    ), f"nutri_facts should be None in ORM kwargs when API value is None"

        # Ensure we tested all known nested objects
        assert (
            len(known_nested_objects) == 0
        ), f"All nested objects should be tested, but these were missed: {known_nested_objects}"

    def test_to_orm_kwargs_nutrition_facts_conversion(self, complex_api_meal):
        """Test to_orm_kwargs handles nutrition facts conversion."""
        kwargs = complex_api_meal.to_orm_kwargs()

        if complex_api_meal.nutri_facts:
            from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
                NutriFactsSaModel,
            )

            assert isinstance(kwargs["nutri_facts"], NutriFactsSaModel)
        else:
            assert kwargs["nutri_facts"] is None

    def test_to_orm_kwargs_computed_properties_conversion(self, complex_api_meal):
        """Test to_orm_kwargs includes computed properties."""
        kwargs = complex_api_meal.to_orm_kwargs()

        # Get all ApiMeal model fields
        api_model_fields = ApiMeal.model_fields.keys()

        # Define known computed properties based on domain analysis
        known_computed_properties = {
            "nutri_facts",
            "weight_in_grams",
            "calorie_density",
            "carbo_percentage",
            "protein_percentage",
            "total_fat_percentage",
        }

        for field_name in api_model_fields:
            api_value = getattr(complex_api_meal, field_name)

            if field_name in known_computed_properties:
                known_computed_properties.remove(field_name)

                # Computed properties should be included in ORM kwargs
                assert (
                    field_name in kwargs
                ), f"Computed property '{field_name}' should be in ORM kwargs"

                orm_value = kwargs[field_name]

                # Special handling for nutri_facts
                if field_name == "nutri_facts":
                    if api_value is not None:
                        from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
                            NutriFactsSaModel,
                        )

                        assert isinstance(
                            orm_value, NutriFactsSaModel
                        ), f"nutri_facts should be converted to NutriFactsSaModel"
                    else:
                        assert (
                            orm_value is None
                        ), f"nutri_facts should be None when API value is None"

                # Special handling for float computed properties
                elif field_name in [
                    "weight_in_grams",
                    "calorie_density",
                    "carbo_percentage",
                    "protein_percentage",
                    "total_fat_percentage",
                ]:
                    if api_value is not None:
                        assert (
                            abs(api_value - orm_value) < 0.001
                        ), f"Computed property '{field_name}' mismatch: API={api_value}, ORM={orm_value}"
                    else:
                        assert (
                            orm_value is None
                        ), f"Computed property '{field_name}' should be None when API value is None"

                else:
                    # Direct comparison for other computed properties
                    assert (
                        api_value == orm_value
                    ), f"Computed property '{field_name}' mismatch: API={api_value}, ORM={orm_value}"

        # Ensure we tested all known computed properties
        assert (
            len(known_computed_properties) == 0
        ), f"All computed properties should be tested, but these were missed: {known_computed_properties}"


class TestApiMealRoundTrip:
    """
    Test suite for round-trip conversion validation tests.
    """

    # =============================================================================
    # ROUND-TRIP CONVERSION VALIDATION TESTS
    # =============================================================================

    def test_domain_to_api_to_domain_round_trip(self, domain_meal):
        """Test complete domain → API → domain round-trip preserves data integrity."""
        # Domain → API
        api_meal = ApiMeal.from_domain(domain_meal)

        # API → Domain
        recovered_domain = api_meal.to_domain()

        # Use Meal's __eq__ method for comprehensive comparison
        assert (
            recovered_domain == domain_meal
        ), "Domain → API → Domain round-trip failed"

    def test_api_to_domain_to_api_round_trip(self, complex_api_meal):
        """Test API → Domain → API conversion preserves essential data while correcting computed properties."""

        # Store original values for comparison
        original_name = complex_api_meal.name
        original_id = complex_api_meal.id
        original_author_id = complex_api_meal.author_id
        original_recipes_count = len(complex_api_meal.recipes)
        original_tags_count = len(complex_api_meal.tags)

        # Calculate expected computed values from recipes
        expected_calories = sum(
            recipe.nutri_facts.calories.value if recipe.nutri_facts else 0
            for recipe in complex_api_meal.recipes
        )
        expected_weight = sum(
            recipe.weight_in_grams if recipe.weight_in_grams else 0
            for recipe in complex_api_meal.recipes
        )

        # Convert API → Domain → API
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)

        # Essential data should be preserved
        assert recovered_api.name == original_name
        assert recovered_api.id == original_id
        assert recovered_api.author_id == original_author_id
        assert recovered_api.recipes is not None
        assert recovered_api.tags is not None
        assert len(recovered_api.recipes) == original_recipes_count
        assert len(recovered_api.tags) == original_tags_count

        # Computed properties should be correctly calculated by domain, not necessarily equal to original
        if recovered_api.nutri_facts and expected_calories > 0:
            assert (
                abs(recovered_api.nutri_facts.calories.value - expected_calories) < 0.1
            )
            assert recovered_api.nutri_facts.protein.value > 0
            assert recovered_api.nutri_facts.carbohydrate.value > 0

        if expected_weight > 0:
            assert recovered_api.weight_in_grams == expected_weight

        # Verify computed properties were recalculated correctly by domain
        # Note: Calorie density calculation is also corrected by domain but skipping detailed check here

    def test_orm_to_api_to_orm_round_trip(self, real_orm_meal):
        """Test ORM → API → ORM round-trip preserves data integrity."""
        # ORM → API
        api_meal = ApiMeal.from_orm_model(real_orm_meal)

        # API → ORM kwargs
        orm_kwargs = api_meal.to_orm_kwargs()

        # Get all ApiMeal model fields to test round-trip comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define fields to exclude from round-trip test (complex nested objects)
        excluded_fields = {"recipes", "tags", "nutri_facts"}

        for field_name in api_model_fields:
            if field_name in excluded_fields:
                continue

            # Check if this field exists in the original ORM model
            if not hasattr(real_orm_meal, field_name):
                continue

            # Get values from both API and ORM kwargs
            original_orm_value = getattr(real_orm_meal, field_name)
            round_trip_orm_value = orm_kwargs.get(field_name)

            # Round-trip should preserve scalar field data integrity
            if (
                isinstance(original_orm_value, (str, int, float, bool))
                or original_orm_value is None
            ):
                assert (
                    original_orm_value == round_trip_orm_value
                ), f"Round-trip field '{field_name}' mismatch: Original({original_orm_value}) != RoundTrip({round_trip_orm_value})"
            elif hasattr(original_orm_value, "value"):  # Enum-like objects
                assert (
                    original_orm_value.value == round_trip_orm_value
                ), f"Round-trip enum field '{field_name}' mismatch: Original({original_orm_value.value}) != RoundTrip({round_trip_orm_value})"
            else:
                # For other types, ensure they're present in round-trip kwargs
                assert (
                    field_name in orm_kwargs
                ), f"Field '{field_name}' should be present in round-trip ORM kwargs"

    def test_complete_four_layer_round_trip(self, simple_api_meal):
        """Test complete four-layer conversion cycle preserves data integrity."""
        # Start with API object
        original_api = simple_api_meal

        # API → Domain
        domain_meal = original_api.to_domain()
        assert (
            domain_meal.nutri_facts.saturated_fat.value
            == original_api.nutri_facts.saturated_fat.value
        )

        # Domain → API
        api_from_domain = ApiMeal.from_domain(domain_meal)

        # Use comprehensive API equality for the API comparison
        assert (
            api_from_domain == original_api
        ), "Four-layer round-trip should preserve API data"

        # API → ORM kwargs - test comprehensively with excluded fields
        orm_kwargs = api_from_domain.to_orm_kwargs()

        # Get all ApiMeal model fields to test four-layer round-trip comprehensively
        api_model_fields = ApiMeal.model_fields.keys()

        # Define fields to exclude from four-layer round-trip test (complex nested objects)
        excluded_fields = {"recipes", "tags", "nutri_facts"}

        for field_name in api_model_fields:
            if field_name in excluded_fields:
                continue

            # Get values from both original API and final ORM kwargs
            original_api_value = getattr(original_api, field_name)
            final_orm_value = orm_kwargs.get(field_name)

            # Four-layer round-trip should preserve scalar field data
            if (
                isinstance(original_api_value, (str, int, float, bool))
                or original_api_value is None
            ):
                assert (
                    original_api_value == final_orm_value
                ), f"Four-layer round-trip field '{field_name}' mismatch: Original({original_api_value}) != Final({final_orm_value})"
            elif hasattr(original_api_value, "value"):  # Enum-like objects
                assert (
                    original_api_value.value == final_orm_value
                ), f"Four-layer round-trip enum field '{field_name}' mismatch: Original({original_api_value.value}) != Final({final_orm_value})"
            else:
                # For other types, ensure they're present in final kwargs
                assert (
                    field_name in orm_kwargs
                ), f"Field '{field_name}' should be present in final ORM kwargs"

    @pytest.mark.parametrize(
        "case_name",
        [
            "empty_recipes",
            "max_recipes",
            "minimal",
            "vegetarian",
            "high_protein",
            "quick",
            "holiday",
            "family",
        ],
    )
    def test_round_trip_with_edge_cases(self, edge_case_meals, case_name):
        """Test round-trip conversion with edge case meals."""
        api_meal = edge_case_meals[case_name]

        # API → Domain → API
        domain_meal = api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)

        # Use comprehensive API equality comparison instead of individual assertions
        # This automatically covers all fields including edge cases
        assert (
            recovered_api == api_meal
        ), f"Round-trip failed for edge case: {case_name}"

    def test_round_trip_preserves_computed_properties(self, complex_api_meal):
        """Test that round-trip conversions preserve computed properties."""
        # Round-trip conversion
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)

        # Use comprehensive API equality - this automatically verifies all computed properties
        assert (
            recovered_api == complex_api_meal
        ), "Round-trip should preserve all computed properties"

    def test_round_trip_with_nested_nutrition_facts(self, complex_api_meal):
        """Test round-trip conversion with complex nutrition facts."""
        if complex_api_meal.nutri_facts:
            # Round-trip conversion
            domain_meal = complex_api_meal.to_domain()
            recovered_api = ApiMeal.from_domain(domain_meal)

            # Use comprehensive API equality - this automatically verifies nutrition facts
            assert (
                recovered_api == complex_api_meal
            ), "Round-trip should preserve nutrition facts"

    def test_round_trip_with_complex_recipes(self, complex_api_meal):
        """Test round-trip conversion with complex recipe collections."""
        # Round-trip conversion
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)

        # Use comprehensive API equality - this automatically verifies recipe collections
        assert (
            recovered_api == complex_api_meal
        ), "Round-trip should preserve recipe collections"

    def test_round_trip_with_complex_tags(self, complex_api_meal):
        """Test round-trip conversion with complex tag collections."""
        # Round-trip conversion
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)

        # Use comprehensive API equality - this automatically verifies tag collections
        assert (
            recovered_api == complex_api_meal
        ), "Round-trip should preserve tag collections"


class TestApiMealComputedProperties:
    """
    Test suite for computed properties functionality.

    These tests verify that computed properties (weight_in_grams, calorie_density,
    nutri_facts, etc.) are correctly calculated in the domain and that incorrect
    values in ApiMeal instances get corrected through round-trip conversions.
    """

    # =============================================================================
    # COMPUTED PROPERTIES TESTS
    # =============================================================================

    def test_computed_properties_correction_round_trip(self):
        """Test that incorrect computed properties are corrected during round-trip conversion."""

        # Create a meal with deliberately incorrect computed properties
        original_api_meal = create_api_meal_with_incorrect_computed_properties()

        # Store original (incorrect) values for comparison
        original_calories = (
            original_api_meal.nutri_facts.calories.value
            if original_api_meal.nutri_facts
            else 0
        )
        original_weight = original_api_meal.weight_in_grams
        original_calorie_density = original_api_meal.calorie_density

        # Calculate expected correct values from recipes
        assert original_api_meal.recipes is not None
        expected_calories = sum(
            recipe.nutri_facts.calories.value if recipe.nutri_facts else 0
            for recipe in original_api_meal.recipes
        )
        expected_protein = sum(
            recipe.nutri_facts.protein.value if recipe.nutri_facts else 0
            for recipe in original_api_meal.recipes
        )
        expected_carbs = sum(
            recipe.nutri_facts.carbohydrate.value if recipe.nutri_facts else 0
            for recipe in original_api_meal.recipes
        )
        expected_fat = sum(
            recipe.nutri_facts.total_fat.value if recipe.nutri_facts else 0
            for recipe in original_api_meal.recipes
        )
        expected_weight = sum(
            recipe.weight_in_grams if recipe.weight_in_grams else 0
            for recipe in original_api_meal.recipes
        )

        # Convert API -> Domain (domain should ignore API computed properties and compute its own)
        domain_meal = original_api_meal.to_domain()

        # Domain should have computed correct values, ignoring API values
        assert domain_meal.nutri_facts is not None
        assert abs(domain_meal.nutri_facts.calories.value - expected_calories) < 0.1
        assert abs(domain_meal.nutri_facts.protein.value - expected_protein) < 0.1
        assert abs(domain_meal.nutri_facts.carbohydrate.value - expected_carbs) < 0.1
        assert abs(domain_meal.nutri_facts.total_fat.value - expected_fat) < 0.1
        assert domain_meal.weight_in_grams == expected_weight

        # Convert Domain -> API (should use domain's computed values)
        corrected_api_meal = ApiMeal.from_domain(domain_meal)

        # Corrected API meal should have domain's computed values, not original API values
        assert corrected_api_meal.nutri_facts is not None
        assert (
            abs(corrected_api_meal.nutri_facts.calories.value - expected_calories) < 0.1
        )
        assert (
            abs(corrected_api_meal.nutri_facts.protein.value - expected_protein) < 0.1
        )
        assert (
            abs(corrected_api_meal.nutri_facts.carbohydrate.value - expected_carbs)
            < 0.1
        )
        assert abs(corrected_api_meal.nutri_facts.total_fat.value - expected_fat) < 0.1
        assert corrected_api_meal.weight_in_grams == expected_weight

        # Verify the correction actually happened (values should be different if they were wrong initially)
        if expected_calories != original_calories:
            assert (
                abs(corrected_api_meal.nutri_facts.calories.value - original_calories)
                > 0.1
            )
        if expected_weight != original_weight:
            assert corrected_api_meal.weight_in_grams != original_weight

    def test_computed_properties_with_no_recipes(self):
        """Test computed properties when meal has no recipes."""
        empty_meal = create_api_meal_without_recipes()

        # Convert through domain to ensure properties are computed correctly
        domain_meal = empty_meal.to_domain()
        corrected_api_meal = ApiMeal.from_domain(domain_meal)

        # Should handle empty meal appropriately
        assert corrected_api_meal.recipes == []
        assert corrected_api_meal.weight_in_grams == 0
        assert corrected_api_meal.calorie_density is None
        assert corrected_api_meal.carbo_percentage is None
        assert corrected_api_meal.protein_percentage is None
        assert corrected_api_meal.total_fat_percentage is None
        assert corrected_api_meal.nutri_facts is None

    def test_computed_properties_with_multiple_recipes(self):
        """Test computed properties aggregation with multiple recipes."""
        multi_recipe_meal = create_api_meal_with_max_recipes()

        # Convert through domain to ensure properties are computed correctly
        domain_meal = multi_recipe_meal.to_domain()
        corrected_api_meal = ApiMeal.from_domain(domain_meal)

        # Should aggregate from multiple recipes
        assert corrected_api_meal.recipes is not None
        assert len(corrected_api_meal.recipes) >= 5

        if corrected_api_meal.nutri_facts:
            # Should have aggregated nutrition facts
            assert corrected_api_meal.nutri_facts.calories.value > 0
            assert corrected_api_meal.nutri_facts.protein.value > 0
            assert corrected_api_meal.nutri_facts.carbohydrate.value > 0

        if corrected_api_meal.weight_in_grams:
            # Should have aggregated weight
            assert corrected_api_meal.weight_in_grams > 0

    def test_computed_properties_correction_through_domain(self):
        """Test that computed properties are corrected through domain conversion."""

        # Create multiple meals with incorrect computed properties
        incorrect_meals = [
            create_api_meal_with_incorrect_computed_properties(),
            create_api_meal_with_max_recipes(),
            create_complex_api_meal(),
        ]

        for api_meal in incorrect_meals:
            # Calculate expected values from recipes
            assert api_meal.recipes is not None
            expected_calories = sum(
                recipe.nutri_facts.calories.value if recipe.nutri_facts else 0
                for recipe in api_meal.recipes
            )
            expected_weight = sum(
                recipe.weight_in_grams if recipe.weight_in_grams else 0
                for recipe in api_meal.recipes
            )

            # Convert API -> Domain -> API
            domain_meal = api_meal.to_domain()
            corrected_api_meal = ApiMeal.from_domain(domain_meal)

            # Should aggregate from multiple recipes
            assert corrected_api_meal.recipes is not None
            assert len(corrected_api_meal.recipes) >= 1

            if corrected_api_meal.nutri_facts and expected_calories > 0:
                # Should have correctly computed nutrition facts from recipes, not API values
                assert (
                    abs(
                        corrected_api_meal.nutri_facts.calories.value
                        - expected_calories
                    )
                    < 0.1
                )
                assert corrected_api_meal.nutri_facts.protein.value > 0
                assert corrected_api_meal.nutri_facts.carbohydrate.value > 0

            if expected_weight > 0:
                # Should have correctly computed weight from recipes, not API values
                assert corrected_api_meal.weight_in_grams == expected_weight

    def test_computed_nutrition_facts_aggregation(self):
        """Test that nutrition facts are correctly aggregated from recipes."""
        # Create a meal with known recipe nutrition facts
        api_meal_with_incorrect = create_api_meal_with_incorrect_computed_properties()

        # Convert through domain to get correct aggregation
        domain_meal = api_meal_with_incorrect.to_domain()
        corrected_api_meal = ApiMeal.from_domain(domain_meal)

        if corrected_api_meal.nutri_facts and corrected_api_meal.recipes:
            # Calculate expected totals from recipes
            expected_calories = sum(
                recipe.nutri_facts.calories.value if recipe.nutri_facts else 0
                for recipe in corrected_api_meal.recipes
            )
            expected_protein = sum(
                recipe.nutri_facts.protein.value if recipe.nutri_facts else 0
                for recipe in corrected_api_meal.recipes
            )
            expected_carbs = sum(
                recipe.nutri_facts.carbohydrate.value if recipe.nutri_facts else 0
                for recipe in corrected_api_meal.recipes
            )
            expected_fat = sum(
                recipe.nutri_facts.total_fat.value if recipe.nutri_facts else 0
                for recipe in corrected_api_meal.recipes
            )

            # Verify aggregated values match expectations (within reasonable tolerance)
            if expected_calories > 0:
                assert (
                    corrected_api_meal.nutri_facts.calories is not None
                    and abs(
                        corrected_api_meal.nutri_facts.calories.value
                        - expected_calories
                    )
                    < 10
                )
            if expected_protein > 0:
                assert (
                    corrected_api_meal.nutri_facts.protein is not None
                    and abs(
                        corrected_api_meal.nutri_facts.protein.value - expected_protein
                    )
                    < 5
                )
            if expected_carbs > 0:
                assert (
                    corrected_api_meal.nutri_facts.carbohydrate is not None
                    and abs(
                        corrected_api_meal.nutri_facts.carbohydrate.value
                        - expected_carbs
                    )
                    < 5
                )
            if expected_fat > 0:
                assert (
                    corrected_api_meal.nutri_facts.total_fat is not None
                    and abs(
                        corrected_api_meal.nutri_facts.total_fat.value - expected_fat
                    )
                    < 5
                )

    def test_computed_weight_aggregation(self):
        """Test that weight is correctly aggregated from recipes."""
        # Create a meal with known recipe weights
        api_meal_with_incorrect = create_api_meal_with_incorrect_computed_properties()

        # Convert through domain to get correct aggregation
        domain_meal = api_meal_with_incorrect.to_domain()
        corrected_api_meal = ApiMeal.from_domain(domain_meal)

        if corrected_api_meal.recipes:
            # Calculate expected weight from recipes
            expected_weight = sum(
                recipe.weight_in_grams or 0 for recipe in corrected_api_meal.recipes
            )

            # Verify aggregated weight matches expectations
            assert corrected_api_meal.weight_in_grams == expected_weight

    def test_computed_calorie_density_calculation(self):
        """Test that calorie density is correctly calculated."""
        # Create a meal with incorrect calorie density
        api_meal_with_incorrect = create_api_meal_with_incorrect_computed_properties()

        # Convert through domain to get correct calculation
        domain_meal = api_meal_with_incorrect.to_domain()
        corrected_api_meal = ApiMeal.from_domain(domain_meal)

        if (
            corrected_api_meal.nutri_facts
            and corrected_api_meal.weight_in_grams
            and corrected_api_meal.weight_in_grams > 0
            and corrected_api_meal.nutri_facts.calories is not None
        ):
            # Calculate expected calorie density
            expected_calorie_density = (
                corrected_api_meal.nutri_facts.calories.value
                / corrected_api_meal.weight_in_grams
            ) * 100

            # Verify calorie density matches expectations (within reasonable tolerance)
            if corrected_api_meal.calorie_density is not None:
                assert (
                    abs(corrected_api_meal.calorie_density - expected_calorie_density)
                    < 1.0
                )

    def test_computed_macro_percentages_calculation(self):
        """Test that macro percentages are correctly calculated."""
        # Create a meal with incorrect macro percentages
        api_meal_with_incorrect = create_api_meal_with_incorrect_computed_properties()

        # Convert through domain to get correct calculation
        domain_meal = api_meal_with_incorrect.to_domain()
        corrected_api_meal = ApiMeal.from_domain(domain_meal)

        if corrected_api_meal.nutri_facts:
            protein = corrected_api_meal.nutri_facts.protein
            carbs = corrected_api_meal.nutri_facts.carbohydrate
            fat = corrected_api_meal.nutri_facts.total_fat

            if protein is not None and carbs is not None and fat is not None:
                total_macros = protein.value + carbs.value + fat.value

                if total_macros > 0:
                    # Calculate expected percentages
                    expected_protein_percentage = (protein.value / total_macros) * 100
                    expected_carbo_percentage = (carbs.value / total_macros) * 100
                    expected_fat_percentage = (fat.value / total_macros) * 100

                    # Verify percentages match expectations (within reasonable tolerance)
                    if corrected_api_meal.protein_percentage is not None:
                        assert (
                            abs(
                                corrected_api_meal.protein_percentage
                                - expected_protein_percentage
                            )
                            < 1.0
                        )
                    if corrected_api_meal.carbo_percentage is not None:
                        assert (
                            abs(
                                corrected_api_meal.carbo_percentage
                                - expected_carbo_percentage
                            )
                            < 1.0
                        )
                    if corrected_api_meal.total_fat_percentage is not None:
                        assert (
                            abs(
                                corrected_api_meal.total_fat_percentage
                                - expected_fat_percentage
                            )
                            < 1.0
                        )

    def test_computed_properties_with_edge_cases(self, edge_case_meals):
        """Test computed properties with various edge cases."""
        # Test with empty recipes - convert through domain to ensure correct computation
        empty_meal = edge_case_meals["empty_recipes"]
        domain_meal = empty_meal.to_domain()
        corrected_empty_meal = ApiMeal.from_domain(domain_meal)

        assert corrected_empty_meal.weight_in_grams == 0
        assert corrected_empty_meal.calorie_density is None
        assert corrected_empty_meal.carbo_percentage is None
        assert corrected_empty_meal.protein_percentage is None
        assert corrected_empty_meal.total_fat_percentage is None

        # Test with max recipes - convert through domain to ensure correct computation
        max_meal = edge_case_meals["max_recipes"]
        domain_meal = max_meal.to_domain()
        corrected_max_meal = ApiMeal.from_domain(domain_meal)

        assert (
            corrected_max_meal.weight_in_grams is not None
            and corrected_max_meal.weight_in_grams >= 0
        )
        if corrected_max_meal.nutri_facts:
            assert (
                corrected_max_meal.nutri_facts.calories is not None
                and corrected_max_meal.nutri_facts.calories.value >= 0
            )
            assert (
                corrected_max_meal.nutri_facts.protein is not None
                and corrected_max_meal.nutri_facts.protein.value >= 0
            )
            assert (
                corrected_max_meal.nutri_facts.carbohydrate is not None
                and corrected_max_meal.nutri_facts.carbohydrate.value >= 0
            )
            assert (
                corrected_max_meal.nutri_facts.total_fat is not None
                and corrected_max_meal.nutri_facts.total_fat.value >= 0
            )

    def test_json_with_computed_properties(self, complex_api_meal):
        """Test JSON serialization includes computed properties."""
        json_str = complex_api_meal.model_dump_json()

        # Should include computed properties in JSON
        import json

        parsed = json.loads(json_str)
        assert "weight_in_grams" in parsed
        assert "calorie_density" in parsed
        assert "carbo_percentage" in parsed
        assert "protein_percentage" in parsed
        assert "total_fat_percentage" in parsed

    def test_json_with_computed_properties_round_trip(self, complex_api_meal):
        """Test JSON round-trip preserves computed properties."""
        # Serialize to JSON
        json_str = complex_api_meal.model_dump_json()

        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)

        # Use comprehensive API equality - this automatically verifies all properties including computed ones
        assert (
            restored_meal == complex_api_meal
        ), "JSON round-trip should preserve all meal data"

    def test_domain_computed_properties_override_api_values(self):
        """Test that domain computed properties override API values during conversion."""

        # Create meal with deliberately incorrect computed properties
        api_meal_with_incorrect = create_api_meal_with_incorrect_computed_properties()

        # Store original API values (which are incorrect)
        original_api_calories = (
            api_meal_with_incorrect.nutri_facts.calories.value
            if api_meal_with_incorrect.nutri_facts
            else 0
        )
        original_api_weight = api_meal_with_incorrect.weight_in_grams
        original_api_calorie_density = api_meal_with_incorrect.calorie_density

        # Calculate what the correct values should be based on recipes
        assert api_meal_with_incorrect.recipes is not None
        expected_calories = sum(
            recipe.nutri_facts.calories.value if recipe.nutri_facts else 0
            for recipe in api_meal_with_incorrect.recipes
        )
        expected_weight = sum(
            recipe.weight_in_grams if recipe.weight_in_grams else 0
            for recipe in api_meal_with_incorrect.recipes
        )
        expected_calorie_density = (
            (expected_calories / expected_weight) * 100 if expected_weight > 0 else None
        )

        # Convert to domain (should ignore API computed properties and compute its own)
        domain_meal = api_meal_with_incorrect.to_domain()

        # Domain should have computed correct values, not the API values
        assert domain_meal.nutri_facts is not None
        assert abs(domain_meal.nutri_facts.calories.value - expected_calories) < 0.1
        assert domain_meal.weight_in_grams == expected_weight

        if (
            expected_calorie_density is not None
            and domain_meal.calorie_density is not None
        ):
            assert abs(domain_meal.calorie_density - expected_calorie_density) < 0.1

        # Convert back to API (should preserve domain's computed values)
        final_api_meal = ApiMeal.from_domain(domain_meal)

        # Final API meal should have domain's computed values, not original API values
        assert final_api_meal.nutri_facts is not None
        assert abs(final_api_meal.nutri_facts.calories.value - expected_calories) < 0.1
        assert final_api_meal.weight_in_grams == expected_weight

        if (
            expected_calorie_density is not None
            and final_api_meal.calorie_density is not None
        ):
            assert abs(final_api_meal.calorie_density - expected_calorie_density) < 0.1

        # Verify that override actually happened (domain values should be different from original API if they were wrong)
        if (
            expected_calories > 0
            and original_api_calories is not None
            and abs(expected_calories - original_api_calories) > 0.1
        ):
            assert (
                abs(final_api_meal.nutri_facts.calories.value - original_api_calories)
                > 0.1
            ), "Domain should have overridden incorrect API calories"

        if expected_weight != original_api_weight:
            assert (
                final_api_meal.weight_in_grams != original_api_weight
            ), "Domain should have overridden incorrect API weight"
