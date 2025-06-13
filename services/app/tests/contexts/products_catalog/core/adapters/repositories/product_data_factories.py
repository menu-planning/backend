"""
Data factories for ProductRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness  
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different product types

All data follows the exact structure of Product domain entities and their relationships.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import uuid
from decimal import Decimal

from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import IsFoodVotes
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_PRODUCT_COUNTER = 1
_SOURCE_COUNTER = 1
_BRAND_COUNTER = 1
_CATEGORY_COUNTER = 1

def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _PRODUCT_COUNTER, _SOURCE_COUNTER, _BRAND_COUNTER, _CATEGORY_COUNTER
    _PRODUCT_COUNTER = 1
    _SOURCE_COUNTER = 1
    _BRAND_COUNTER = 1
    _CATEGORY_COUNTER = 1

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
        
    Raises:
        ValueError: If invalid attribute combinations are provided
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
    
    # Validation logic to ensure required attributes
    required_fields = ["id", "source_id", "name"]
    for field in required_fields:
        if not defaults.get(field):
            raise ValueError(f"Required field '{field}' cannot be empty")
    
    # Validate source_id format
    if not isinstance(defaults["source_id"], str) or not defaults["source_id"]:
        raise ValueError("source_id must be a non-empty string")
    
    # Validate is_food is boolean
    if defaults.get("is_food") is not None and not isinstance(defaults["is_food"], bool):
        raise ValueError("is_food must be a boolean or None")
    
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
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

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