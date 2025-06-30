"""
Test suite for SQLAlchemy composite field handling patterns in API schemas.

This module tests BEHAVIOR, not implementation - validating that composite field
data flows correctly through all four conversion layers while maintaining data integrity.

Tests cover the four composite patterns found in the codebase:
1. Direct Dictionary Conversion (nutri_facts pattern)
2. Value Object Pattern (profile/contact_info/address pattern)
3. Model Validation Pattern (simple composites)
4. Complex Type Conversion Pattern (collection handling)
"""

import pytest
from datetime import date, datetime
from typing import Any, Dict

from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import ContactInfoSaModel
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.contact_info import ApiContactInfo
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit


class TestDirectDictionaryConversionPattern:
    """
    Test the direct dictionary conversion pattern used for nutri_facts.
    
    Pattern: API schema accesses composite.__dict__ for from_orm_model()
    and creates new composite(**api.model_dump()) for to_orm_kwargs().
    """
    
    def test_nutri_facts_orm_to_api_conversion_behavior(self):
        """
        BEHAVIOR: ORM composite fields should convert to API schema fields correctly.
        
        This tests that accessing __dict__ from a composite dataclass provides
        the correct field values for API schema instantiation.
        """
        # Given: A populated NutriFactsSaModel composite
        nutri_facts_orm = NutriFactsSaModel(
            calories=150.5,
            protein=12.3,
            carbohydrate=20.1,
            total_fat=5.2,
            dietary_fiber=3.1,
            sodium=250.0,
            # ... other fields can be None
        )
        
        # When: Converting using the direct dictionary pattern
        api_nutri_facts = ApiNutriFacts(**nutri_facts_orm.__dict__)
        
        # Then: All values should be preserved accurately
        assert api_nutri_facts.calories == 150.5
        assert api_nutri_facts.protein == 12.3
        assert api_nutri_facts.carbohydrate == 20.1
        assert api_nutri_facts.total_fat == 5.2
        assert api_nutri_facts.dietary_fiber == 3.1
        assert api_nutri_facts.sodium == 250.0
        
    def test_nutri_facts_api_to_orm_conversion_behavior(self):
        """
        BEHAVIOR: API schema fields should convert back to ORM composite correctly.
        
        This tests that model_dump() provides the correct dictionary structure
        for creating a new composite instance.
        """
        # Given: A populated ApiNutriFacts instance
        api_nutri_facts = ApiNutriFacts(
            calories=200.0,
            protein=15.5,
            carbohydrate=25.0,
            total_fat=8.0,
            sodium=300.0
        )
        
        # When: Converting using the model_dump pattern
        nutri_facts_orm = NutriFactsSaModel(**api_nutri_facts.model_dump())
        
        # Then: All values should be preserved accurately
        assert nutri_facts_orm.calories == 200.0
        assert nutri_facts_orm.protein == 15.5
        assert nutri_facts_orm.carbohydrate == 25.0
        assert nutri_facts_orm.total_fat == 8.0
        assert nutri_facts_orm.sodium == 300.0
        
    def test_nutri_facts_roundtrip_conversion_behavior(self):
        """
        BEHAVIOR: Data should survive complete roundtrip conversion.
        
        Tests: ORM composite → API → ORM kwargs → new ORM composite
        """
        # Given: Original ORM composite with mixed None and valued fields
        original_orm = NutriFactsSaModel(
            calories=175.0,
            protein=14.2,
            carbohydrate=None,  # None values should be preserved
            total_fat=6.5,
            sodium=280.0,
            vitamin_c=None
        )
        
        # When: Complete roundtrip conversion
        api_instance = ApiNutriFacts(**original_orm.__dict__)
        orm_kwargs = api_instance.model_dump()
        final_orm = NutriFactsSaModel(**orm_kwargs)
        
        # Then: All data should be identical after roundtrip
        assert final_orm.calories == original_orm.calories
        assert final_orm.protein == original_orm.protein
        assert final_orm.carbohydrate == original_orm.carbohydrate  # None preserved
        assert final_orm.total_fat == original_orm.total_fat
        assert final_orm.sodium == original_orm.sodium
        assert final_orm.vitamin_c == original_orm.vitamin_c  # None preserved


class TestValueObjectPattern:
    """
    Test the value object pattern used for profile, contact_info, address.
    
    Pattern: API schema delegates conversion to value object methods
    from_orm_model() and to_orm_kwargs().
    """
    
    def test_profile_value_object_conversion_behavior(self):
        """
        BEHAVIOR: Profile composite should convert through value object pattern.
        
        This tests that model_validate() correctly handles composite dataclass
        field mapping to API schema fields.
        """
        # Given: A ProfileSaModel composite instance
        profile_orm = ProfileSaModel(
            name="John Doe",
            birthday=date(1990, 5, 15),
            sex="M"
        )
        
        # When: Converting using value object pattern
        api_profile = ApiProfile.from_orm_model(profile_orm)
        
        # Then: All fields should be correctly mapped
        assert api_profile.name == "John Doe"
        assert api_profile.birthday == date(1990, 5, 15)
        assert api_profile.sex == "M"
        
    def test_profile_orm_kwargs_conversion_behavior(self):
        """
        BEHAVIOR: Profile API should convert to ORM kwargs correctly.
        
        This tests that model_dump() provides the correct structure
        for creating composite instances.
        """
        # Given: An ApiProfile instance
        api_profile = ApiProfile(
            name="Jane Smith",
            birthday=date(1985, 12, 3),
            sex="F"
        )
        
        # When: Converting to ORM kwargs
        orm_kwargs = api_profile.to_orm_kwargs()
        
        # Then: Structure should be suitable for composite creation
        assert orm_kwargs["name"] == "Jane Smith"
        assert orm_kwargs["birthday"] == date(1985, 12, 3)
        assert orm_kwargs["sex"] == "F"
        
        # And: Should be able to create composite instance
        profile_composite = ProfileSaModel(**orm_kwargs)
        assert profile_composite.name == "Jane Smith"
        
    def test_contact_info_collection_conversion_behavior(self):
        """
        BEHAVIOR: ContactInfo should handle set ↔ list conversion correctly.
        
        This tests the complex type conversion pattern where API uses sets
        but ORM composites store as lists.
        """
        # Given: ContactInfoSaModel with list fields
        contact_orm = ContactInfoSaModel(
            main_phone="+1234567890",
            main_email="john@example.com",
            all_phones=["+1234567890", "+0987654321"],
            all_emails=["john@example.com", "john.work@company.com"]
        )
        
        # When: Converting to API (list → set conversion)
        api_contact = ApiContactInfo.from_orm_model(contact_orm)
        
        # Then: Collections should be converted to sets
        assert api_contact.main_phone == "+1234567890"
        assert api_contact.main_email == "john@example.com"
        assert api_contact.all_phones == {"+1234567890", "+0987654321"}
        assert api_contact.all_emails == {"john@example.com", "john.work@company.com"}
        
    def test_contact_info_roundtrip_collection_behavior(self):
        """
        BEHAVIOR: ContactInfo collections should survive roundtrip conversion.
        
        Tests: ORM lists → API sets → ORM lists with data integrity preserved.
        """
        # Given: Original contact with duplicate-free collections
        original_contact = ContactInfoSaModel(
            main_phone="+1111111111",
            main_email="test@example.com",
            all_phones=["+1111111111", "+2222222222", "+3333333333"],
            all_emails=["test@example.com", "test2@example.com"]
        )
        
        # When: Complete roundtrip conversion
        api_contact = ApiContactInfo.from_orm_model(original_contact)
        orm_kwargs = api_contact.to_orm_kwargs()
        
        # Then: Collections should maintain data integrity
        assert set(orm_kwargs["all_phones"]) == {"+1111111111", "+2222222222", "+3333333333"}
        assert set(orm_kwargs["all_emails"]) == {"test@example.com", "test2@example.com"}
        
        # And: Should be able to recreate composite
        final_contact = ContactInfoSaModel(**orm_kwargs)
        assert final_contact.main_phone == original_contact.main_phone
        assert set(final_contact.all_phones) == set(original_contact.all_phones)


class TestCompositeFieldNullHandling:
    """
    Test how composite fields handle None/null values in various scenarios.
    
    This is critical for real-world usage where composite fields may be optional.
    """
    
    def test_none_composite_handling_behavior(self):
        """
        BEHAVIOR: None composite values should be handled gracefully.
        
        This tests the pattern used in ApiMeal for optional nutri_facts.
        """
        # Given: None nutri_facts (as would come from ORM)
        nutri_facts_orm = None
        
        # When: Converting using the pattern from ApiMeal.from_orm_model()
        api_nutri_facts = ApiNutriFacts(**nutri_facts_orm.__dict__) if nutri_facts_orm else None
        
        # Then: Should handle None gracefully
        assert api_nutri_facts is None
        
    def test_none_value_object_composite_handling(self):
        """
        BEHAVIOR: None value objects should be handled correctly in conversion.
        
        This tests the pattern used in ApiClient for optional contact_info/address.
        """
        # Given: None contact_info (as would come from ORM)
        contact_info_orm = None
        
        # When: Converting using the pattern from ApiClient.from_orm_model()
        api_contact_info = ApiContactInfo.from_orm_model(contact_info_orm) if contact_info_orm else None
        
        # Then: Should handle None gracefully
        assert api_contact_info is None
        
    def test_empty_composite_vs_none_behavior(self):
        """
        BEHAVIOR: Empty composites should be distinguishable from None.
        
        This tests edge cases where composite exists but has no meaningful data.
        """
        # Given: Empty but not None composite
        empty_nutri_facts = NutriFactsSaModel()  # All fields None by default
        
        # When: Converting to API
        api_nutri_facts = ApiNutriFacts(**empty_nutri_facts.__dict__)
        
        # Then: Should create valid API object with None values
        assert api_nutri_facts is not None
        assert api_nutri_facts.calories is None
        assert api_nutri_facts.protein is None
        
        # And: Should convert back to equivalent ORM composite
        orm_kwargs = api_nutri_facts.model_dump()
        recreated_composite = NutriFactsSaModel(**orm_kwargs)
        assert recreated_composite.calories is None
        assert recreated_composite.protein is None


class TestCompositeFieldPerformance:
    """
    Test performance characteristics of composite field conversions.
    
    These tests ensure that the composite patterns don't introduce performance regressions.
    """
    
    def test_large_nutri_facts_conversion_performance(self, benchmark):
        """
        BEHAVIOR: Large nutri_facts conversions should be performant.
        
        This tests that the __dict__ access pattern doesn't create performance issues.
        """
        # Given: Fully populated NutriFactsSaModel (all 80+ fields)
        nutri_facts_orm = NutriFactsSaModel(
            calories=200.0, protein=15.0, carbohydrate=30.0, total_fat=8.0,
            saturated_fat=2.5, trans_fat=0.1, dietary_fiber=5.0, sodium=400.0,
            # ... populate many more fields for realistic test
            vitamin_a=500.0, vitamin_c=25.0, vitamin_d=10.0, vitamin_e=8.0,
            calcium=150.0, iron=2.5, potassium=300.0, magnesium=50.0
        )
        
        def convert_nutri_facts():
            # Simulate the conversion pattern from ApiMeal
            api_instance = ApiNutriFacts(**nutri_facts_orm.__dict__)
            orm_kwargs = api_instance.model_dump()
            return NutriFactsSaModel(**orm_kwargs)
        
        # When: Running conversion benchmark
        result = benchmark(convert_nutri_facts)
        
        # Then: Should complete efficiently (exact timing is environment-dependent)
        assert result is not None
        assert result.calories == 200.0
        
    def test_multiple_composite_fields_performance(self, benchmark):
        """
        BEHAVIOR: Multiple composite fields should convert efficiently.
        
        This tests the performance of converting multiple composites like in ApiClient.
        """
        # Given: Multiple composite instances as in ClientSaModel
        profile_orm = ProfileSaModel(name="Test User", birthday=date(1990, 1, 1), sex="M")
        contact_orm = ContactInfoSaModel(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=["+1111111111", "+2222222222"],
            all_emails=["test@example.com", "work@example.com"]
        )
        
        def convert_multiple_composites():
            # Simulate the conversion pattern from ApiClient
            api_profile = ApiProfile.from_orm_model(profile_orm)
            api_contact = ApiContactInfo.from_orm_model(contact_orm)
            
            profile_kwargs = api_profile.to_orm_kwargs()
            contact_kwargs = api_contact.to_orm_kwargs()
            
            return (
                ProfileSaModel(**profile_kwargs),
                ContactInfoSaModel(**contact_kwargs)
            )
        
        # When: Running multiple composite conversion benchmark
        result = benchmark(convert_multiple_composites)
        
        # Then: Should complete efficiently
        assert result is not None
        assert len(result) == 2
        assert result[0].name == "Test User"
        assert result[1].main_phone == "+1234567890"


class TestCompositeFieldIntegrationPatterns:
    """
    Test how composite fields integrate with the four-layer conversion pattern.
    
    These tests validate that composite field handling works correctly within
    the broader API schema conversion ecosystem.
    """
    
    def test_composite_in_full_four_layer_conversion(self):
        """
        BEHAVIOR: Composite fields should work correctly in the actual patterns used in the codebase.
        
        This tests the direct dictionary conversion pattern used for nutri_facts composite
        and the value object pattern used for profile/contact_info composites.
        """
        # Test 1: Direct Dictionary Conversion Pattern (nutri_facts style)
        # Given: NutriFactsSaModel with simple float values (as used in actual ORM)
        nutri_facts_orm = NutriFactsSaModel(
            calories=180.0,
            protein=12.0,
            carbohydrate=25.0,
            total_fat=6.0
        )
        
        # When: Converting using the direct dictionary pattern
        # ORM → API using __dict__ pattern
        api_nutri_facts = ApiNutriFacts(**nutri_facts_orm.__dict__)
        
        # API → ORM kwargs using model_dump pattern
        orm_kwargs = api_nutri_facts.model_dump()
        final_nutri_facts_orm = NutriFactsSaModel(**orm_kwargs)
        
        # Then: Data should survive the conversion cycle
        assert final_nutri_facts_orm.calories == nutri_facts_orm.calories
        assert final_nutri_facts_orm.protein == nutri_facts_orm.protein
        assert final_nutri_facts_orm.carbohydrate == nutri_facts_orm.carbohydrate
        assert final_nutri_facts_orm.total_fat == nutri_facts_orm.total_fat
        
        # Test 2: Value Object Pattern (profile style)
        # Given: ProfileSaModel composite
        profile_orm = ProfileSaModel(
            name="John Doe",
            birthday=date(1990, 5, 15),
            sex="M"
        )
        
        # When: Converting using the value object pattern
        # ORM → API using from_orm_model
        api_profile = ApiProfile.from_orm_model(profile_orm)
        
        # API → ORM kwargs using to_orm_kwargs
        profile_kwargs = api_profile.to_orm_kwargs()
        final_profile_orm = ProfileSaModel(**profile_kwargs)
        
        # Then: Data should survive the conversion cycle
        assert final_profile_orm.name == profile_orm.name
        assert final_profile_orm.birthday == profile_orm.birthday
        assert final_profile_orm.sex == profile_orm.sex
        
    def test_composite_field_validation_integration(self):
        """
        BEHAVIOR: Composite field conversions should work with Pydantic validation.
        
        This tests that composite patterns don't interfere with field validation.
        """
        # Given: Invalid data that should trigger validation
        invalid_nutri_facts_data = {
            "calories": "not_a_number",  # Invalid type
            "protein": -5.0,  # Potentially invalid value
        }
        
        # When: Creating API instance with validation
        with pytest.raises((ValueError, TypeError)):
            ApiNutriFacts(**invalid_nutri_facts_data)
        
        # Then: Validation should work normally with composite pattern
        # (The pattern itself doesn't break validation)
        
    def test_composite_field_partial_data_behavior(self):
        """
        BEHAVIOR: Composite fields should handle partial data correctly.
        
        This tests real-world scenarios where only some composite fields are populated.
        """
        # Given: Partially populated composite (common in real data)
        partial_nutri_facts = NutriFactsSaModel(
            calories=150.0,
            protein=10.0,
            # carbohydrate=None (not provided)
            # total_fat=None (not provided)
        )
        
        # When: Converting through API schema
        api_instance = ApiNutriFacts(**partial_nutri_facts.__dict__)
        orm_kwargs = api_instance.model_dump()
        
        # Then: Partial data should be preserved correctly
        assert orm_kwargs["calories"] == 150.0
        assert orm_kwargs["protein"] == 10.0
        assert orm_kwargs["carbohydrate"] is None
        assert orm_kwargs["total_fat"] is None
        
        # And: Should be able to recreate composite
        recreated_composite = NutriFactsSaModel(**orm_kwargs)
        assert recreated_composite.calories == 150.0
        assert recreated_composite.protein == 10.0
        assert recreated_composite.carbohydrate is None 