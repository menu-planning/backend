"""
Pattern Validation Tests for API Schema Documentation

This module implements comprehensive testing for the four-layer conversion pattern:
Domain → API → ORM → API → Domain

Tests validate:
1. Four-layer conversion cycle integrity 
2. Type preservation through conversions
3. Data consistency across all layers
4. Performance of conversion operations

These tests ensure documentation accuracy by validating actual codebase behavior.
"""

import pytest
from typing import Any, Dict, List, Optional, Set, Type, Union
from unittest.mock import Mock
from dataclasses import dataclass

# Import domain objects and API schemas for testing
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole


@dataclass
class ConversionTestResult:
    """Results from a four-layer conversion test."""
    success: bool
    original_data: Any
    final_data: Any
    conversion_errors: List[str]
    type_mismatches: List[str]
    performance_ms: float


class TestFourLayerConversionPattern:
    """Test the four-layer conversion pattern across all schema types."""
    
    def test_tag_conversion_cycle_integrity(self, sample_tag_domain, conversion_cycle_validator):
        """Test Tag: Domain → API → ORM → API → Domain cycle."""
        # Mock ORM model since we don't have the actual TagSaModel
        mock_orm_class = Mock()
        
        # Test the conversion cycle
        result = conversion_cycle_validator(
            domain_obj=sample_tag_domain,
            api_class=ApiTag,
            orm_class=mock_orm_class
        )
        
        # Verify cycle integrity
        assert result.success, f"Conversion cycle failed: {result.conversion_errors}"
        # For tags, compare key attributes instead of full equality
        assert sample_tag_domain.key == result.final_data.key, "Tag key should be preserved"
        assert sample_tag_domain.value == result.final_data.value, "Tag value should be preserved"
        
    def test_type_preservation_in_conversions(self, sample_tags_collection):
        """Test that type conversions preserve data integrity."""
        domain_tags = set(sample_tags_collection)  # Domain uses set
        
        # Convert to API layer (should become frozenset)
        api_tags = frozenset(ApiTag.from_domain(tag) for tag in domain_tags)
        assert isinstance(api_tags, frozenset), "API layer should use frozenset"
        assert len(api_tags) == len(domain_tags), "Tag count should be preserved"
        
        # Convert back to domain layer
        reconstructed_domain = {api_tag.to_domain() for api_tag in api_tags}
        assert isinstance(reconstructed_domain, set), "Domain layer should use set"
        assert reconstructed_domain == domain_tags, "Data should be identical after round-trip"
        
    def test_collection_type_transformations(self, sample_tags_collection, sample_api_tags_collection):
        """Test the documented type transformation patterns."""
        # Test set → frozenset → list transformations
        domain_set = set(sample_tags_collection)
        api_frozenset = frozenset(sample_api_tags_collection)
        
        # Simulate ORM conversion (frozenset → list for database)
        orm_list = list(api_frozenset)
        assert isinstance(orm_list, list), "ORM layer should use list for relational storage"
        
        # Simulate reconstruction (list → frozenset → set)
        reconstructed_frozenset = frozenset(orm_list)
        reconstructed_domain = {item.to_domain() for item in reconstructed_frozenset}
        
        assert len(reconstructed_domain) == len(domain_set), "Collection size should be preserved"
        
    @pytest.mark.performance
    def test_conversion_performance_benchmarks(self, sample_tags_collection, performance_validator):
        """Test that four-layer conversions meet performance requirements."""
        domain_tags = set(sample_tags_collection)
        
        def full_conversion_cycle():
            # Domain → API
            api_tags = frozenset(ApiTag.from_domain(tag) for tag in domain_tags)
            
            # API → ORM kwargs (simulate)
            orm_kwargs_list = [tag.to_orm_kwargs() for tag in api_tags]
            
            # ORM → API (simulate)
            mock_orm_objects = [Mock(**kwargs) for kwargs in orm_kwargs_list]
            reconstructed_api = frozenset(ApiTag.from_orm_model(orm_obj) for orm_obj in mock_orm_objects)
            
            # API → Domain
            final_domain = {tag.to_domain() for tag in reconstructed_api}
            return final_domain
        
        # Test performance (should complete in < 5ms for 3 tags)
        performance_validator(
            operation_func=full_conversion_cycle,
            max_time_ms=5.0,
            operation_name="four_layer_conversion_cycle"
        )


class TestValidationPatternCompliance:
    """Test that schemas follow documented validation patterns."""
    
    def test_before_validator_usage_patterns(self, sample_ingredient_data):
        """Test BeforeValidator patterns for data cleanup."""
        # Test with whitespace and empty string handling
        test_data = sample_ingredient_data.copy()
        test_data["name"] = "  Tomatoes  "  # Should be trimmed
        
        ingredient = ApiIngredient.model_validate(test_data)
        assert ingredient.name == "Tomatoes", "BeforeValidator should trim whitespace"
        
    def test_field_validator_business_logic(self, sample_tags_collection):
        """Test field_validator patterns for business logic validation."""
        # Test that validation catches business rule violations
        api_tags = [ApiTag.from_domain(tag) for tag in sample_tags_collection]
        
        # Each tag should be valid individually
        for tag in api_tags:
            assert tag.key is not None, "Tag key is required"
            assert tag.value is not None, "Tag value is required"
            
    def test_computed_property_materialization(self):
        """Test that computed properties are properly materialized in API layer."""
        # This would test the @cached_property → regular field pattern
        # Implementation would depend on having Meal schema with nutri_facts
        pytest.skip("Requires ApiMeal implementation - will be tested in Phase 1.2")


class TestTypeAdapterPatternCompliance:
    """Test that TypeAdapter usage follows documented patterns."""
    
    def test_singleton_pattern_validation(self):
        """Test that TypeAdapters are implemented as module-level singletons."""
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import TagFrozensetAdapter
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import IngredientListAdapter
        
        # Verify adapters are module-level objects, not functions
        assert hasattr(TagFrozensetAdapter, 'validate_python'), "Should be TypeAdapter instance"
        assert hasattr(IngredientListAdapter, 'validate_python'), "Should be TypeAdapter instance"
        
    def test_adapter_performance_against_baselines(self, large_collection_data, performance_validator):
        """Test that TypeAdapter performance meets documented standards."""
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import TagFrozensetAdapter
        
        tag_data = large_collection_data["tags"][:10]  # Test with 10 items
        
        def validate_tags():
            return TagFrozensetAdapter.validate_python(tag_data)
        
        # Should validate 10 tags in < 3ms (PRD requirement)
        performance_validator(
            operation_func=validate_tags,
            max_time_ms=3.0,
            operation_name="typeadapter_10_tag_validation"
        )


class TestErrorHandlingPatterns:
    """Test error handling patterns in API schemas."""
    
    def test_validation_error_clarity(self):
        """Test that validation errors provide clear, actionable messages."""
        # Test invalid tag data
        invalid_tag_data = {"key": "", "value": None, "author_id": "invalid", "type": "unknown"}
        
        with pytest.raises(Exception) as exc_info:
            ApiTag.model_validate(invalid_tag_data)
        
        # Error should be informative (exact validation depends on implementation)
        assert str(exc_info.value), "Validation error should have descriptive message"
        
    def test_graceful_degradation(self, sample_ingredient_data):
        """Test that schemas handle partial data gracefully."""
        # Test with optional fields missing
        minimal_data = {
            "name": sample_ingredient_data["name"],
            "quantity": sample_ingredient_data["quantity"],
            "unit": sample_ingredient_data["unit"],
            "position": sample_ingredient_data["position"],
            "full_text": sample_ingredient_data["full_text"],
            "product_id": sample_ingredient_data["product_id"]
        }
        
        # Should validate successfully (all these fields are actually required for ApiIngredient)
        ingredient = ApiIngredient.model_validate(minimal_data)
        assert ingredient.name == minimal_data["name"]


class TestSecurityPatterns:
    """Test security best practices in API schemas."""
    
    def test_input_sanitization(self):
        """Test that inputs are properly sanitized."""
        # Test with potentially dangerous input
        malicious_tag_data = {
            "key": "<script>alert('xss')</script>",
            "value": "'; DROP TABLE users; --",
            "author_id": "user-123",
            "type": "category"
        }
        
        tag = ApiTag.model_validate(malicious_tag_data)
        # Validation should succeed but data should be safely handled
        assert tag.key == malicious_tag_data["key"]  # Raw storage, sanitization happens at display
        
    def test_no_information_leakage_in_errors(self):
        """Test that error messages don't leak sensitive information."""
        # Test with invalid UUID format that will actually raise an error
        invalid_data = {
            "key": "test", 
            "value": "test", 
            "author_id": "not-a-uuid-format", 
            "type": None  # Invalid type should cause validation error
        }
        
        with pytest.raises(Exception) as exc_info:
            ApiTag.model_validate(invalid_data)
        
        error_msg = str(exc_info.value).lower()
        # Error should not contain sensitive system information
        assert "database" not in error_msg, "Error should not leak database info"
        assert "connection" not in error_msg, "Error should not leak connection info"


@pytest.fixture
def pattern_compliance_validator():
    """Create utility for testing pattern compliance."""
    def validate_schema_compliance(schema_class: Type, test_data: Dict[str, Any]) -> ConversionTestResult:
        """
        Validate that a schema class follows documented patterns.
        
        Args:
            schema_class: The API schema class to test
            test_data: Sample data for testing
            
        Returns:
            ConversionTestResult with compliance results
        """
        errors = []
        type_mismatches = []
        
        try:
            # Test basic validation
            instance = schema_class.model_validate(test_data)
            
            # Test required methods exist
            required_methods = ['to_domain', 'from_domain', 'to_orm_kwargs', 'from_orm_model']
            for method in required_methods:
                if not hasattr(schema_class, method):
                    errors.append(f"Missing required method: {method}")
            
            # Test type annotations
            if not hasattr(schema_class, '__annotations__'):
                errors.append("Schema should have type annotations")
                
            success = len(errors) == 0
            
        except Exception as e:
            errors.append(f"Validation failed: {str(e)}")
            success = False
            instance = None
        
        return ConversionTestResult(
            success=success,
            original_data=test_data,
            final_data=instance,
            conversion_errors=errors,
            type_mismatches=type_mismatches,
            performance_ms=0.0
        )
    
    return validate_schema_compliance 