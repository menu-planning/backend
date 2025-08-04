"""
Test fixtures for API schema validation tests.
"""

import pytest
from typing import Dict, Any, List, Set
from datetime import datetime



@pytest.fixture
def valid_collection_data() -> List[Dict[str, Any]]:
    """Valid collection data for testing UniqueCollectionAdapter."""
    return [
        {"id": "1", "name": "Item 1", "value": 10},
        {"id": "2", "name": "Item 2", "value": 20},
        {"id": "3", "name": "Item 3", "value": 30},
    ]


@pytest.fixture
def duplicate_collection_data() -> List[Dict[str, Any]]:
    """Collection data with duplicates for testing validation."""
    return [
        {"id": "1", "name": "Item 1", "value": 10},
        {"id": "2", "name": "Item 2", "value": 20},
        {"id": "1", "name": "Item 1 Duplicate", "value": 15},  # Duplicate ID
    ]


@pytest.fixture
def valid_percentage_data() -> List[float]:
    """Valid percentage values that sum to 100."""
    return [30.5, 25.0, 44.5]


@pytest.fixture
def invalid_percentage_data() -> List[float]:
    """Invalid percentage values that don't sum to 100."""
    return [30.0, 25.0, 50.0]  # Sums to 105


@pytest.fixture
def edge_case_percentage_data() -> List[float]:
    """Edge case percentage values (exactly 100 with floating point)."""
    return [33.333333, 33.333333, 33.333334]


@pytest.fixture
def nested_object_data() -> Dict[str, Any]:
    """Complex nested object data for testing hierarchical schemas."""
    return {
        "id": "meal-123",
        "name": "Test Meal",
        "author_id": "user-456",
        "recipes": [
            {
                "id": "recipe-1",
                "name": "Recipe 1",
                "ingredients": [
                    {"name": "Ingredient 1", "quantity": 100, "unit": "grams"},
                    {"name": "Ingredient 2", "quantity": 50, "unit": "ml"},
                ]
            },
            {
                "id": "recipe-2", 
                "name": "Recipe 2",
                "ingredients": [
                    {"name": "Ingredient 3", "quantity": 200, "unit": "grams"},
                ]
            }
        ],
        "tags": [
            {"key": "cuisine", "value": "Italian", "author_id": "user-456", "type": "category"},
            {"key": "diet", "value": "vegetarian", "author_id": "user-456", "type": "restriction"},
        ],
        "description": "A test meal with multiple recipes",
        "like": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.fixture
def schema_field_mapping_examples() -> Dict[str, Dict[str, Set[str]]]:
    """Examples of field mappings between Domain/API/ORM for different scenarios."""
    return {
        "perfect_match": {
            "domain": {"id", "name", "description", "created_at"},
            "api": {"id", "name", "description", "created_at"},
            "orm": {"id", "name", "description", "created_at"},
        },
        "api_extra_validation": {
            "domain": {"id", "name", "value"},
            "api": {"id", "name", "value", "validation_field"},  # Extra validation field
            "orm": {"id", "name", "value"},
        },
        "orm_extra_metadata": {
            "domain": {"id", "name", "content"},
            "api": {"id", "name", "content"},
            "orm": {"id", "name", "content", "preprocessed_content", "search_vector"},  # Extra ORM fields
        },
        "computed_fields": {
            "domain": {"id", "values", "total", "average"},  # Computed properties
            "api": {"id", "values"},  # Only serializable fields
            "orm": {"id", "values", "cached_total"},  # Cached computed values
        },
        "relationship_differences": {
            "domain": {"id", "items", "owner"},  # Direct relationships
            "api": {"id", "item_ids", "owner_id"},  # ID references only  
            "orm": {"id", "items", "owner_id"},  # Mixed relationships and IDs
        }
    }


@pytest.fixture
def mock_domain_class():
    """Mock domain class for testing field extraction."""
    class MockDomain:
        def __init__(self, *, id: str, name: str, value: int, optional: str | None = None):
            self.id = id
            self.name = name
            self.value = value
            self.optional = optional
            
        @property
        def computed_field(self) -> str:
            return f"{self.name}_{self.value}"
            
        @property  
        def another_property(self) -> int:
            return self.value * 2
            
    return MockDomain


@pytest.fixture
def mock_api_class():
    """Mock API class for testing field extraction."""
    from pydantic import BaseModel
    
    class MockApiSchema(BaseModel):
        id: str
        name: str
        value: int
        optional: str | None = None
        validation_only: str | None = None  # API-only validation field
        
    return MockApiSchema


@pytest.fixture
def mock_orm_class():
    """Mock ORM class for testing field extraction."""
    from sqlalchemy import Column, String, Integer
    from src.db.base import SaBase
    
    class MockOrmModel(SaBase):
        __tablename__ = "mock_table"
        
        id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        value = Column(Integer, nullable=False)
        optional = Column(String, nullable=True)
        orm_metadata = Column(String, nullable=True)  # ORM-only field
        
    return MockOrmModel


@pytest.fixture
def conversion_test_data():
    """Test data for conversion method validation."""
    return {
        "valid_minimal": {
            "id": "test-123",
            "name": "Test Item",
        },
        "valid_complete": {
            "id": "test-456", 
            "name": "Complete Test Item",
            "description": "A complete test item with all fields",
            "value": 42,
            "tags": ["tag1", "tag2"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        },
        "invalid_missing_required": {
            "name": "Missing ID",  # Missing required ID field
        },
        "invalid_wrong_type": {
            "id": "test-789",
            "name": 123,  # Wrong type - should be string
        },
        "edge_case_empty_collections": {
            "id": "test-000",
            "name": "Empty Collections",
            "tags": [],
            "items": [],
        }
    }


@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing."""
    return {
        "small_dataset": [{"id": f"item-{i}", "name": f"Item {i}"} for i in range(10)],
        "medium_dataset": [{"id": f"item-{i}", "name": f"Item {i}"} for i in range(100)],
        "large_dataset": [{"id": f"item-{i}", "name": f"Item {i}"} for i in range(1000)],
    }


@pytest.fixture
def error_scenario_data():
    """Data designed to trigger various error conditions."""
    return {
        "circular_reference": {
            # This would create circular references if not handled properly
            "id": "circular-1",
            "name": "Circular Item",
            "parent_id": "circular-1",  # References itself
        },
        "deep_nesting": {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": "deep_value"
                        }
                    }
                }
            }
        },
        "unicode_and_special_chars": {
            "id": "unicode-test",
            "name": "Test with émojis 🚀 and spëcial chars àáâãäå",
            "description": "Testing unicode: αβγδε, 中文, العربية, עברית",
        },
        "boundary_values": {
            "id": "boundary-test",
            "percentage": 100.0,  # Exact boundary
            "large_number": 999999999999999,
            "tiny_number": 0.000000001,
            "empty_string": "",
            "null_value": None,
        }
    } 