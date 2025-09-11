from datetime import datetime

import pytest
from pydantic import ValidationError
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_api_recipe_with_concurrent_modifications,
    create_api_recipe_with_extreme_ratings,
    create_api_recipe_with_fractional_averages,
    create_api_recipe_with_future_timestamps,
    create_api_recipe_with_high_version,
    create_api_recipe_with_html_characters,
    create_api_recipe_with_invalid_timestamp_order,
    create_api_recipe_with_mismatched_computed_properties,
    create_api_recipe_with_negative_version,
    create_api_recipe_with_past_timestamps,
    create_api_recipe_with_same_timestamps,
    create_api_recipe_with_single_rating,
    create_api_recipe_with_special_characters,
    create_api_recipe_with_sql_injection,
    create_api_recipe_with_unicode_text,
    create_api_recipe_with_very_long_text,
    create_api_recipe_with_zero_version,
    create_complex_api_recipe,
    create_comprehensive_validation_test_cases_for_api_recipe,
    create_minimal_api_recipe,
    create_simple_api_recipe,
    create_vegetarian_api_recipe,
    validate_json_serialization_of_api_recipe,
    validate_orm_conversion_for_api_recipe,
    validate_round_trip_conversion_for_api_recipe,
)

"""
ApiRecipe Edge Cases Test Suite

Test classes for edge cases including computed properties, text/security, concurrency,
datetime edge cases, and comprehensive validation.
"""


class TestApiRecipeComputedPropertiesEdgeCases:
    """
    Test suite for computed properties edge cases.
    """

    def test_mismatched_computed_properties_correction(self):
        """Test that mismatched computed properties are corrected during round-trip."""
        mismatched_kwargs = create_api_recipe_with_mismatched_computed_properties()
        recipe = ApiRecipe(**mismatched_kwargs)

        # Round-trip should correct the averages
        domain_recipe = recipe.to_domain()
        corrected_api = ApiRecipe.from_domain(domain_recipe)

        # Verify correction
        assert recipe.ratings is not None
        expected_taste = sum(r.taste for r in recipe.ratings) / len(recipe.ratings)
        expected_convenience = sum(r.convenience for r in recipe.ratings) / len(
            recipe.ratings
        )

        assert corrected_api.average_taste_rating == expected_taste
        assert corrected_api.average_convenience_rating == expected_convenience

    def test_single_rating_computed_properties(self):
        """Test computed properties with single rating."""
        single_kwargs = create_api_recipe_with_single_rating()
        recipe = ApiRecipe(**single_kwargs)

        # With single rating, averages should equal that rating
        assert recipe.ratings is not None
        rating = list(recipe.ratings)[0]
        assert recipe.average_taste_rating == rating.taste
        assert recipe.average_convenience_rating == rating.convenience

    def test_extreme_ratings_computed_properties(self):
        """Test computed properties with extreme rating values."""
        extreme_kwargs = create_api_recipe_with_extreme_ratings()
        recipe = ApiRecipe(**extreme_kwargs)

        # Should handle extreme values correctly
        assert recipe.average_taste_rating == 2.5  # (0 + 5) / 2
        assert recipe.average_convenience_rating == 2.5  # (0 + 5) / 2

    def test_fractional_averages_computed_properties(self):
        """Test computed properties with fractional averages."""
        fractional_kwargs = create_api_recipe_with_fractional_averages()
        recipe = ApiRecipe(**fractional_kwargs)

        # Should handle fractional averages correctly
        assert recipe.average_taste_rating == 2.0  # (1 + 2 + 3) / 3
        assert recipe.average_convenience_rating == 2.0  # (1 + 2 + 3) / 3

    def test_computed_properties_round_trip_validation(self):
        """Test comprehensive computed properties validation using factory helper."""
        recipe = create_api_recipe_with_mismatched_computed_properties()
        api_recipe = ApiRecipe(**recipe)

        # Use the validation helper
        validation_result = validate_round_trip_conversion_for_api_recipe(api_recipe)

        assert validation_result[
            "api_to_domain_success"
        ], "API to domain conversion failed"
        assert validation_result[
            "domain_to_api_success"
        ], "Domain to API conversion failed"
        assert validation_result[
            "computed_properties_corrected"
        ], "Computed properties not corrected"

    @pytest.mark.parametrize(
        "scenario,factory_func",
        [
            ("mismatched", create_api_recipe_with_mismatched_computed_properties),
            ("single_rating", create_api_recipe_with_single_rating),
            ("extreme_ratings", create_api_recipe_with_extreme_ratings),
            ("fractional", create_api_recipe_with_fractional_averages),
        ],
    )
    def test_computed_properties_scenarios_parametrized(self, scenario, factory_func):
        """Test computed properties scenarios using parametrization."""
        kwargs = factory_func()
        recipe = ApiRecipe(**kwargs)

        # Basic validation
        assert isinstance(recipe, ApiRecipe)
        if recipe.ratings:
            assert recipe.average_taste_rating is not None
            assert recipe.average_convenience_rating is not None
        else:
            assert recipe.average_taste_rating is None
            assert recipe.average_convenience_rating is None


class TestApiRecipeDatetimeEdgeCases:
    """
    Test suite for datetime edge cases.
    """

    def test_future_timestamps_handling(self):
        """Test handling of future timestamps."""
        future_kwargs = create_api_recipe_with_future_timestamps()
        recipe = ApiRecipe(**future_kwargs)

        # Should handle future dates
        assert recipe.created_at is not None
        assert recipe.updated_at is not None
        assert recipe.created_at > datetime.now()
        assert recipe.updated_at > datetime.now()

        # Round-trip should preserve datetime values
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)

        assert recovered_api.created_at == recipe.created_at
        assert recovered_api.updated_at == recipe.updated_at

    def test_past_timestamps_handling(self):
        """Test handling of past timestamps."""
        past_kwargs = create_api_recipe_with_past_timestamps()
        recipe = ApiRecipe(**past_kwargs)

        # Should handle old dates
        assert recipe.created_at is not None
        assert recipe.updated_at is not None
        assert recipe.created_at < datetime.now()
        assert recipe.updated_at < datetime.now()

        # Round-trip should preserve datetime values
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)

        assert recovered_api.created_at == recipe.created_at
        assert recovered_api.updated_at == recipe.updated_at

    def test_invalid_timestamp_order_handling(self):
        """Test handling of invalid timestamp order (updated_at before created_at)."""
        invalid_kwargs = create_api_recipe_with_invalid_timestamp_order()
        recipe = ApiRecipe(**invalid_kwargs)

        # Should accept invalid order (validation might be at domain layer)
        assert isinstance(recipe, ApiRecipe)
        assert recipe.created_at is not None
        assert recipe.updated_at is not None
        assert recipe.updated_at < recipe.created_at

    def test_same_timestamps_handling(self):
        """Test handling of identical timestamps."""
        same_kwargs = create_api_recipe_with_same_timestamps()
        recipe = ApiRecipe(**same_kwargs)

        # Should handle identical timestamps
        assert recipe.created_at == recipe.updated_at

    @pytest.mark.parametrize(
        "scenario,factory_func",
        [
            ("future", create_api_recipe_with_future_timestamps),
            ("past", create_api_recipe_with_past_timestamps),
            ("invalid_order", create_api_recipe_with_invalid_timestamp_order),
            ("same", create_api_recipe_with_same_timestamps),
        ],
    )
    def test_datetime_scenarios_parametrized(self, scenario, factory_func):
        """Test datetime scenarios using parametrization."""
        kwargs = factory_func()
        recipe = ApiRecipe(**kwargs)

        assert isinstance(recipe, ApiRecipe)
        assert isinstance(recipe.created_at, datetime)
        assert isinstance(recipe.updated_at, datetime)


class TestApiRecipeTextAndSecurityEdgeCases:
    """
    Test suite for text and security edge cases.
    """

    def test_unicode_text_handling(self):
        """Test handling of unicode characters."""
        unicode_kwargs = create_api_recipe_with_unicode_text()
        recipe = ApiRecipe(**unicode_kwargs)

        # Should handle unicode characters properly
        assert "Pâté" in recipe.name
        assert "Échalotes" in recipe.name
        assert "🍷" in recipe.name
        assert recipe.description and "Délicieux" in recipe.description
        assert recipe.description and "🇫🇷" in recipe.description

    def test_special_characters_handling(self):
        """Test handling of special characters."""
        special_kwargs = create_api_recipe_with_special_characters()
        recipe = ApiRecipe(**special_kwargs)

        # Should handle special characters
        assert "!@#$%^&*()" in recipe.name
        assert recipe.description and "<>&\"'{}[]|\\" in recipe.description

    def test_html_characters_handling(self):
        """Test handling of HTML characters (XSS protection)."""
        html_kwargs = create_api_recipe_with_html_characters()
        recipe = ApiRecipe(**html_kwargs)

        # Should sanitize HTML characters (script tags should be removed)
        assert "<script>" not in recipe.name
        assert "HTML" in recipe.name  # The safe part should remain
        assert (
            recipe.description and "<b>Bold</b>" in recipe.description
        )  # Basic HTML tags may be preserved

    def test_sql_injection_handling(self):
        """Test handling of SQL injection attempts."""
        sql_kwargs = create_api_recipe_with_sql_injection()
        recipe = ApiRecipe(**sql_kwargs)

        # Should sanitize SQL injection strings (dangerous parts should be removed)
        assert "DROP TABLE" not in recipe.name
        assert "Recipe" in recipe.name  # The safe part should remain
        assert recipe.description and "OR '1'='1" not in recipe.description

    def test_very_long_text_handling(self):
        """Test handling of very long text."""
        long_kwargs = create_api_recipe_with_very_long_text()

        # Should fail validation due to length limits
        with pytest.raises(ValidationError) as exc_info:
            ApiRecipe(**long_kwargs)

        # Verify it's failing on the expected fields
        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        expected_fields = {"name", "description", "utensils", "notes"}
        assert expected_fields.issubset(
            error_fields
        ), f"Expected errors on {expected_fields}, got errors on {error_fields}"

    def test_text_round_trip_preservation(self):
        """Test that special text is preserved in round-trip conversions."""
        unicode_kwargs = create_api_recipe_with_unicode_text()
        recipe = ApiRecipe(**unicode_kwargs)

        # Round-trip through domain
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)

        # Unicode should be preserved
        assert recovered_api.name == recipe.name
        assert recovered_api.description == recipe.description

    @pytest.mark.parametrize(
        "scenario,factory_func",
        [
            ("unicode", create_api_recipe_with_unicode_text),
            ("special_chars", create_api_recipe_with_special_characters),
            ("html", create_api_recipe_with_html_characters),
            ("sql_injection", create_api_recipe_with_sql_injection),
            ("long_text", create_api_recipe_with_very_long_text),
        ],
    )
    def test_text_scenarios_parametrized(self, scenario, factory_func):
        """Test text scenarios using parametrization."""
        kwargs = factory_func()

        if scenario == "long_text":
            # Long text should fail validation
            with pytest.raises(ValidationError):
                ApiRecipe(**kwargs)
        else:
            recipe = ApiRecipe(**kwargs)
            assert isinstance(recipe, ApiRecipe)
            assert isinstance(recipe.name, str)
            assert isinstance(recipe.instructions, str)


class TestApiRecipeConcurrencyEdgeCases:
    """
    Test suite for concurrency and version edge cases.
    """

    def test_concurrent_modifications_handling(self):
        """Test handling of concurrent modification scenarios."""
        concurrent_kwargs = create_api_recipe_with_concurrent_modifications()
        recipe = ApiRecipe(**concurrent_kwargs)

        # Should handle concurrent modification data
        assert recipe.version == 1
        assert isinstance(recipe.created_at, datetime)
        assert isinstance(recipe.updated_at, datetime)

    def test_high_version_handling(self):
        """Test handling of high version numbers."""
        high_version_kwargs = create_api_recipe_with_high_version()
        recipe = ApiRecipe(**high_version_kwargs)

        # Should handle high version numbers
        assert recipe.version == 99999

    def test_zero_version_handling(self):
        """Test handling of zero version."""
        zero_version_kwargs = create_api_recipe_with_zero_version()
        with pytest.raises(ValidationError):
            ApiRecipe(**zero_version_kwargs)

    def test_negative_version_handling(self):
        """Test handling of negative version."""
        negative_version_kwargs = create_api_recipe_with_negative_version()
        with pytest.raises(ValidationError):
            ApiRecipe(**negative_version_kwargs)

    def test_version_round_trip_preservation(self):
        """Test that version values are preserved in round-trip conversions."""
        high_version_kwargs = create_api_recipe_with_high_version()
        recipe = ApiRecipe(**high_version_kwargs)

        # Round-trip through domain
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)

        # Version should be preserved
        assert recovered_api.version == recipe.version

    @pytest.mark.parametrize(
        "scenario,factory_func",
        [
            ("concurrent", create_api_recipe_with_concurrent_modifications),
            ("high_version", create_api_recipe_with_high_version),
            ("zero_version", create_api_recipe_with_zero_version),
            ("negative_version", create_api_recipe_with_negative_version),
        ],
    )
    def test_version_scenarios_parametrized(self, scenario, factory_func):
        """Test version scenarios using parametrization."""
        kwargs = factory_func()
        if scenario in ["zero_version", "negative_version"]:
            with pytest.raises(ValidationError):
                ApiRecipe(**kwargs)
        else:
            recipe = ApiRecipe(**kwargs)

            assert isinstance(recipe, ApiRecipe)
            assert isinstance(recipe.version, int)


class TestApiRecipeComprehensiveValidation:
    """
    Test suite for comprehensive validation using factory helpers.
    """

    @pytest.mark.parametrize(
        "case", create_comprehensive_validation_test_cases_for_api_recipe()
    )
    def test_comprehensive_validation_test_cases(self, case):
        """Test all comprehensive validation test cases."""
        factory_func = case["factory"]
        expected_error = case["expected_error"]

        try:
            kwargs = factory_func()
            recipe = ApiRecipe(**kwargs)

            if expected_error == "domain_rule":
                # Should fail when converting to domain
                with pytest.raises(Exception):
                    recipe.to_domain()
            elif expected_error == "validation":
                # Should have failed during creation but didn't
                pytest.fail(
                    f"Expected validation error but creation succeeded for {factory_func.__name__}"
                )
            elif expected_error is not None:
                # Should have failed during creation but didn't
                pytest.fail(
                    f"Expected error '{expected_error}' but creation succeeded for {factory_func.__name__}"
                )
            else:
                # Should succeed
                assert isinstance(recipe, ApiRecipe)

        except ValidationError as e:
            # Handle the case where the factory is expected to produce validation errors
            if expected_error == "validation":
                # This is expected
                assert True
            elif expected_error is None:
                pytest.fail(
                    f"Unexpected validation error for {factory_func.__name__}: {e}"
                )
            # Expected error occurred
            assert True

    @pytest.mark.parametrize(
        "recipe_factory",
        [
            create_simple_api_recipe,
            create_complex_api_recipe,
            create_vegetarian_api_recipe,
            create_api_recipe_with_mismatched_computed_properties,
        ],
    )
    def test_round_trip_conversion_validation(self, recipe_factory):
        """Test comprehensive round-trip conversion validation."""
        recipe = recipe_factory()
        validation_result = validate_round_trip_conversion_for_api_recipe(recipe)

        assert validation_result[
            "api_to_domain_success"
        ], f"API to domain conversion failed: {validation_result['errors']}"
        assert validation_result[
            "domain_to_api_success"
        ], f"Domain to API conversion failed: {validation_result['errors']}"
        assert validation_result[
            "data_integrity_maintained"
        ], f"Data integrity not maintained: {validation_result['warnings']}"

    @pytest.mark.parametrize(
        "recipe_factory",
        [
            create_simple_api_recipe,
            create_complex_api_recipe,
            create_minimal_api_recipe,
        ],
    )
    def test_orm_conversion_validation(self, recipe_factory):
        """Test comprehensive ORM conversion validation."""
        recipe = recipe_factory()
        validation_result = validate_orm_conversion_for_api_recipe(recipe)

        assert validation_result[
            "api_to_orm_kwargs_success"
        ], f"API to ORM kwargs failed: {validation_result['errors']}"
        assert validation_result[
            "orm_kwargs_valid"
        ], f"ORM kwargs invalid: {validation_result['warnings']}"

    @pytest.mark.parametrize(
        "recipe_factory,description",
        [
            (create_simple_api_recipe, "simple recipe"),
            (create_complex_api_recipe, "complex recipe"),
            (
                lambda: ApiRecipe(**create_api_recipe_with_unicode_text()),
                "unicode text recipe",
            ),
        ],
    )
    def test_json_serialization_validation(self, recipe_factory, description):
        """Test comprehensive JSON serialization validation."""
        recipe = recipe_factory()
        validation_result = validate_json_serialization_of_api_recipe(recipe)

        assert validation_result[
            "api_to_json_success"
        ], f"API to JSON failed for {description}: {validation_result['errors']}"
        assert validation_result[
            "json_to_api_success"
        ], f"JSON to API failed for {description}: {validation_result['errors']}"
        assert validation_result[
            "json_valid"
        ], f"JSON invalid for {description}: {validation_result['errors']}"
        assert validation_result[
            "round_trip_success"
        ], f"Round-trip failed for {description}: {validation_result['warnings']}"
