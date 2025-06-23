"""
Data factories for ProductRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness  
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different product types

This module includes both domain model and ORM model factories:

DOMAIN MODEL FACTORIES:
- All data follows the exact structure of Product domain entities and their relationships
- Uses value objects like Score, IsFoodVotes, NutriFacts
- Methods: create_product_kwargs(), create_product(), create_source_kwargs(), etc.

ORM MODEL FACTORIES:
- All data follows the exact structure of ProductSaModel ORM entities and their relationships
- Uses individual fields instead of value objects (e.g., final_score vs Score object)
- Methods: create_ORM_product_kwargs(), create_ORM_product(), create_ORM_source_kwargs(), etc.
- ORM methods only reference other ORM methods to maintain separation

Both sets of factories use separate counters to ensure deterministic but distinct test data.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import uuid
from decimal import Decimal

from src.contexts.products_catalog.core.adapters.name_search import StrProcessor
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import IsFoodVotes
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

# ORM Model imports
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import ProductSaModel, ScoreSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import SourceSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import BrandSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.category_sa_model import CategorySaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_categorysa_model import ParentCategorySaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.food_group_sa_model import FoodGroupSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type_sa_model import ProcessTypeSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.is_food_votes import IsFoodVotesSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_PRODUCT_COUNTER = 1
_SOURCE_COUNTER = 1
_BRAND_COUNTER = 1
_CATEGORY_COUNTER = 1

# ORM-specific counters (separate from domain model counters)
_ORM_PRODUCT_COUNTER = 1
_ORM_SOURCE_COUNTER = 1
_ORM_BRAND_COUNTER = 1
_ORM_CATEGORY_COUNTER = 1

def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _PRODUCT_COUNTER, _SOURCE_COUNTER, _BRAND_COUNTER, _CATEGORY_COUNTER
    global _ORM_PRODUCT_COUNTER, _ORM_SOURCE_COUNTER, _ORM_BRAND_COUNTER, _ORM_CATEGORY_COUNTER
    _PRODUCT_COUNTER = 1
    _SOURCE_COUNTER = 1
    _BRAND_COUNTER = 1
    _CATEGORY_COUNTER = 1
    _ORM_PRODUCT_COUNTER = 1
    _ORM_SOURCE_COUNTER = 1
    _ORM_BRAND_COUNTER = 1
    _ORM_CATEGORY_COUNTER = 1

# =============================================================================
# PRODUCT DATA FACTORIES
# =============================================================================

def create_product_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create product kwargs with deterministic values and validation.
    
    Following seedwork pattern with static counters for consistent test behavior.
    All required entity attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required product creation parameters
    """
    global _PRODUCT_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Use simple source_id that can be created by tests - source_id is REQUIRED (NOT NULL)
    # Tests should create the source entity separately if needed
    simple_source_id = f"test_source_{(_PRODUCT_COUNTER % 3) + 1}"
    
    defaults = {
        "id": f"product_{_PRODUCT_COUNTER:03d}",
        "source_id": simple_source_id,  # REQUIRED - tests must ensure this source exists
        "name": f"Test Product {_PRODUCT_COUNTER}",
        "is_food": True,  # Most products are food for testing
        "shopping_name": f"Shopping Name {_PRODUCT_COUNTER}",
        "store_department_name": f"Department {((_PRODUCT_COUNTER - 1) % 6)}",
        "recommended_brands_and_products": f"Recommended brands for product {_PRODUCT_COUNTER}",
        "edible_yield": Decimal("0.85") + Decimal(str((_PRODUCT_COUNTER % 20) / 100)),  # 0.85-1.04
        "kg_per_unit": 0.5 + (_PRODUCT_COUNTER % 10) * 0.1,  # 0.5-1.4 kg
        "liters_per_kg": 1.0 + (_PRODUCT_COUNTER % 5) * 0.1,  # 1.0-1.4 L/kg
        "nutrition_group": f"nutrition_group_{((_PRODUCT_COUNTER - 1) % 6) + 1}",
        "cooking_factor": 1.0 + (_PRODUCT_COUNTER % 3) * 0.2,  # 1.0-1.4
        "conservation_days": 7 + (_PRODUCT_COUNTER % 14),  # 7-20 days
        "substitutes": f"substitute_product_{_PRODUCT_COUNTER % 5 + 1}",
        "barcode": f"123456789{_PRODUCT_COUNTER:03d}" if _PRODUCT_COUNTER % 3 == 0 else None,  # Every 3rd has barcode
        
        # OPTIONAL FOREIGN KEYS - Set to None to avoid constraint violations
        # Tests can override these if they create the referenced entities
        "brand_id": None,  # Optional - was f"brand_{(_PRODUCT_COUNTER % 5) + 1}"
        "category_id": None,  # Optional - was f"category_fruits_{category_index + 1}"
        "parent_category_id": None,  # Optional - was f"parent_category_{(category_index // 2) + 1}"
        "food_group_id": None,  # Optional - was f"food_group_{category_index + 1}" 
        "process_type_id": None,  # Optional - was f"process_type_{(_PRODUCT_COUNTER % 4) + 1}"
        
        "score": Score(
            final=0.7 + (_PRODUCT_COUNTER % 30) / 100,  # 0.7-0.99
            ingredients=0.6 + (_PRODUCT_COUNTER % 40) / 100,  # 0.6-0.99
            nutrients=0.8 + (_PRODUCT_COUNTER % 20) / 100   # 0.8-0.99
        ),
        "ingredients": f"ingredient1, ingredient2, ingredient{_PRODUCT_COUNTER}",
        "package_size": 500.0 + (_PRODUCT_COUNTER % 10) * 100,  # 500-1400g
        "package_size_unit": "g" if _PRODUCT_COUNTER % 2 == 0 else "ml",
        "image_url": f"https://example.com/product_{_PRODUCT_COUNTER}.jpg" if _PRODUCT_COUNTER % 4 == 0 else None,
        "nutri_facts": NutriFacts(
            calories=200 + (_PRODUCT_COUNTER % 300),  # 200-499 kcal
            protein=10.0 + (_PRODUCT_COUNTER % 20),   # 10-29g
            carbohydrate=20.0 + (_PRODUCT_COUNTER % 50),  # 20-69g
            total_fat=5.0 + (_PRODUCT_COUNTER % 25)   # 5-29g
        ),
        "json_data": f'{{"test_data": "product_{_PRODUCT_COUNTER}"}}',
        "created_at": base_time + timedelta(hours=_PRODUCT_COUNTER),
        "updated_at": base_time + timedelta(hours=_PRODUCT_COUNTER, minutes=30),
        "discarded": False,
        "version": 1,
        "is_food_votes": IsFoodVotes(
            acceptance_line={
                0: None,
                3: 1,
                5: 0.7,
            }
        ),  # Empty votes for clean testing
    }
    
    # Override with provided kwargs
    defaults.update(kwargs)
    
    # Increment counter for next call
    _PRODUCT_COUNTER += 1
    
    return defaults

def create_product(**kwargs) -> Product:
    """
    Create a Product domain entity with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Product domain entity
    """
    product_kwargs = create_product_kwargs(**kwargs)
    return Product(**product_kwargs)

# =============================================================================
# ORM PRODUCT DATA FACTORIES
# =============================================================================

def create_ORM_product_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ORM product kwargs with deterministic values and validation.
    
    Following seedwork pattern with static counters for consistent test behavior.
    All required ORM entity attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ORM product creation parameters
    """
    global _ORM_PRODUCT_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Use simple source_id that can be created by tests - source_id is REQUIRED (NOT NULL)
    # Tests should create the source entity separately if needed
    simple_source_id = f"orm_test_source_{(_ORM_PRODUCT_COUNTER % 3) + 1}"
    
    final_kwargs = {
        "id": kwargs.get("id", f"orm_product_{_ORM_PRODUCT_COUNTER:03d}"),
        "source_id": kwargs.get("source_id", simple_source_id),  # REQUIRED - tests must ensure this source exists
        "name": kwargs.get("name", f"ORM Test Product {_ORM_PRODUCT_COUNTER}"),
        # "preprocessed_name": f"orm test product {_ORM_PRODUCT_COUNTER}",
        "is_food": kwargs.get("is_food", True),  # Most products are food for testing
        "is_food_houses_choice": kwargs.get("is_food_houses_choice", None),
        "shopping_name": kwargs.get("shopping_name", f"ORM Shopping Name {_ORM_PRODUCT_COUNTER}"),
        "store_department_name": kwargs.get("store_department_name", f"ORM Department {((_ORM_PRODUCT_COUNTER - 1) % 6)}"),
        "recommended_brands_and_products": kwargs.get("recommended_brands_and_products", f"ORM Recommended brands for product {_ORM_PRODUCT_COUNTER}"),
        "edible_yield": kwargs.get("edible_yield", Decimal("0.85") + Decimal(str((_ORM_PRODUCT_COUNTER % 20) / 100))),  # 0.85-1.04
        "kg_per_unit": kwargs.get("kg_per_unit", 0.5 + (_ORM_PRODUCT_COUNTER % 10) * 0.1),  # 0.5-1.4 kg
        "liters_per_kg": kwargs.get("liters_per_kg", 1.0 + (_ORM_PRODUCT_COUNTER % 5) * 0.1),  # 1.0-1.4 L/kg
        "nutrition_group": kwargs.get("nutrition_group", f"orm_nutrition_group_{((_ORM_PRODUCT_COUNTER - 1) % 6) + 1}"),
        "cooking_factor": kwargs.get("cooking_factor", 1.0 + (_ORM_PRODUCT_COUNTER % 3) * 0.2),  # 1.0-1.4
        "conservation_days": kwargs.get("conservation_days", 7 + (_ORM_PRODUCT_COUNTER % 14)),  # 7-20 days
        "substitutes": kwargs.get("substitutes", f"orm_substitute_product_{_ORM_PRODUCT_COUNTER % 5 + 1}"),
        "barcode": kwargs.get("barcode", f"987654321{_ORM_PRODUCT_COUNTER:03d}" if _ORM_PRODUCT_COUNTER % 3 == 0 else None),  # Every 3rd has barcode
        
        # OPTIONAL FOREIGN KEYS - Set to None to avoid constraint violations
        # Tests can override these if they create the referenced entities
        "brand_id": kwargs.get("brand_id", None),  # Optional
        "category_id": kwargs.get("category_id", None),  # Optional
        "parent_category_id": kwargs.get("parent_category_id", None),  # Optional
        "food_group_id": kwargs.get("food_group_id", None),  # Optional 
        "process_type_id": kwargs.get("process_type_id", None),  # Optional
        
        # ORM uses individual score fields instead of Score value object
        "final_score": kwargs.get("final_score", 0.7 + (_ORM_PRODUCT_COUNTER % 30) / 100),  # 0.7-0.99
        "ingredients_score": kwargs.get("ingredients_score", 0.6 + (_ORM_PRODUCT_COUNTER % 40) / 100),  # 0.6-0.99
        "nutrients_score": kwargs.get("nutrients_score", 0.8 + (_ORM_PRODUCT_COUNTER % 20) / 100),   # 0.8-0.99
        
        "ingredients": kwargs.get("ingredients", f"orm ingredient1, orm ingredient2, orm ingredient{_ORM_PRODUCT_COUNTER}"),
        "package_size": kwargs.get("package_size", 500.0 + (_ORM_PRODUCT_COUNTER % 10) * 100),  # 500-1400g
        "package_size_unit": kwargs.get("package_size_unit", "g" if _ORM_PRODUCT_COUNTER % 2 == 0 else "ml"),
        "image_url": kwargs.get("image_url", f"https://example.com/orm_product_{_ORM_PRODUCT_COUNTER}.jpg" if _ORM_PRODUCT_COUNTER % 4 == 0 else None),
        
        # ORM uses individual nutri_facts fields instead of NutriFacts value object
        "calories": kwargs.get("calories", 200.0 + (_ORM_PRODUCT_COUNTER % 300)),  # 200-499 kcal
        "protein": kwargs.get("protein", 10.0 + (_ORM_PRODUCT_COUNTER % 20)),   # 10-29g
        "carbohydrate": kwargs.get("carbohydrate", 20.0 + (_ORM_PRODUCT_COUNTER % 50)),  # 20-69g
        "total_fat": kwargs.get("total_fat", 5.0 + (_ORM_PRODUCT_COUNTER % 25)),   # 5-29g
        
        "json_data": kwargs.get("json_data", f'{{"orm_test_data": "product_{_ORM_PRODUCT_COUNTER}"}}'),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_ORM_PRODUCT_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_ORM_PRODUCT_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Handle preprocessed_name with StrProcessor after getting the name
    final_kwargs["preprocessed_name"] = kwargs.get("preprocessed_name", StrProcessor(final_kwargs["name"]).output)
    
    # Increment counter for next call
    _ORM_PRODUCT_COUNTER += 1
    
    return final_kwargs

def create_ORM_product(**kwargs) -> ProductSaModel:
    """
    Create a ProductSaModel ORM entity with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ProductSaModel ORM entity
    """
    product_kwargs = create_ORM_product_kwargs(**kwargs)
    return ProductSaModel(**product_kwargs)

# =============================================================================
# SOURCE/BRAND/CATEGORY DATA FACTORIES
# =============================================================================

def create_source_kwargs(**kwargs) -> Dict[str, Any]:
    """Create source kwargs for testing with simple deterministic IDs"""
    global _SOURCE_COUNTER
    
    defaults = {
        "id": f"test_source_{_SOURCE_COUNTER}",  # Simple deterministic ID
        "name": f"Test Source {_SOURCE_COUNTER}",
        "author_id": f"author_{(_SOURCE_COUNTER % 3) + 1}",
        "description": f"Test source {_SOURCE_COUNTER} description"
    }
    
    defaults.update(kwargs)
    _SOURCE_COUNTER += 1
    return defaults

def create_brand_kwargs(**kwargs) -> Dict[str, Any]:
    """Create brand kwargs for testing"""
    global _BRAND_COUNTER
    
    brands = ["TestBrand", "QualityFoods", "HealthyChoice", "NaturalPro", "FreshMarket"]
    brand_name = brands[(_BRAND_COUNTER - 1) % len(brands)]
    
    defaults = {
        "id": f"test_brand_{_BRAND_COUNTER}",  # Simple deterministic ID
        "name": f"{brand_name} {_BRAND_COUNTER}",
        "author_id": f"author_{(_BRAND_COUNTER % 3) + 1}",
        "description": f"Test brand {brand_name} description"
    }
    
    defaults.update(kwargs)
    _BRAND_COUNTER += 1
    return defaults

def create_category_kwargs(**kwargs) -> Dict[str, Any]:
    """Create category kwargs for testing"""
    global _CATEGORY_COUNTER
    
    categories = ["fruits", "vegetables", "grains", "proteins", "dairy", "beverages"]
    category_name = categories[(_CATEGORY_COUNTER - 1) % len(categories)]
    
    defaults = {
        "id": f"test_category_{_CATEGORY_COUNTER}",  # Simple deterministic ID  
        "name": f"{category_name.title()} {_CATEGORY_COUNTER}",
        "author_id": f"author_{(_CATEGORY_COUNTER % 3) + 1}",
        "description": f"Test category {category_name} description"
    }
    
    defaults.update(kwargs)
    _CATEGORY_COUNTER += 1
    return defaults

def create_required_sources_for_products() -> List[Dict[str, Any]]:
    """
    Create the minimal source entities required by product data factories.
    
    Products reference test_source_1, test_source_2, test_source_3 in rotation.
    This function creates exactly those source entities.
    
    Returns:
        List of source kwargs for the 3 required sources
    """
    sources = []
    for i in range(1, 4):  # test_source_1, test_source_2, test_source_3
        sources.append({
            "id": f"test_source_{i}",
            "name": f"Test Source {i}",
            "author_id": "test_author_1",
            "description": f"Required test source {i}"
        })
    return sources

# =============================================================================
# ORM SOURCE/BRAND/CATEGORY DATA FACTORIES
# =============================================================================

def create_ORM_source_kwargs(**kwargs) -> Dict[str, Any]:
    """Create ORM source kwargs for testing with simple deterministic IDs"""
    global _ORM_SOURCE_COUNTER
    
    final_kwargs = {
        "id": kwargs.get("id", f"orm_test_source_{_ORM_SOURCE_COUNTER}"),  # Simple deterministic ID
        "name": kwargs.get("name", f"ORM Test Source {_ORM_SOURCE_COUNTER}"),
        "author_id": kwargs.get("author_id", f"orm_author_{(_ORM_SOURCE_COUNTER % 3) + 1}"),
        "description": kwargs.get("description", f"ORM test source {_ORM_SOURCE_COUNTER} description"),
        "created_at": kwargs.get("created_at", datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=_ORM_SOURCE_COUNTER)),
        "updated_at": kwargs.get("updated_at", datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=_ORM_SOURCE_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1)
    }
    
    _ORM_SOURCE_COUNTER += 1
    return final_kwargs

def create_ORM_source(**kwargs) -> SourceSaModel:
    """Create a SourceSaModel ORM entity with deterministic data"""
    source_kwargs = create_ORM_source_kwargs(**kwargs)
    return SourceSaModel(**source_kwargs)

def create_ORM_brand_kwargs(**kwargs) -> Dict[str, Any]:
    """Create ORM brand kwargs for testing"""
    global _ORM_BRAND_COUNTER
    
    brands = ["ORMTestBrand", "ORMQualityFoods", "ORMHealthyChoice", "ORMNaturalPro", "ORMFreshMarket"]
    brand_name = brands[(_ORM_BRAND_COUNTER - 1) % len(brands)]
    
    final_kwargs = {
        "id": kwargs.get("id", f"orm_test_brand_{_ORM_BRAND_COUNTER}"),  # Simple deterministic ID
        "name": kwargs.get("name", f"{brand_name} {_ORM_BRAND_COUNTER}"),
        "author_id": kwargs.get("author_id", f"orm_author_{(_ORM_BRAND_COUNTER % 3) + 1}"),
        "description": kwargs.get("description", f"ORM test brand {brand_name} description"),
        "created_at": kwargs.get("created_at", datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=_ORM_BRAND_COUNTER)),
        "updated_at": kwargs.get("updated_at", datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=_ORM_BRAND_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1)
    }
    
    _ORM_BRAND_COUNTER += 1
    return final_kwargs

def create_ORM_brand(**kwargs) -> BrandSaModel:
    """Create a BrandSaModel ORM entity with deterministic data"""
    brand_kwargs = create_ORM_brand_kwargs(**kwargs)
    return BrandSaModel(**brand_kwargs)

def create_ORM_category_kwargs(**kwargs) -> Dict[str, Any]:
    """Create ORM category kwargs for testing"""
    global _ORM_CATEGORY_COUNTER
    
    categories = ["orm_fruits", "orm_vegetables", "orm_grains", "orm_proteins", "orm_dairy", "orm_beverages"]
    category_name = categories[(_ORM_CATEGORY_COUNTER - 1) % len(categories)]
    
    final_kwargs = {
        "id": kwargs.get("id", f"orm_test_category_{_ORM_CATEGORY_COUNTER}"),  # Simple deterministic ID  
        "name": kwargs.get("name", f"{category_name.title()} {_ORM_CATEGORY_COUNTER}"),
        "author_id": kwargs.get("author_id", f"orm_author_{(_ORM_CATEGORY_COUNTER % 3) + 1}"),
        "description": kwargs.get("description", f"ORM test category {category_name} description"),
        "created_at": kwargs.get("created_at", datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=_ORM_CATEGORY_COUNTER)),
        "updated_at": kwargs.get("updated_at", datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=_ORM_CATEGORY_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "type": kwargs.get("type", "category")  # Required for polymorphic classification
    }
    
    _ORM_CATEGORY_COUNTER += 1
    return final_kwargs

def create_ORM_category(**kwargs) -> CategorySaModel:
    """Create a CategorySaModel ORM entity with deterministic data"""
    category_kwargs = create_ORM_category_kwargs(**kwargs)
    return CategorySaModel(**category_kwargs)

def create_ORM_required_sources_for_products() -> List[Dict[str, Any]]:
    """
    Create the minimal ORM source entities required by ORM product data factories.
    
    ORM Products reference orm_test_source_1, orm_test_source_2, orm_test_source_3 in rotation.
    This function creates exactly those source entities.
    
    Returns:
        List of ORM source kwargs for the 3 required sources
    """
    sources = []
    for i in range(1, 4):  # orm_test_source_1, orm_test_source_2, orm_test_source_3
        sources.append({
            "id": f"orm_test_source_{i}",
            "name": f"ORM Test Source {i}",
            "author_id": "orm_test_author_1",
            "description": f"Required ORM test source {i}",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 1, 12, 0, 0),
            "discarded": False,
            "version": 1
        })
    return sources

# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

def get_ORM_product_filter_scenarios() -> List[Dict[str, Any]]:
    """
    Get ORM-specific predefined scenarios for testing product filtering logic.
    
    Similar to get_product_filter_scenarios() but uses ORM source IDs and ORM-compatible
    product kwargs that match the ORM model structure.
    
    Each scenario defines:
    - product_kwargs: Data for creating a test ORM product
    - filter: Filter conditions to apply
    - should_match: Whether the product should match the filter
    - description: Human-readable description of the test
    - skip_reason: (Optional) Why this test should be skipped if entities don't exist
    - requires_task: (Optional) What task needs to be completed to enable this test
    
    Returns:
        List of ORM product filtering test scenarios
    """
    return [
        {
            "scenario_id": "is_food_true",
            "product_kwargs": {"is_food": True, "name": "ORM Food Product"},
            "filter": {"is_food": True},
            "should_match": True,
            "description": "ORM Product with is_food=True should match is_food=True filter"
        },
        {
            "scenario_id": "is_food_false",
            "product_kwargs": {"is_food": False, "name": "ORM Non-Food Product"},
            "filter": {"is_food": True},
            "should_match": False,
            "description": "ORM Product with is_food=False should not match is_food=True filter"
        },
        {
            "scenario_id": "name_exact_match",
            "product_kwargs": {"name": "ORM Organic Apple"},
            "filter": {"name": "ORM Organic Apple"},
            "should_match": True,
            "description": "ORM Product with exact name match should work"
        },
        {
            "scenario_id": "name_no_match",
            "product_kwargs": {"name": "ORM Organic Apple"},
            "filter": {"name": "ORM Banana"},
            "should_match": False,
            "description": "ORM Product with different name should not match"
        },
        {
            "scenario_id": "barcode_match",
            "product_kwargs": {"barcode": "9876543210123"},
            "filter": {"barcode": "9876543210123"},
            "should_match": True,
            "description": "ORM Product with matching barcode should work"
        },
        {
            "scenario_id": "barcode_no_match",
            "product_kwargs": {"barcode": "9876543210123"},
            "filter": {"barcode": "1234567890987"},
            "should_match": False,
            "description": "ORM Product with different barcode should not match"
        },
        # TODO: Enable after Task 4.4.1 (Source filtering implementation)
        {
            "scenario_id": "source_match",
            "product_kwargs": {"source_id": "orm_test_source_1"},  # Use ORM source ID
            "filter": {"source": "ORM Test Source 1"},  # Note: filter maps to source.name
            "should_match": True,
            "description": "ORM Product should match by source name through join",
            "skip_reason": "Requires source filtering implementation (Task 4.4.1)",
            "requires_task": "4.4.1"
        },
        # TODO: Enable after Task 4.4.2 (Brand entities) and Task 4.4.3 (Brand repository)
        {
            "scenario_id": "brand_match",
            "product_kwargs": {"brand_id": "orm_brand_testbrand_1"},  # Use ORM brand ID
            "filter": {"brand": "ORMTestBrand 1"},  # Note: filter maps to brand.name
            "should_match": True,
            "description": "ORM Product should match by brand name through join",
            "skip_reason": "Requires brand entities and repository (Task 4.4.2-4.4.3)",
            "requires_task": "4.4.3"
        },
        # TODO: Enable after Task 4.4.2 (Category entities) and Task 4.4.3 (Category repository)
        {
            "scenario_id": "category_match",
            "product_kwargs": {"category_id": "orm_category_fruits_1"},  # Use ORM category ID
            "filter": {"category": "Orm_fruits 1"},  # Note: filter maps to category.name
            "should_match": True,
            "description": "ORM Product should match by category name through join",
            "skip_reason": "Requires category entities and repository (Task 4.4.2-4.4.3)",
            "requires_task": "4.4.3"
        },
        {
            "scenario_id": "multiple_filters_all_match",
            "product_kwargs": {
                "is_food": True,
                "name": "ORM Test Multi Filter Product",
                "source_id": "orm_test_source_1"  # Use ORM source ID
            },
            "filter": {
                "is_food": True,
                "name": "ORM Test Multi Filter Product"
            },
            "should_match": True,
            "description": "ORM Product should match when all filter conditions are met"
        },
        {
            "scenario_id": "multiple_filters_partial_match",
            "product_kwargs": {
                "is_food": True,
                "name": "ORM Test Multi Filter Product",
                "source_id": "orm_test_source_1"  # Use ORM source ID
            },
            "filter": {
                "is_food": True,
                "name": "ORM Different Name"
            },
            "should_match": False,
            "description": "ORM Product should not match when any filter condition fails"
        }
    ]

def get_product_filter_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing product filtering logic.
    
    Each scenario defines:
    - product_kwargs: Data for creating a test product
    - filter: Filter conditions to apply
    - should_match: Whether the product should match the filter
    - description: Human-readable description of the test
    - skip_reason: (Optional) Why this test should be skipped if entities don't exist
    - requires_task: (Optional) What task needs to be completed to enable this test
    
    Returns:
        List of product filtering test scenarios
    """
    return [
        {
            "scenario_id": "is_food_true",
            "product_kwargs": {"is_food": True, "name": "Food Product"},
            "filter": {"is_food": True},
            "should_match": True,
            "description": "Product with is_food=True should match is_food=True filter"
        },
        {
            "scenario_id": "is_food_false",
            "product_kwargs": {"is_food": False, "name": "Non-Food Product"},
            "filter": {"is_food": True},
            "should_match": False,
            "description": "Product with is_food=False should not match is_food=True filter"
        },
        {
            "scenario_id": "name_exact_match",
            "product_kwargs": {"name": "Organic Apple"},
            "filter": {"name": "Organic Apple"},
            "should_match": True,
            "description": "Product with exact name match should work"
        },
        {
            "scenario_id": "name_no_match",
            "product_kwargs": {"name": "Organic Apple"},
            "filter": {"name": "Banana"},
            "should_match": False,
            "description": "Product with different name should not match"
        },
        {
            "scenario_id": "barcode_match",
            "product_kwargs": {"barcode": "1234567890123"},
            "filter": {"barcode": "1234567890123"},
            "should_match": True,
            "description": "Product with matching barcode should work"
        },
        {
            "scenario_id": "barcode_no_match",
            "product_kwargs": {"barcode": "1234567890123"},
            "filter": {"barcode": "9876543210987"},
            "should_match": False,
            "description": "Product with different barcode should not match"
        },
        # TODO: Enable after Task 4.4.1 (Source filtering implementation)
        {
            "scenario_id": "source_match",
            "product_kwargs": {"source_id": "test_source_1"},
            "filter": {"source": "Test Source 1"},  # Note: filter maps to source.name
            "should_match": True,
            "description": "Product should match by source name through join",
            "skip_reason": "Requires source filtering implementation (Task 4.4.1)",
            "requires_task": "4.4.1"
        },
        # TODO: Enable after Task 4.4.2 (Brand entities) and Task 4.4.3 (Brand repository)
        {
            "scenario_id": "brand_match",
            "product_kwargs": {"brand_id": "brand_testbrand_1"},
            "filter": {"brand": "TestBrand 1"},  # Note: filter maps to brand.name
            "should_match": True,
            "description": "Product should match by brand name through join",
            "skip_reason": "Requires brand entities and repository (Task 4.4.2-4.4.3)",
            "requires_task": "4.4.3"
        },
        # TODO: Enable after Task 4.4.2 (Category entities) and Task 4.4.3 (Category repository)
        {
            "scenario_id": "category_match",
            "product_kwargs": {"category_id": "category_fruits_1"},
            "filter": {"category": "Fruits 1"},  # Note: filter maps to category.name
            "should_match": True,
            "description": "Product should match by category name through join",
            "skip_reason": "Requires category entities and repository (Task 4.4.2-4.4.3)",
            "requires_task": "4.4.3"
        },
        {
            "scenario_id": "multiple_filters_all_match",
            "product_kwargs": {
                "is_food": True,
                "name": "Test Multi Filter Product",
                "source_id": "test_source_1"  # Using existing test source
            },
            "filter": {
                "is_food": True,
                "name": "Test Multi Filter Product"
            },
            "should_match": True,
            "description": "Product should match when all filter conditions are met"
        },
        {
            "scenario_id": "multiple_filters_partial_match",
            "product_kwargs": {
                "is_food": True,
                "name": "Test Multi Filter Product",
                "source_id": "test_source_1"  # Using existing test source
            },
            "filter": {
                "is_food": True,
                "name": "Different Name"
            },
            "should_match": False,
            "description": "Product should not match when any filter condition fails"
        }
    ]

def get_similarity_search_scenarios() -> List[Dict[str, Any]]:
    """Get scenarios for testing similarity search functionality"""
    return [
        {
            "scenario_id": "exact_name_match",
            "products": [
                {"name": "Organic Apple Juice"},
                {"name": "Regular Apple Juice"},
                {"name": "Orange Juice"}
            ],
            "search_term": "Organic Apple Juice",
            "expected_first": "Organic Apple Juice",
            "expected_matches": ["Organic Apple Juice"],  # List of names, not count
            "description": "Exact name match should be first result"
        },
        {
            "scenario_id": "partial_match",
            "products": [
                {"name": "Apple Juice"},
                {"name": "Apple Sauce"},
                {"name": "Orange Juice"}
            ],
            "search_term": "Apple",
            "expected_count_gte": 2,
            "expected_matches": ["Apple Juice", "Apple Sauce"],  # List of names that should match
            "description": "Partial matches should return multiple results"
        },
        {
            "scenario_id": "first_word_match",
            "products": [
                {"name": "Apple Juice"},
                {"name": "Apple Sauce"},
                {"name": "Banana Juice"}
            ],
            "search_term": "Apple Crisp",
            "expected_count_gte": 2,
            "expected_matches": ["Apple Juice", "Apple Sauce"],  # List of names that should match
            "description": "First word matches should be found"
        }
    ]

def get_hierarchical_filter_scenarios() -> List[Dict[str, Any]]:
    """Get scenarios for testing hierarchical filtering (parent_category -> category -> brand)"""
    # NOTE: These scenarios require foreign key entities to be created first
    # TODO: Enable these tests after completing task 4.4.2 (Brand/Category entities) and 4.4.3 (Classification repositories)
    return [
        {
            "scenario_id": "parent_category_only",
            "requires_entities": ["parent_category", "category", "brand"],  # Entities that must exist
            "requires_task": "4.4.3",  # Task that creates these entities
            "products": [
                {
                    "parent_category_id": "parent_cat_1",
                    "category_id": "cat_1_a",
                    "brand_id": "brand_1"
                },
                {
                    "parent_category_id": "parent_cat_1", 
                    "category_id": "cat_1_b",
                    "brand_id": "brand_2"
                },
                {
                    "parent_category_id": "parent_cat_2",
                    "category_id": "cat_2_a", 
                    "brand_id": "brand_3"
                }
            ],
            "filter": {"parent_category": "Parent Category 1"},
            "expected_count": 2,
            "description": "Parent category filter should return all products in that parent category",
            "skip_reason": "Requires parent_category, category, and brand entities (Task 4.4.3)"
        },
        {
            "scenario_id": "parent_and_category",
            "requires_entities": ["parent_category", "category", "brand"],
            "requires_task": "4.4.3",
            "products": [
                {
                    "parent_category_id": "parent_cat_1",
                    "category_id": "cat_1_a",
                    "brand_id": "brand_1"
                },
                {
                    "parent_category_id": "parent_cat_1",
                    "category_id": "cat_1_b", 
                    "brand_id": "brand_2"
                }
            ],
            "filter": {
                "parent_category": "Parent Category 1",
                "category": "Category 1A"
            },
            "expected_count": 1,
            "description": "Parent + category filter should narrow results",
            "skip_reason": "Requires parent_category, category, and brand entities (Task 4.4.3)"
        }
    ]

def get_performance_test_scenarios() -> List[Dict[str, Any]]:
    """Get scenarios for performance testing with different dataset sizes"""
    return [
        {
            "scenario_id": "small_dataset_basic_query",
            "entity_count": 100,
            "operation": "basic_query",
            "max_duration_seconds": 1.0,
            "description": "Basic query on 100 products should complete in < 1.0s"
        },
        {
            "scenario_id": "medium_dataset_basic_query",
            "entity_count": 500,
            "operation": "basic_query", 
            "max_duration_seconds": 2.0,
            "description": "Basic query on 500 products should complete in < 2.0s"
        },
        {
            "scenario_id": "large_dataset_basic_query",
            "entity_count": 1000,
            "operation": "basic_query",
            "max_duration_seconds": 3.0,
            "description": "Basic query on 1000 products should complete in < 3.0s"
        },
        {
            "scenario_id": "small_dataset_similarity_search",
            "entity_count": 100,
            "operation": "similarity_search",
            "max_duration_seconds": 2.0,
            "description": "Similarity search on 100 products should complete in < 2.0s"
        },
        {
            "scenario_id": "medium_dataset_similarity_search",
            "entity_count": 500,
            "operation": "similarity_search",
            "max_duration_seconds": 5.0,
            "description": "Similarity search on 500 products should complete in < 5.0s"
        },
        {
            "scenario_id": "small_dataset_complex_filtering",
            "entity_count": 100,
            "operation": "complex_filtering",
            "max_duration_seconds": 1.5,
            "description": "Complex filtering on 100 products should complete in < 1.5s"
        },
        {
            "scenario_id": "medium_dataset_complex_filtering",
            "entity_count": 500,
            "operation": "complex_filtering",
            "max_duration_seconds": 3.0,
            "description": "Complex filtering on 500 products should complete in < 3.0s"
        }
    ]

# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_organic_product(**kwargs) -> Product:
    """Create an organic product with typical organic characteristics"""
    organic_kwargs = {
        "name": "Organic Apple", 
        "ingredients": "organic ingredient1, organic ingredient2",
        "score": Score(final=0.9, ingredients=0.95, nutrients=0.85),
        # No specific foreign keys - let base factory handle with None values
    }
    organic_kwargs.update(kwargs)
    return create_product(**organic_kwargs)

def create_processed_product(**kwargs) -> Product:
    """Create a highly processed product"""
    processed_kwargs = {
        "name": "Processed Snack Food",
        "ingredients": "processed ingredient1, artificial flavor, preservatives",
        "score": Score(final=0.3, ingredients=0.2, nutrients=0.4),
        # No specific foreign keys - let base factory handle with None values  
    }
    processed_kwargs.update(kwargs)
    return create_product(**processed_kwargs)

def create_high_protein_product(**kwargs) -> Product:
    """Create a high-protein product"""
    high_protein_kwargs = {
        "name": "High Protein Shake",
        "nutri_facts": NutriFacts(
            calories=150,
            protein=30.0,  # High protein
            carbohydrate=5.0,
            total_fat=2.0
        ),
        "ingredients": "whey protein, vitamins, minerals"
    }
    high_protein_kwargs.update(kwargs)
    return create_product(**high_protein_kwargs)

def create_beverage_product(**kwargs) -> Product:
    """Create a beverage product"""
    beverage_kwargs = {
        "name": "Natural Fruit Juice",
        "package_size": 1000.0,
        "package_size_unit": "ml",
        "liters_per_kg": 1.0,  # Liquid product
    }
    beverage_kwargs.update(kwargs)
    return create_product(**beverage_kwargs)

def create_product_with_barcode(**kwargs) -> Product:
    """Create a product that definitely has a barcode"""
    barcode_kwargs = {
        "barcode": "1234567890123",  # Ensure barcode exists
        "name": "Retail Product with Barcode"
    }
    barcode_kwargs.update(kwargs)
    return create_product(**barcode_kwargs)

# =============================================================================
# ORM SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_ORM_organic_product(**kwargs) -> ProductSaModel:
    """Create an ORM organic product with typical organic characteristics"""
    organic_kwargs = {
        "name": "ORM Organic Apple", 
        "ingredients": "orm organic ingredient1, orm organic ingredient2",
        "final_score": 0.9,
        "ingredients_score": 0.95,
        "nutrients_score": 0.85,
        # No specific foreign keys - let base factory handle with None values
    }
    organic_kwargs.update(kwargs)
    return create_ORM_product(**organic_kwargs)

def create_ORM_processed_product(**kwargs) -> ProductSaModel:
    """Create an ORM highly processed product"""
    processed_kwargs = {
        "name": "ORM Processed Snack Food",
        "ingredients": "orm processed ingredient1, orm artificial flavor, orm preservatives",
        "final_score": 0.3,
        "ingredients_score": 0.2,
        "nutrients_score": 0.4,
        # No specific foreign keys - let base factory handle with None values  
    }
    processed_kwargs.update(kwargs)
    return create_ORM_product(**processed_kwargs)

def create_ORM_high_protein_product(**kwargs) -> ProductSaModel:
    """Create an ORM high-protein product"""
    high_protein_kwargs = {
        "name": "ORM High Protein Shake",
        "calories": 150.0,
        "protein": 30.0,  # High protein
        "carbohydrate": 5.0,
        "total_fat": 2.0,
        "ingredients": "orm whey protein, orm vitamins, orm minerals"
    }
    high_protein_kwargs.update(kwargs)
    return create_ORM_product(**high_protein_kwargs)

def create_ORM_beverage_product(**kwargs) -> ProductSaModel:
    """Create an ORM beverage product"""
    beverage_kwargs = {
        "name": "ORM Natural Fruit Juice",
        "package_size": 1000.0,
        "package_size_unit": "ml",
        "liters_per_kg": 1.0,  # Liquid product
    }
    beverage_kwargs.update(kwargs)
    return create_ORM_product(**beverage_kwargs)

def create_ORM_product_with_barcode(**kwargs) -> ProductSaModel:
    """Create an ORM product that definitely has a barcode"""
    barcode_kwargs = {
        "barcode": "9876543210123",  # Ensure barcode exists (different from domain version)
        "name": "ORM Retail Product with Barcode"
    }
    barcode_kwargs.update(kwargs)
    return create_ORM_product(**barcode_kwargs)

# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_test_dataset(product_count: int = 100) -> Dict[str, Any]:
    """Create a dataset of products for performance testing"""
    products = []
    
    for i in range(product_count):
        product = create_product()
        products.append(product)
    
    return {
        "products": products,
        "count": len(products)
    }

def create_products_with_hierarchy(count: int = 10) -> List[Product]:
    """Create products with realistic hierarchical relationships"""
    products = []
    
    # Create products across different hierarchies
    hierarchies = [
        ("parent_fruits", "category_apples", "brand_orchard"),
        ("parent_fruits", "category_bananas", "brand_tropical"),
        ("parent_vegetables", "category_leafy", "brand_fresh"),
        ("parent_grains", "category_wheat", "brand_healthy")
    ]
    
    for i in range(count):
        hierarchy = hierarchies[i % len(hierarchies)]
        parent_cat, category, brand = hierarchy
        
        product = create_product(
            parent_category_id=f"{parent_cat}_{i // len(hierarchies) + 1}",
            category_id=f"{category}_{i // len(hierarchies) + 1}",
            brand_id=f"{brand}_{i // len(hierarchies) + 1}"
        )
        products.append(product)
    
    return products

# =============================================================================
# ORM HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_ORM_test_dataset(product_count: int = 100) -> Dict[str, Any]:
    """Create an ORM dataset of products for performance testing"""
    products = []
    
    for i in range(product_count):
        product = create_ORM_product()
        products.append(product)
    
    return {
        "products": products,
        "count": len(products)
    }

def create_ORM_products_with_hierarchy(count: int = 10) -> List[ProductSaModel]:
    """Create ORM products with realistic hierarchical relationships"""
    products = []
    
    # Create products across different hierarchies
    hierarchies = [
        ("orm_parent_fruits", "orm_category_apples", "orm_brand_orchard"),
        ("orm_parent_fruits", "orm_category_bananas", "orm_brand_tropical"),
        ("orm_parent_vegetables", "orm_category_leafy", "orm_brand_fresh"),
        ("orm_parent_grains", "orm_category_wheat", "orm_brand_healthy")
    ]
    
    for i in range(count):
        hierarchy = hierarchies[i % len(hierarchies)]
        parent_cat, category, brand = hierarchy
        
        product = create_ORM_product(
            parent_category_id=f"{parent_cat}_{i // len(hierarchies) + 1}",
            category_id=f"{category}_{i // len(hierarchies) + 1}",
            brand_id=f"{brand}_{i // len(hierarchies) + 1}"
        )
        products.append(product)
    
    return products 