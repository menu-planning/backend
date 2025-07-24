"""
Fake implementations for testing following "Architecture Patterns with Python" patterns.

These fake repositories use in-memory storage and implement the same interfaces
as the real repositories for isolated testing.
"""

from typing import Any

from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.entities.classification import (
    Brand, Source, Category, ParentCategory, FoodGroup, ProcessType
)


class FakeProductRepository:
    """In-memory fake implementation of ProductRepo for testing."""
    
    def __init__(self):
        self._products: dict[str, Product] = {}
        self.seen: set[Product] = set()
        # Basic repository attributes to match real interface
        self.data_mapper = None
        self.domain_model_type = Product
        self.sa_model_type = None

    async def add(self, entity: Product):
        """Add a product to the in-memory store."""
        self._products[entity.id] = entity
        self.seen.add(entity)

    async def get(self, id: str) -> Product:
        """Get a product by ID."""
        if id not in self._products:
            raise KeyError(f"Product with id {id} not found")
        product = self._products[id]
        self.seen.add(product)
        return product

    async def get_sa_instance(self, id: str):
        """Return a fake SA instance - not needed for most tests."""
        # For testing purposes, we'll just return the domain object
        # In real tests, you might want to create a proper mock
        return await self.get(id)

    async def list_all_brand_names(self) -> list[str]:
        """List all unique brand names from products."""
        brands = set()
        for product in self._products.values():
            if product.brand_id:
                brands.add(product.brand_id)  # Simplified - real implementation would join with brands
        return list(brands)

    async def list_top_similar_names(
        self,
        description: str,
        include_product_with_barcode: bool = False,
        limit: int = 20,
        filter_by_first_word_partial_match: bool = False,
    ) -> list[Product]:
        """Simple similarity search based on name matching."""
        results = []
        description_lower = description.lower()
        
        for product in self._products.values():
            if not include_product_with_barcode and product.barcode:
                continue
                
            # Simple similarity: check if description appears in product name
            if description_lower in product.name.lower():
                results.append(product)
                
        # Simple sorting by name similarity (real implementation would use PostgreSQL similarity)
        results.sort(key=lambda p: len(p.name))
        return results[:limit]

    async def list_filter_options(
        self,
        *,
        filter: dict[str, Any] | None = None,
        starting_stmt = None,
        limit: int | None = None,
    ) -> dict[str, dict[str, str | list[str]]]:
        """Return simplified filter options."""
        # Simplified implementation for testing
        brands = list(set(p.brand_id for p in self._products.values() if p.brand_id))
        categories = list(set(p.category_id for p in self._products.values() if p.category_id))
        parent_categories = list(set(p.parent_category_id for p in self._products.values() if p.parent_category_id))
        
        return {
            "sort": {
                "type": "sort",
                "options": ["name", "created_at", "updated_at"],
            },
            "parent-category": {
                "type": "multi_selection",
                "options": parent_categories,
            },
            "category": {
                "type": "multi_selection",
                "options": categories,
            },
            "brand": {
                "type": "multi_selection", 
                "options": brands,
            },
        }

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt = None,
        hide_undefined_auto_products: bool = True,
        _return_sa_instance: bool = False,
    ) -> list[Product]:
        """Query products with basic filtering."""
        results = list(self._products.values())
        
        # Apply basic filters
        if "name" in filter:
            name_filter = filter["name"]
            results = [p for p in results if name_filter.lower() in p.name.lower()]
            
        if "is_food" in filter:
            is_food = filter["is_food"]
            results = [p for p in results if p.is_food == is_food]
            
        if "barcode" in filter:
            barcode = filter["barcode"]
            results = [p for p in results if p.barcode == barcode]
            
        if "brand" in filter:
            brand = filter["brand"]
            if isinstance(brand, list):
                results = [p for p in results if p.brand_id in brand]
            else:
                results = [p for p in results if p.brand_id == brand]
                
        if "category" in filter:
            category = filter["category"]
            if isinstance(category, list):
                results = [p for p in results if p.category_id in category]
            else:
                results = [p for p in results if p.category_id == category]
                
        if "parent_category" in filter:
            parent_category = filter["parent_category"]
            if isinstance(parent_category, list):
                results = [p for p in results if p.parent_category_id in parent_category]
            else:
                results = [p for p in results if p.parent_category_id == parent_category]

        # Apply discarded filter (products not marked as discarded)
        if filter.get("discarded", False) is False:
            results = [p for p in results if not p.discarded]

        # Apply limit
        if "limit" in filter:
            limit = filter["limit"]
            results = results[:limit]
            
        # Apply skip
        if "skip" in filter:
            skip = filter["skip"]
            results = results[skip:]

        # Mark as seen
        for product in results:
            self.seen.add(product)
            
        return results

    async def persist(self, domain_obj: Product) -> None:
        """Persist a domain object."""
        self._products[domain_obj.id] = domain_obj
        self.seen.add(domain_obj)

    async def persist_all(self, domain_entities: list[Product] | None = None) -> None:
        """Persist multiple domain objects."""
        if domain_entities:
            for entity in domain_entities:
                await self.persist(entity)


class FakeClassificationRepository:
    """Base fake repository for classification entities (Brand, Source, etc)."""
    
    def __init__(self, entity_type):
        self._entities: dict[str, Any] = {}
        self.seen: set[Any] = set()
        self.domain_model_type = entity_type
        self.data_mapper = None
        self.sa_model_type = None

    async def add(self, entity):
        """Add an entity to the in-memory store."""
        self._entities[entity.id] = entity
        self.seen.add(entity)

    async def get(self, id: str):
        """Get an entity by ID."""
        if id not in self._entities:
            raise KeyError(f"Entity with id {id} not found")
        entity = self._entities[id]
        self.seen.add(entity)
        return entity

    async def get_sa_instance(self, id: str):
        """Return a fake SA instance."""
        return await self.get(id)

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt = None,
        _return_sa_instance: bool = False,
    ) -> list:
        """Query entities with basic filtering."""
        results = list(self._entities.values())
        
        # Apply basic name filter
        if "name" in filter:
            name_filter = filter["name"]
            results = [e for e in results if name_filter.lower() in e.name.lower()]

        # Apply discarded filter
        if filter.get("discarded", False) is False:
            results = [e for e in results if not e.discarded]

        # Apply limit
        if "limit" in filter:
            limit = filter["limit"]
            results = results[:limit]
            
        # Apply skip
        if "skip" in filter:
            skip = filter["skip"]
            results = results[skip:]

        # Mark as seen
        for entity in results:
            self.seen.add(entity)
            
        return results

    async def persist(self, domain_obj) -> None:
        """Persist a domain object."""
        self._entities[domain_obj.id] = domain_obj
        self.seen.add(domain_obj)

    async def persist_all(self, domain_entities: list | None = None) -> None:
        """Persist multiple domain objects."""
        if domain_entities:
            for entity in domain_entities:
                await self.persist(entity)


class FakeBrandRepository(FakeClassificationRepository):
    """Fake repository for Brand entities."""
    def __init__(self):
        super().__init__(Brand)


class FakeSourceRepository(FakeClassificationRepository):
    """Fake repository for Source entities."""
    def __init__(self):
        super().__init__(Source)


class FakeCategoryRepository(FakeClassificationRepository):
    """Fake repository for Category entities."""
    def __init__(self):
        super().__init__(Category)


class FakeParentCategoryRepository(FakeClassificationRepository):
    """Fake repository for ParentCategory entities."""
    def __init__(self):
        super().__init__(ParentCategory)


class FakeFoodGroupRepository(FakeClassificationRepository):
    """Fake repository for FoodGroup entities."""
    def __init__(self):
        super().__init__(FoodGroup)


class FakeProcessTypeRepository(FakeClassificationRepository):
    """Fake repository for ProcessType entities."""
    def __init__(self):
        super().__init__(ProcessType) 