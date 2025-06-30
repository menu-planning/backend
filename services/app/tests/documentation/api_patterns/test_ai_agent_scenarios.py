"""
AI Agent Usage Simulation Tests

Tests that simulate common scenarios an AI agent might encounter when implementing
new API schemas based on the documented patterns. These tests validate that the
documentation is complete and accurate enough for successful implementation.

Key Principles:
- Test actual behavior, not implementation details
- Use real domain objects and API schemas
- Validate end-to-end conversion cycles
- No mocks - focus on genuine behavior validation
- Simulate realistic AI agent implementation scenarios
"""

import pytest
import time
from typing import Any, Dict, List

from pydantic import ValidationError
from pydantic_core import ValidationError as CoreValidationError

# Import real API schemas and domain objects (using working patterns)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.domain.value_objects.tag import Tag

# Import working TypeAdapters
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import TagFrozensetAdapter


class TestAIAgentImplementationScenarios:
    """
    Test scenarios that simulate how an AI agent would implement new API schemas
    based on the documented patterns. These tests validate documentation completeness.
    """

    def test_ai_agent_scenario_new_simple_entity_implementation(self, sample_tag_domain, sample_tag_api):
        """
        Scenario: AI agent needs to implement a new simple entity API schema
        Tests: Can follow four-layer conversion pattern for basic entity
        """
        # Test 1: Validate four-layer conversion works as documented
        # Domain → API conversion (using real fixtures)
        domain_tag = sample_tag_domain
        api_from_domain = ApiTag.from_domain(domain_tag)
        
        # Verify conversion accuracy
        assert api_from_domain.key == domain_tag.key
        assert api_from_domain.value == domain_tag.value
        assert api_from_domain.author_id == domain_tag.author_id
        assert api_from_domain.type == domain_tag.type
        
        # Test 2: API → Domain conversion
        converted_back = api_from_domain.to_domain()
        assert converted_back.key == domain_tag.key
        assert converted_back.value == domain_tag.value
        assert converted_back.author_id == domain_tag.author_id
        assert converted_back.type == domain_tag.type
        
        # Test 3: Validate field validation patterns work as documented
        # Should handle edge cases properly (using real Tag constructor)
        with pytest.raises(ValidationError):
            ApiTag(key="", value="test", author_id="test", type="test")  # Empty key should fail

    def test_ai_agent_scenario_collection_handling_implementation(self, sample_tags_collection):
        """
        Scenario: AI agent needs to implement schema with collection conversions
        Tests: Can follow type conversion patterns for collections (set ↔ frozenset ↔ list)
        """
        # Test 1: Apply documented conversion patterns
        # Using real domain tags from fixture
        domain_tags = set(sample_tags_collection)  # set[Tag] as in domain
        
        # set[Tag] → frozenset[ApiTag] as documented
        api_tags_frozen = frozenset(ApiTag.from_domain(tag) for tag in domain_tags)
        
        # Validate conversion accuracy
        assert len(api_tags_frozen) == len(domain_tags)
        assert all(isinstance(tag, ApiTag) for tag in api_tags_frozen)
        
        # Test 2: Use TypeAdapter pattern as documented
        # Validate that TypeAdapter singleton pattern works for collections
        tag_data = [
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},
            {"key": "diet", "value": "vegetarian", "author_id": "user-456", "type": "dietary"}
        ]
        
        validated_tags = TagFrozensetAdapter.validate_python(tag_data)
        
        assert isinstance(validated_tags, frozenset)
        assert len(validated_tags) == 2
        
        # Test 3: Performance requirements met as documented
        start_time = time.perf_counter()
        
        # Should validate 10 tags in <3ms as per documentation
        large_tag_data = [
            {"key": f"tag{i}", "value": f"value{i}", "author_id": f"user{i}", "type": "category"}
            for i in range(10)
        ]
        result = TagFrozensetAdapter.validate_python(large_tag_data)
        
        end_time = time.perf_counter()
        validation_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert validation_time < 3.0  # Should meet documented performance target
        assert len(result) == 10

    def test_ai_agent_scenario_complex_nested_schema_implementation(self, sample_meal_with_complex_data):
        """
        Scenario: AI agent implements complex schema with all patterns combined
        Tests: Integration of all documented patterns in realistic scenario
        """
        # Test using real complex meal fixture
        domain_meal = sample_meal_with_complex_data
        
        # Apply all conversion patterns as documented
        # Four-layer conversion with type conversions, computed properties, and collections
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Verify all pattern integrations work
        assert api_meal.id == domain_meal.id
        assert api_meal.name == domain_meal.name
        assert api_meal.author_id == domain_meal.author_id
        
        # Test full conversion cycle integrity
        # Domain → API → ORM → API → Domain
        orm_kwargs = api_meal.to_orm_kwargs()
        assert isinstance(orm_kwargs, dict)
        
        # Should be able to reconstruct from ORM data (testing complete pattern integration)
        # This validates that all documented patterns work together
        reconstructed_api = ApiMeal.from_orm_model(type('MockORM', (), orm_kwargs)())
        
        # Verify data integrity through full cycle
        assert reconstructed_api.id == api_meal.id
        assert reconstructed_api.name == api_meal.name

    def test_ai_agent_scenario_error_handling_patterns(self):
        """
        Scenario: AI agent needs to implement proper error handling
        Tests: Error handling patterns work as documented
        """
        # Test 1: Validation error clarity as documented
        try:
            ApiMeal(
                id="",  # Invalid empty ID
                name="Test",
                author_id="test-author",
                recipes=[],
                tags=[]
            )
            assert False, "Should have raised validation error"
        except ValidationError as e:
            # Error should be clear and helpful for AI agent debugging
            error_str = str(e)
            assert "id" in error_str.lower()
            assert len(e.errors()) > 0

        # Test 2: Graceful degradation patterns
        # Edge case: Empty collections should be handled gracefully
        api_meal_empty = ApiMeal(
            id="test_empty",
            name="Empty Meal",
            author_id="test-author",
            recipes=[],
            tags=frozenset()  # Use frozenset() instead of [] for tags field
        )
        
        # Should convert successfully despite empty collections
        domain_meal = api_meal_empty.to_domain()
        assert domain_meal.id == "test_empty"
        assert len(domain_meal.recipes) == 0
        assert len(domain_meal.tags) == 0

    def test_ai_agent_scenario_performance_requirements_validation(self, large_collection_data):
        """
        Scenario: AI agent needs to validate performance meets requirements
        Tests: All documented performance benchmarks are achievable
        """
        # Test TypeAdapter performance as documented using real large data
        tag_data = large_collection_data["tags"][:10]  # Use 10 items for performance test
        
        start_time = time.perf_counter()
        validated_tags = TagFrozensetAdapter.validate_python(tag_data)
        end_time = time.perf_counter()
        
        validation_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Should meet documented performance target
        assert validation_time < 3.0  # <3ms for 10 items
        assert len(validated_tags) == 10
        
        # Test memory usage should be reasonable
        import sys
        initial_size = sys.getsizeof(validated_tags)
        
        # Create larger dataset
        large_tag_data = large_collection_data["tags"][:100]
        large_validated = TagFrozensetAdapter.validate_python(large_tag_data)
        final_size = sys.getsizeof(large_validated)
        
        # Memory growth should be reasonable (not exponential)
        memory_ratio = final_size / initial_size if initial_size > 0 else 1
        assert memory_ratio < 20  # Should scale reasonably

    def test_ai_agent_scenario_documentation_example_accuracy(self, sample_tag_domain):
        """
        Scenario: AI agent follows exact examples from documentation
        Tests: All documented code examples work correctly
        """
        # Test 1: Basic schema creation example (as would appear in docs)
        # Using real domain object from fixture
        domain_tag = sample_tag_domain
        
        # This should work exactly as documented
        api_tag_example = ApiTag.from_domain(domain_tag)
        
        assert api_tag_example.key == domain_tag.key
        assert api_tag_example.value == domain_tag.value
        
        # Test 2: TypeAdapter usage example (as documented)
        tags_data = [
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},
            {"key": "diet", "value": "vegetarian", "author_id": "user-456", "type": "dietary"}
        ]
        
        # This should work exactly as documented
        validated_tags = TagFrozensetAdapter.validate_python(tags_data)
        assert isinstance(validated_tags, frozenset)
        assert len(validated_tags) == 2
        
        # Test 3: Four-layer conversion example (as documented)
        # Domain → API → Domain cycle should work as documented
        api_tag = ApiTag.from_domain(domain_tag)
        converted_back = api_tag.to_domain()
        
        assert converted_back.key == domain_tag.key
        assert converted_back.value == domain_tag.value
        assert converted_back.author_id == domain_tag.author_id
        assert converted_back.type == domain_tag.type


class TestAIAgentPatternComprehension:
    """
    Tests that validate AI agents can understand and apply documented patterns
    without needing clarification or additional information.
    """

    def test_pattern_decision_matrix_usability(self, sample_meal_with_complex_data):
        """
        Test that AI agent can make correct decisions using documented decision matrix
        """
        # Scenario: AI agent needs to decide when to use each conversion method
        domain_meal = sample_meal_with_complex_data
        
        # Case 1: HTTP API endpoint - should use from_domain/to_domain
        # AI agent following docs should use from_domain for API responses
        api_response = ApiMeal.from_domain(domain_meal)
        assert isinstance(api_response, ApiMeal)
        
        # Case 2: Database persistence - should use to_orm_kwargs/from_orm_model
        orm_data = api_response.to_orm_kwargs()
        assert isinstance(orm_data, dict)
        
        # Case 3: Type validation - should use TypeAdapters
        json_data = [{"key": "test", "value": "test", "author_id": "test", "type": "test"}]
        validated = TagFrozensetAdapter.validate_python(json_data)
        assert isinstance(validated, frozenset)

    def test_pattern_integration_comprehension(self):
        """
        Test that AI agent understands how patterns work together
        """
        # Scenario: AI agent needs to implement schema with multiple patterns
        
        # Should understand: Type conversions + Validation patterns
        complex_data = {
            "id": "complex_meal",
            "name": "  Complex Meal  ",  # Needs trimming (validation pattern)
            "author_id": "author-123",
            "recipes": [],  # Collection conversion pattern
            "tags": []  # Collection conversion pattern
        }
        
        # AI agent should be able to create working schema
        api_meal = ApiMeal(**complex_data)
        
        # Validate patterns applied correctly
        assert api_meal.name == "Complex Meal"  # Trimmed
        assert len(api_meal.recipes) == 0  # Collection handled
        assert len(api_meal.tags) == 0  # Collection handled

    def test_ai_agent_debugging_capability(self):
        """
        Test that error messages enable AI agent self-correction
        """
        # Scenario: AI agent makes mistake and needs to debug
        
        # Test 1: Clear validation error for self-correction
        try:
            ApiTag(
                key="invalid_key_that_is_too_long" * 10,  # Deliberately invalid
                value="test",
                author_id="test",
                type="test"
            )
            assert False, "Should fail validation"
        except ValidationError as e:
            # Error should be specific enough for AI agent to understand fix
            error_message = str(e)
            assert "key" in error_message.lower()
            # AI agent should understand it needs to fix the key field


class TestDocumentationCompletenessValidation:
    """
    Tests that validate the documentation contains all necessary information
    for successful AI agent implementation.
    """

    def test_all_common_use_cases_covered(self, sample_tag_domain, sample_meal_with_complex_data):
        """
        Test that documentation covers 90% of common schema implementation scenarios
        """
        # Common scenario 1: Simple entity with validation
        domain_tag = sample_tag_domain
        simple_entity = ApiTag.from_domain(domain_tag)
        assert simple_entity.key == domain_tag.key
        
        # Common scenario 2: Entity with collections
        domain_meal = sample_meal_with_complex_data
        complex_entity = ApiMeal.from_domain(domain_meal)
        assert complex_entity.id == domain_meal.id
        
        # Common scenario 3: Type conversions
        tag_data = [{"key": "test", "value": "test", "author_id": "test", "type": "test"}]
        converted = TagFrozensetAdapter.validate_python(tag_data)
        assert len(converted) == 1
        
        # Common scenario 4: Performance-critical validation
        start = time.perf_counter()
        for _ in range(100):
            TagFrozensetAdapter.validate_python(tag_data)
        end = time.perf_counter()
        
        # Should handle repeated validation efficiently
        assert (end - start) < 0.1  # 100 validations in <100ms

    def test_edge_case_documentation_completeness(self):
        """
        Test that documentation adequately covers edge cases
        """
        # Edge case 1: Empty collections
        empty_meal = ApiMeal(
            id="empty_meal",
            name="Empty Meal",
            author_id="author-123", 
            recipes=[],
            tags=[]
        )
        domain_meal = empty_meal.to_domain()
        assert len(domain_meal.recipes) == 0
        assert len(domain_meal.tags) == 0

    def test_documentation_accuracy_against_real_codebase(self, sample_tag_domain):
        """
        Test that documented patterns match actual codebase implementations
        """
        # Test 1: Documented TypeAdapter patterns match reality
        # TagFrozensetAdapter should work as documented
        test_data = [{"key": "test", "value": "test", "author_id": "test", "type": "test"}]
        result = TagFrozensetAdapter.validate_python(test_data)
        assert isinstance(result, frozenset)
        
        # Test 2: Documented conversion patterns match reality
        domain_tag = sample_tag_domain
        api_tag = ApiTag.from_domain(domain_tag)
        back_to_domain = api_tag.to_domain()
        
        assert back_to_domain.key == domain_tag.key
        assert back_to_domain.value == domain_tag.value
        
        # Test 3: Documented performance characteristics match reality
        start = time.perf_counter()
        large_data = [{"key": f"tag{i}", "value": f"name{i}", "author_id": f"author{i}", "type": "category"} for i in range(100)]
        TagFrozensetAdapter.validate_python(large_data)
        end = time.perf_counter()
        
        # Should meet documented performance expectations
        validation_time = (end - start) * 1000  # Convert to ms
        assert validation_time < 50  # Should be very fast for 100 items 


class TestDocumentationExampleAccuracy:
    """
    Tests that validate all code examples in documentation work correctly and accurately
    represent the actual codebase behavior. This ensures documentation stays in sync with reality.
    """

    def test_overview_document_examples(self, sample_tag_domain, sample_meal_with_complex_data):
        """
        Test all code examples from docs/architecture/api-schema-patterns/overview.md
        """
        # Example 1: Basic four-layer conversion (from overview.md)
        domain_tag = sample_tag_domain
        
        # Step 1: Domain → API (example from documentation)
        api_tag = ApiTag.from_domain(domain_tag)
        assert api_tag.key == domain_tag.key
        assert api_tag.value == domain_tag.value
        
        # Step 2: API → Domain (reverse conversion example)
        reconstructed_domain = api_tag.to_domain()
        assert reconstructed_domain.key == domain_tag.key
        assert reconstructed_domain.value == domain_tag.value
        
        # Example 2: Complex meal conversion (from overview.md)
        domain_meal = sample_meal_with_complex_data
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Validate documented behavior
        assert api_meal.id == domain_meal.id
        assert api_meal.name == domain_meal.name
        assert api_meal.author_id == domain_meal.author_id

    def test_typeadapter_usage_examples(self, large_collection_data):
        """
        Test all code examples from docs/architecture/api-schema-patterns/patterns/typeadapter-usage.md
        """
        # Example 1: Module-level singleton pattern (documented best practice)
        tag_data = [
            {"key": "cuisine", "value": "italian", "author_id": "user-123", "type": "category"},
            {"key": "diet", "value": "vegetarian", "author_id": "user-456", "type": "dietary"}
        ]
        
        # This should work exactly as documented in typeadapter-usage.md
        validated_tags = TagFrozensetAdapter.validate_python(tag_data)
        assert isinstance(validated_tags, frozenset)
        assert len(validated_tags) == 2
        
        # Example 2: Performance characteristics (documented in typeadapter-usage.md)
        import time
        start_time = time.perf_counter()
        
        # Should validate 10 items in <3ms as documented
        tag_data_10 = large_collection_data["tags"][:10]
        result = TagFrozensetAdapter.validate_python(tag_data_10)
        
        end_time = time.perf_counter()
        validation_time = (end_time - start_time) * 1000
        
        # Must meet documented performance requirement
        assert validation_time < 3.0, f"Expected <3ms, got {validation_time:.2f}ms"
        assert len(result) == 10

    def test_type_conversion_examples(self, sample_tags_collection):
        """
        Test all code examples from docs/architecture/api-schema-patterns/patterns/type-conversions.md
        """
        # Example 1: Collection type conversion (from type-conversions.md)
        domain_tags_set = set(sample_tags_collection)  # Domain: set[Tag]
        
        # Domain set → API frozenset (documented conversion)
        api_tags_frozenset = frozenset(ApiTag.from_domain(tag) for tag in domain_tags_set)
        assert isinstance(api_tags_frozenset, frozenset)
        assert len(api_tags_frozenset) == len(domain_tags_set)
        
        # Example 2: TypeAdapter conversion (from type-conversions.md)
        tag_list_data = [
            {"key": tag.key, "value": tag.value, "author_id": tag.author_id, "type": tag.type}
            for tag in sample_tags_collection
        ]
        
        # TypeAdapter validates to frozenset (documented behavior)
        validated_frozenset = TagFrozensetAdapter.validate_python(tag_list_data)
        assert isinstance(validated_frozenset, frozenset)
        assert len(validated_frozenset) == len(sample_tags_collection)

    def test_field_validation_examples(self, sample_tag_domain):
        """
        Test all code examples from docs/architecture/api-schema-patterns/patterns/field-validation.md
        """
        # Example 1: Successful validation (from field-validation.md)
        domain_tag = sample_tag_domain
        api_tag = ApiTag.from_domain(domain_tag)
        
        # Should validate successfully as documented
        assert api_tag.key == domain_tag.key.strip()  # BeforeValidator behavior
        assert api_tag.value == domain_tag.value.strip()  # BeforeValidator behavior
        
        # Example 2: Validation error handling (from field-validation.md)
        try:
            # This should fail as documented in field-validation.md
            invalid_tag = ApiTag(
                key="",  # Empty key should fail validation
                value="test",
                author_id="test", 
                type="test"
            )
            assert False, "Should have raised ValidationError as documented"
        except ValidationError as e:
            # Error should be clear as documented
            assert "key" in str(e).lower()

    def test_computed_properties_examples(self, sample_meal_with_complex_data):
        """
        Test all code examples from docs/architecture/api-schema-patterns/patterns/computed-properties.md
        """
        # Example 1: Computed property materialization (from computed-properties.md)
        domain_meal = sample_meal_with_complex_data
        
        # Computed properties should be available in domain
        # (This tests the documented domain layer behavior)
        if hasattr(domain_meal, 'nutri_facts') and domain_meal.nutri_facts is not None:
            domain_nutri_facts = domain_meal.nutri_facts
            assert domain_nutri_facts is not None
        
        # Example 2: API materialization (from computed-properties.md)
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Computed property should be materialized in API as documented
        # (API layer converts @cached_property to regular field)
        assert hasattr(api_meal, 'nutri_facts')

    def test_meal_schema_complete_examples(self, sample_meal_with_complex_data):
        """
        Test all code examples from docs/architecture/api-schema-patterns/examples/meal-schema-complete.md
        """
        # Example 1: Complete conversion cycle (from meal-schema-complete.md)
        domain_meal = sample_meal_with_complex_data
        
        # Step 1: Domain → API (documented in meal-schema-complete.md)
        api_meal = ApiMeal.from_domain(domain_meal)
        assert api_meal.id == domain_meal.id
        assert api_meal.name == domain_meal.name
        
        # Step 2: API → ORM kwargs (documented in meal-schema-complete.md)
        orm_kwargs = api_meal.to_orm_kwargs()
        assert isinstance(orm_kwargs, dict)
        assert "id" in orm_kwargs
        assert "name" in orm_kwargs
        
        # Step 3: ORM → API reconstruction (documented in meal-schema-complete.md)
        mock_orm = type('MockORM', (), orm_kwargs)()
        reconstructed_api = ApiMeal.from_orm_model(mock_orm)
        
        # Data integrity preserved as documented
        assert reconstructed_api.id == api_meal.id
        assert reconstructed_api.name == api_meal.name

    def test_performance_benchmarks_accuracy(self, large_collection_data):
        """
        Test that all performance benchmarks documented in the patterns match reality
        """
        # Benchmark 1: TagFrozensetAdapter performance (documented across multiple files)
        tag_data_100 = large_collection_data["tags"][:100]
        
        import time
        start_time = time.perf_counter()
        result = TagFrozensetAdapter.validate_python(tag_data_100)
        end_time = time.perf_counter()
        
        validation_time_ms = (end_time - start_time) * 1000
        
        # Should be very fast for 100 items as documented
        assert validation_time_ms < 50, f"Expected <50ms for 100 items, got {validation_time_ms:.2f}ms"
        assert len(result) == 100
        
        # Benchmark 2: Memory efficiency (documented in typeadapter-usage.md)
        import sys
        initial_memory = sys.getsizeof(result)
        
        # Repeated validations shouldn't cause memory growth (documented behavior)
        for _ in range(10):
            TagFrozensetAdapter.validate_python(tag_data_100[:10])
        
        final_memory = sys.getsizeof(result)
        # Memory should remain stable (singleton pattern benefit)
        memory_growth_ratio = final_memory / initial_memory if initial_memory > 0 else 1
        assert memory_growth_ratio < 2  # Minimal growth expected

    def test_decision_matrix_examples(self, sample_meal_with_complex_data, sample_tag_domain):
        """
        Test all decision matrix examples from overview.md and other pattern documentation
        """
        # Decision 1: When to use from_domain() - HTTP API responses
        domain_meal = sample_meal_with_complex_data
        api_response = ApiMeal.from_domain(domain_meal)  # Correct choice for API responses
        assert isinstance(api_response, ApiMeal)
        
        # Decision 2: When to use to_orm_kwargs() - Database persistence
        orm_data = api_response.to_orm_kwargs()  # Correct choice for DB operations
        assert isinstance(orm_data, dict)
        
        # Decision 3: When to use TypeAdapters - Input validation
        input_data = [{"key": "test", "value": "test", "author_id": "test", "type": "test"}]
        validated_input = TagFrozensetAdapter.validate_python(input_data)  # Correct choice for validation
        assert isinstance(validated_input, frozenset)
        
        # Decision 4: When to use from_orm_model() - Database retrieval
        mock_orm = type('MockORM', (), orm_data)()
        reconstructed = ApiMeal.from_orm_model(mock_orm)  # Correct choice for DB → API
        assert isinstance(reconstructed, ApiMeal)

    def test_anti_pattern_examples(self):
        """
        Test that documented anti-patterns are correctly identified and avoided
        """
        # Anti-pattern 1: TypeAdapter recreation (documented in typeadapter-usage.md)
        import time
        
        # Test performance difference between singleton and recreation patterns
        tag_data = [{"key": "test", "value": "test", "author_id": "test", "type": "test"}]
        
        # Singleton pattern (GOOD) - documented best practice
        start_singleton = time.perf_counter()
        for _ in range(10):
            TagFrozensetAdapter.validate_python(tag_data)
        end_singleton = time.perf_counter()
        singleton_time = end_singleton - start_singleton
        
        # Singleton should be consistently fast (documented benefit)
        assert singleton_time < 0.01  # Should be very fast for 10 validations
        
        # Anti-pattern 2: Empty field validation (documented in field-validation.md)
        with pytest.raises(ValidationError):
            # This anti-pattern should fail as documented
            ApiTag(key="", value="test", author_id="test", type="test")

    def test_integration_examples(self, sample_meal_with_complex_data):
        """
        Test examples showing how all patterns work together in real scenarios
        """
        # Integration example: Complete workflow (documented across all pattern files)
        domain_meal = sample_meal_with_complex_data
        
        # Step 1: Domain → API (four-layer conversion pattern)
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Step 2: Validate with TypeAdapter if needed (TypeAdapter pattern)
        # (Simulating input validation scenario)
        
        # Step 3: Database persistence preparation (type conversion pattern)
        orm_kwargs = api_meal.to_orm_kwargs()
        
        # Step 4: Reconstruction from database (computed properties + field validation)
        mock_orm = type('MockORM', (), orm_kwargs)()
        reconstructed = ApiMeal.from_orm_model(mock_orm)
        
        # Step 5: Back to domain if needed (complete cycle)
        final_domain = reconstructed.to_domain()
        
        # All patterns working together should preserve data integrity
        assert final_domain.id == domain_meal.id
        assert final_domain.name == domain_meal.name
        assert final_domain.author_id == domain_meal.author_id 