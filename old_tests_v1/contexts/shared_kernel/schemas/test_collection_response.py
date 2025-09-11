"""
Unit tests for collection response utilities.

Tests the pagination utilities and CollectionResponse integration patterns
used by Lambda endpoints for consistent collection handling.
"""

import pytest
import time
import json
from typing import Dict, Any
from pydantic import BaseModel, TypeAdapter

from src.contexts.shared_kernel.schemas.collection_response import (
    create_paginated_response,
    extract_pagination_from_query,
    calculate_database_offset,
    CollectionResponse
)


# Mock API model for performance testing
class MockApiItem(BaseModel):
    """Mock API model for performance testing."""
    id: str
    name: str
    description: str
    value: int
    metadata: dict[str, Any]


class TestCreatePaginatedResponse:
    """Test cases for create_paginated_response function."""
    
    def test_create_paginated_response_basic(self):
        """Test basic pagination response creation."""
        items = [{"id": "1", "name": "item1"}, {"id": "2", "name": "item2"}]
        
        response = create_paginated_response(
            items=items,
            total_count=100,
            page_size=10,
            current_page=1
        )
        
        assert isinstance(response, CollectionResponse)
        assert response.items == items
        assert response.total_count == 100
        assert response.page_size == 10
        assert response.current_page == 1
        assert response.has_next is True  # 1 * 10 < 100
        assert response.has_previous is False  # page 1
        assert response.total_pages == 10  # 100 / 10
    
    def test_create_paginated_response_middle_page(self):
        """Test pagination for middle page."""
        items = [{"id": "21", "name": "item21"}]
        
        response = create_paginated_response(
            items=items,
            total_count=50,
            page_size=10,
            current_page=3
        )
        
        assert response.current_page == 3
        assert response.has_next is True  # 3 * 10 < 50
        assert response.has_previous is True  # page > 1
        assert response.total_pages == 5  # 50 / 10
    
    def test_create_paginated_response_last_page(self):
        """Test pagination for last page."""
        items = [{"id": "45", "name": "item45"}]
        
        response = create_paginated_response(
            items=items,
            total_count=45,
            page_size=10,
            current_page=5
        )
        
        assert response.current_page == 5
        assert response.has_next is False  # 5 * 10 >= 45
        assert response.has_previous is True  # page > 1
        assert response.total_pages == 5  # ceil(45 / 10)
    
    def test_create_paginated_response_empty_collection(self):
        """Test pagination with empty collection."""
        response = create_paginated_response(
            items=[],
            total_count=0,
            page_size=10,
            current_page=1
        )
        
        assert response.items == []
        assert response.total_count == 0
        assert response.has_next is False
        assert response.has_previous is False
        assert response.total_pages == 0
    
    def test_create_paginated_response_single_page(self):
        """Test pagination with all items on single page."""
        items = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        
        response = create_paginated_response(
            items=items,
            total_count=3,
            page_size=10,
            current_page=1
        )
        
        assert response.total_count == 3
        assert response.has_next is False  # 1 * 10 >= 3
        assert response.has_previous is False
        assert response.total_pages == 1
    
    def test_create_paginated_response_custom_page_size(self):
        """Test pagination with custom page size."""
        items = [{"id": str(i)} for i in range(25)]
        
        response = create_paginated_response(
            items=items,
            total_count=150,
            page_size=25,
            current_page=2
        )
        
        assert response.page_size == 25
        assert response.current_page == 2
        assert response.has_next is True  # 2 * 25 < 150
        assert response.has_previous is True
        assert response.total_pages == 6  # 150 / 25


class TestExtractPaginationFromQuery:
    """Test cases for extract_pagination_from_query function."""
    
    def test_extract_pagination_defaults(self):
        """Test pagination extraction with no parameters."""
        query_params: dict[str, Any] = {}
        
        page, page_size = extract_pagination_from_query(query_params)
        
        assert page == 1
        assert page_size == 50  # default
    
    def test_extract_pagination_valid_params(self):
        """Test pagination extraction with valid parameters."""
        query_params = {
            "page": "3",
            "page_size": "25"
        }
        
        page, page_size = extract_pagination_from_query(query_params)
        
        assert page == 3
        assert page_size == 25
    
    def test_extract_pagination_integer_params(self):
        """Test pagination extraction with integer parameters."""
        query_params = {
            "page": 5,
            "page_size": 100
        }
        
        page, page_size = extract_pagination_from_query(query_params)
        
        assert page == 5
        assert page_size == 100
    
    def test_extract_pagination_invalid_page(self):
        """Test pagination extraction with invalid page (negative/zero)."""
        query_params = {
            "page": "0",
            "page_size": "20"
        }
        
        page, page_size = extract_pagination_from_query(query_params)
        
        assert page == 1  # minimum page is 1
        assert page_size == 20
        
        # Test negative page
        query_params["page"] = "-5"
        page, page_size = extract_pagination_from_query(query_params)
        assert page == 1
    
    def test_extract_pagination_invalid_page_size(self):
        """Test pagination extraction with invalid page size."""
        query_params = {
            "page": "2",
            "page_size": "0"
        }
        
        page, page_size = extract_pagination_from_query(query_params)
        
        assert page == 2
        assert page_size == 1  # minimum page_size is 1
    
    def test_extract_pagination_exceeds_max_page_size(self):
        """Test pagination extraction with page size exceeding maximum."""
        query_params = {
            "page": "1",
            "page_size": "500"  # exceeds default max of 200
        }
        
        page, page_size = extract_pagination_from_query(query_params)
        
        assert page == 1
        assert page_size == 200  # capped at max
    
    def test_extract_pagination_custom_defaults(self):
        """Test pagination extraction with custom default values."""
        query_params: dict[str, Any] = {}
        
        page, page_size = extract_pagination_from_query(
            query_params,
            default_page_size=25,
            max_page_size=100
        )
        
        assert page == 1
        assert page_size == 25  # custom default
    
    def test_extract_pagination_custom_max(self):
        """Test pagination extraction with custom maximum."""
        query_params = {
            "page_size": "150"
        }
        
        page, page_size = extract_pagination_from_query(
            query_params,
            max_page_size=100
        )
        
        assert page_size == 100  # capped at custom max


class TestCalculateDatabaseOffset:
    """Test cases for calculate_database_offset function."""
    
    def test_calculate_offset_first_page(self):
        """Test offset calculation for first page."""
        offset = calculate_database_offset(page=1, page_size=10)
        assert offset == 0  # (1 - 1) * 10
    
    def test_calculate_offset_second_page(self):
        """Test offset calculation for second page."""
        offset = calculate_database_offset(page=2, page_size=10)
        assert offset == 10  # (2 - 1) * 10
    
    def test_calculate_offset_various_page_sizes(self):
        """Test offset calculation with various page sizes."""
        # Page 3, page size 25
        offset = calculate_database_offset(page=3, page_size=25)
        assert offset == 50  # (3 - 1) * 25
        
        # Page 5, page size 100
        offset = calculate_database_offset(page=5, page_size=100)
        assert offset == 400  # (5 - 1) * 100
    
    def test_calculate_offset_invalid_page(self):
        """Test offset calculation with invalid page numbers."""
        # Page 0 should be treated as page 1
        offset = calculate_database_offset(page=0, page_size=10)
        assert offset == 0  # max(1, 0) = 1, (1 - 1) * 10 = 0
        
        # Negative page should be treated as page 1
        offset = calculate_database_offset(page=-5, page_size=10)
        assert offset == 0  # max(1, -5) = 1, (1 - 1) * 10 = 0


class TestCollectionResponseIntegration:
    """Test integration with CollectionResponse schema."""
    
    def test_collection_response_type_validation(self):
        """Test that create_paginated_response returns valid CollectionResponse."""
        items = [{"test": "data"}]
        
        response = create_paginated_response(
            items=items,
            total_count=1,
            page_size=10,
            current_page=1
        )
        
        # Verify it's a valid CollectionResponse instance
        assert isinstance(response, CollectionResponse)
        
        # Test serialization works
        data = response.model_dump()
        assert data["items"] == items
        assert data["total_count"] == 1
        assert data["page_size"] == 10
        assert data["current_page"] == 1
        assert data["has_next"] is False
        assert data["has_previous"] is False
        
        # Test JSON serialization
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        assert "total_count" in json_str
    
    def test_complete_pagination_workflow(self):
        """Test complete pagination workflow from query params to response."""
        # Simulate Lambda event query parameters
        query_params = {
            "page": "2",
            "page_size": "10"
        }
        
        # Extract pagination
        page, page_size = extract_pagination_from_query(query_params)
        
        # Calculate database offset
        offset = calculate_database_offset(page, page_size)
        
        # Simulate fetched data
        mock_items = [{"id": str(i + offset)} for i in range(page_size)]
        total_count = 45
        
        # Create paginated response
        response = create_paginated_response(
            items=mock_items,
            total_count=total_count,
            page_size=page_size,
            current_page=page
        )
        
        # Verify complete workflow
        assert offset == 10  # (2 - 1) * 10
        assert len(response.items) == 10
        assert response.current_page == 2
        assert response.total_count == 45
        assert response.has_next is True  # 2 * 10 < 45
        assert response.has_previous is True  # page > 1
        assert response.total_pages == 5  # ceil(45 / 10)


class TestSerializationPerformance:
    """Performance tests comparing TypeAdapter vs individual serialization."""
    
    @pytest.fixture
    def mock_items_small(self):
        """Create small dataset (50 items) for performance testing."""
        return [
            MockApiItem(
                id=f"item_{i}",
                name=f"Item {i}",
                description=f"Description for item {i}",
                value=i * 10,
                metadata={"index": i, "category": f"cat_{i % 5}", "active": i % 2 == 0}
            )
            for i in range(50)
        ]
    
    @pytest.fixture
    def mock_items_large(self):
        """Create large dataset (1000 items) for performance testing."""
        return [
            MockApiItem(
                id=f"item_{i}",
                name=f"Item {i}",
                description=f"Description for item {i}" * 3,  # Longer descriptions
                value=i * 10,
                metadata={
                    "index": i, 
                    "category": f"cat_{i % 10}", 
                    "active": i % 2 == 0,
                    "tags": [f"tag_{j}" for j in range(i % 5 + 1)],
                    "score": float(i * 0.1)
                }
            )
            for i in range(1000)
        ]
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Helper to measure execution time."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time
    
    def serialize_with_typeadapter(self, items: list[MockApiItem]) -> tuple[str, float]:
        """Serialize using TypeAdapter approach."""
        # Create TypeAdapter (this would be done once at module level in real usage)
        adapter = TypeAdapter(list[MockApiItem])
        
        def serialize():
            return adapter.dump_json(items).decode('utf-8')
        
        result, execution_time = self.measure_execution_time(serialize)
        return result, execution_time
    
    def serialize_individually(self, items: list[MockApiItem]) -> tuple[str, float]:
        """Serialize using individual model_dump_json approach."""
        def serialize():
            # Serialize each item individually and combine
            serialized_items = [item.model_dump_json() for item in items]
            # Aggregate into JSON array format
            return '[' + ','.join(serialized_items) + ']'
        
        result, execution_time = self.measure_execution_time(serialize)
        return result, execution_time
    
    def serialize_with_model_dump(self, items: list[MockApiItem]) -> tuple[str, float]:
        """Serialize using model_dump approach and manual JSON encoding."""
        def serialize():
            # Convert to dicts first, then JSON encode
            item_dicts = [item.model_dump() for item in items]
            return json.dumps(item_dicts)
        
        result, execution_time = self.measure_execution_time(serialize)
        return result, execution_time
    
    def test_serialization_correctness(self, mock_items_small):
        """Verify all serialization methods produce equivalent results."""
        typeadapter_result, _ = self.serialize_with_typeadapter(mock_items_small)
        individual_result, _ = self.serialize_individually(mock_items_small)
        model_dump_result, _ = self.serialize_with_model_dump(mock_items_small)
        
        # Parse back to Python objects for comparison
        typeadapter_data = json.loads(typeadapter_result)
        individual_data = json.loads(individual_result)
        model_dump_data = json.loads(model_dump_result)
        
        # All should produce the same data structure
        assert typeadapter_data == individual_data == model_dump_data
        assert len(typeadapter_data) == 50
    
    def test_performance_small_dataset(self, mock_items_small):
        """Compare performance on small dataset (50 items)."""
        # Run multiple iterations for more reliable timing
        iterations = 10
        
        typeadapter_times = []
        individual_times = []
        model_dump_times = []
        
        for _ in range(iterations):
            _, ta_time = self.serialize_with_typeadapter(mock_items_small)
            _, ind_time = self.serialize_individually(mock_items_small)
            _, md_time = self.serialize_with_model_dump(mock_items_small)
            
            typeadapter_times.append(ta_time)
            individual_times.append(ind_time)
            model_dump_times.append(md_time)
        
        # Calculate averages
        avg_typeadapter = sum(typeadapter_times) / iterations
        avg_individual = sum(individual_times) / iterations  
        avg_model_dump = sum(model_dump_times) / iterations
        
        print(f"\n=== SMALL DATASET (50 items) PERFORMANCE ===")
        print(f"TypeAdapter:      {avg_typeadapter:.6f}s (avg over {iterations} runs)")
        print(f"Individual JSON:  {avg_individual:.6f}s (avg over {iterations} runs)")
        print(f"Model Dump:       {avg_model_dump:.6f}s (avg over {iterations} runs)")
        
        # Determine fastest approach
        fastest_time = min(avg_typeadapter, avg_individual, avg_model_dump)
        if fastest_time == avg_typeadapter:
            fastest = "TypeAdapter"
        elif fastest_time == avg_individual:
            fastest = "Individual JSON"
        else:
            fastest = "Model Dump"
        
        print(f"Fastest approach: {fastest}")
        
        # All times should be reasonable (under 1 second for small dataset)
        assert avg_typeadapter < 1.0
        assert avg_individual < 1.0
        assert avg_model_dump < 1.0
    
    def test_performance_large_dataset(self, mock_items_large):
        """Compare performance on large dataset (1000 items)."""
        # Run fewer iterations for large dataset
        iterations = 3
        
        typeadapter_times = []
        individual_times = []
        model_dump_times = []
        
        for _ in range(iterations):
            _, ta_time = self.serialize_with_typeadapter(mock_items_large)
            _, ind_time = self.serialize_individually(mock_items_large)
            _, md_time = self.serialize_with_model_dump(mock_items_large)
            
            typeadapter_times.append(ta_time)
            individual_times.append(ind_time)
            model_dump_times.append(md_time)
        
        # Calculate averages
        avg_typeadapter = sum(typeadapter_times) / iterations
        avg_individual = sum(individual_times) / iterations
        avg_model_dump = sum(model_dump_times) / iterations
        
        print(f"\n=== LARGE DATASET (1000 items) PERFORMANCE ===")
        print(f"TypeAdapter:      {avg_typeadapter:.6f}s (avg over {iterations} runs)")
        print(f"Individual JSON:  {avg_individual:.6f}s (avg over {iterations} runs)")
        print(f"Model Dump:       {avg_model_dump:.6f}s (avg over {iterations} runs)")
        
        # Calculate performance ratios
        if avg_typeadapter < avg_individual:
            ratio = avg_individual / avg_typeadapter
            print(f"TypeAdapter is {ratio:.2f}x faster than Individual JSON")
        else:
            ratio = avg_typeadapter / avg_individual
            print(f"Individual JSON is {ratio:.2f}x faster than TypeAdapter")
        
        # Determine fastest approach
        fastest_time = min(avg_typeadapter, avg_individual, avg_model_dump)
        if fastest_time == avg_typeadapter:
            fastest = "TypeAdapter"
        elif fastest_time == avg_individual:
            fastest = "Individual JSON"
        else:
            fastest = "Model Dump"
        
        print(f"Fastest approach: {fastest}")
        
        # All times should be reasonable (under 5 seconds for large dataset)
        assert avg_typeadapter < 5.0
        assert avg_individual < 5.0
        assert avg_model_dump < 5.0
    
    def test_typeadapter_reuse_performance(self, mock_items_small):
        """Test performance when reusing the same TypeAdapter instance."""
        # Pre-create adapter (simulating module-level creation)
        adapter = TypeAdapter(list[MockApiItem])
        
        def serialize_with_reused_adapter():
            return adapter.dump_json(mock_items_small).decode('utf-8')
        
        # Run multiple times with the same adapter
        iterations = 10
        reuse_times = []
        
        for _ in range(iterations):
            _, time_taken = self.measure_execution_time(serialize_with_reused_adapter)
            reuse_times.append(time_taken)
        
        avg_reuse_time = sum(reuse_times) / iterations
        
        # Compare with fresh TypeAdapter creation each time
        fresh_times = []
        for _ in range(iterations):
            _, time_taken = self.serialize_with_typeadapter(mock_items_small)
            fresh_times.append(time_taken)
        
        avg_fresh_time = sum(fresh_times) / iterations
        
        print(f"\n=== TYPEADAPTER REUSE PERFORMANCE ===")
        print(f"Reused TypeAdapter:  {avg_reuse_time:.6f}s")
        print(f"Fresh TypeAdapter:   {avg_fresh_time:.6f}s")
        
        if avg_reuse_time < avg_fresh_time:
            ratio = avg_fresh_time / avg_reuse_time
            print(f"Reusing TypeAdapter is {ratio:.2f}x faster")
        
        # Reused adapter should be at least as fast (usually faster)
        assert avg_reuse_time <= avg_fresh_time * 1.1  # Allow 10% tolerance 