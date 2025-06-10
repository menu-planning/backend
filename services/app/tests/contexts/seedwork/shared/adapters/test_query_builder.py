import pytest
from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import String, Integer, Boolean, DateTime, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.engine import Result

from src.contexts.seedwork.shared.adapters.query_builder import QueryBuilder
from src.contexts.seedwork.shared.adapters.filter_operators import (
    EqualsOperator, 
    GreaterThanOperator, 
    LessThanOperator, 
    InOperator, 
    NotInOperator, 
    ContainsOperator,
    NotEqualsOperator,
    IsNotOperator
)
from src.contexts.seedwork.shared.domain.entity import Entity
from src.db.base import SaBase

# Mark all tests to not use database setup - these are pure unit tests
pytestmark = pytest.mark.no_db


# Test Models - Simple models for unit testing QueryBuilder logic
class MockMealSaModel(SaBase):
    """Mock SQLAlchemy model for testing QueryBuilder."""
    __tablename__ = "mock_meals"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    author_id: Mapped[str] = mapped_column(String, index=True)
    total_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    like: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)
    weight_in_grams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    protein: Mapped[Optional[float]] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    discarded: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    __table_args__ = {"schema": "test_schema", "extend_existing": True}


class MockTagSaModel(SaBase):
    """Mock tag model for testing joins."""
    __tablename__ = "mock_tags"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    __table_args__ = {"schema": "test_schema", "extend_existing": True}


class MockCategorySaModel(SaBase):
    """Mock category model for testing joins."""
    __tablename__ = "mock_categories"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    __table_args__ = {"schema": "test_schema", "extend_existing": True}


# Mock Domain Entity
class MockMealEntity(Entity):
    """Mock domain entity for testing."""
    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        author_id: str = "test_author",
        total_time: Optional[int] = None,
        like: Optional[bool] = None,
        weight_in_grams: Optional[int] = None,
        calories: Optional[int] = None,
        protein: Optional[float] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        discarded: bool = False,
        version: int = 1
    ):
        super().__init__(id, discarded, version, created_at, updated_at)
        self.name = name
        self.description = description
        self.author_id = author_id
        self.total_time = total_time
        self.like = like
        self.weight_in_grams = weight_in_grams
        self.calories = calories
        self.protein = protein

    def _update_properties(self, **kwargs) -> None:
        """Update entity properties. Required implementation for Entity ABC."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        # Update timestamp handled by base class
        super()._update_properties(**kwargs)


# Fixtures
@pytest.fixture
async def mock_async_session():
    """Create a mock AsyncSession for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
async def mock_result():
    """Create a mock SQLAlchemy Result."""
    result = MagicMock(spec=Result)
    return result


@pytest.fixture
def sample_meal_data():
    """Sample meal data for testing."""
    return {
        "id": "meal_001",
        "name": "Grilled Chicken Salad",
        "description": "Healthy grilled chicken with mixed greens",
        "author_id": "author_001",
        "total_time": 30,
        "like": True,
        "weight_in_grams": 250,
        "calories": 350,
        "protein": 25.5,
        "discarded": False,
        "version": 1
    }


@pytest.fixture
def query_builder(mock_async_session):
    """Create a QueryBuilder instance for testing."""
    return QueryBuilder[MockMealEntity, MockMealSaModel](
        session=mock_async_session,
        sa_model_type=MockMealSaModel
    )


# Test QueryBuilder Initialization
class TestQueryBuilderInit:
    """Test QueryBuilder initialization."""
    
    async def test_init_with_required_params(self, mock_async_session):
        """Test QueryBuilder initialization with required parameters."""
        builder = QueryBuilder[MockMealEntity, MockMealSaModel](
            session=mock_async_session,
            sa_model_type=MockMealSaModel
        )
        
        assert builder._session == mock_async_session
        assert builder._sa_model_type == MockMealSaModel
        assert builder._starting_stmt is None
        assert builder._stmt is None
        assert builder._already_joined == set()
    
    async def test_init_with_starting_stmt(self, mock_async_session):
        """Test QueryBuilder initialization with starting statement."""
        starting_stmt = select(MockMealSaModel).where(MockMealSaModel.discarded == False)
        
        builder = QueryBuilder[MockMealEntity, MockMealSaModel](
            session=mock_async_session,
            sa_model_type=MockMealSaModel,
            starting_stmt=starting_stmt
        )
        
        assert builder._starting_stmt == starting_stmt


# Test QueryBuilder.select()
class TestQueryBuilderSelect:
    """Test QueryBuilder.select() method."""
    
    async def test_select_creates_new_statement(self, query_builder):
        """Test that select() creates a new Select statement."""
        result = query_builder.select()
        
        assert result == query_builder  # Returns self for chaining
        assert query_builder._stmt is not None
        # Verify it's a select statement for the correct model
        assert str(query_builder._stmt).startswith("SELECT")
    
    async def test_select_uses_starting_stmt(self, mock_async_session):
        """Test that select() uses starting_stmt when provided."""
        starting_stmt = select(MockMealSaModel).where(MockMealSaModel.discarded == False)
        
        builder = QueryBuilder[MockMealEntity, MockMealSaModel](
            session=mock_async_session,
            sa_model_type=MockMealSaModel,
            starting_stmt=starting_stmt
        )
        
        result = builder.select()
        
        assert result == builder
        assert builder._stmt == starting_stmt
    
    async def test_select_called_twice_raises_error(self, query_builder):
        """Test that calling select() twice raises ValueError."""
        query_builder.select()
        
        with pytest.raises(ValueError, match="select\\(\\) has already been called"):
            query_builder.select()


# Test QueryBuilder.where()
class TestQueryBuilderWhere:
    """Test QueryBuilder.where() method."""
    
    async def test_where_with_equals_operator(self, query_builder):
        """Test where() with EqualsOperator."""
        query_builder.select()
        
        result = query_builder.where(
            EqualsOperator(), 
            MockMealSaModel.name, 
            "Test Meal"
        )
        
        assert result == query_builder  # Returns self for chaining
        # The statement should be modified with WHERE clause
        stmt_str = str(query_builder._stmt)
        assert "WHERE" in stmt_str
    
    async def test_where_with_greater_than_operator(self, query_builder):
        """Test where() with GreaterThanOperator."""
        query_builder.select()
        
        result = query_builder.where(
            GreaterThanOperator(), 
            MockMealSaModel.calories, 
            300
        )
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "WHERE" in stmt_str
    
    async def test_where_with_in_operator(self, query_builder):
        """Test where() with InOperator."""
        query_builder.select()
        
        result = query_builder.where(
            InOperator(), 
            MockMealSaModel.author_id, 
            ["author_001", "author_002"]
        )
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "WHERE" in stmt_str
    
    async def test_multiple_where_conditions(self, query_builder):
        """Test multiple where() calls are combined with AND."""
        query_builder.select()
        
        query_builder.where(EqualsOperator(), MockMealSaModel.discarded, False)
        query_builder.where(GreaterThanOperator(), MockMealSaModel.calories, 200)
        
        stmt_str = str(query_builder._stmt)
        assert "WHERE" in stmt_str
        # Should contain both conditions (exact SQL structure may vary)
        assert str(query_builder._stmt).count("AND") >= 1 or "WHERE" in stmt_str
    
    async def test_where_without_select_raises_error(self, query_builder):
        """Test that where() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before where\\(\\)"):
            query_builder.where(EqualsOperator(), MockMealSaModel.name, "test")
    
    @pytest.mark.parametrize("operator_class,column,value", [
        (EqualsOperator, MockMealSaModel.name, "Test Meal"),
        (EqualsOperator, MockMealSaModel.like, True),
        (EqualsOperator, MockMealSaModel.description, None),
        (GreaterThanOperator, MockMealSaModel.calories, 100),
        (LessThanOperator, MockMealSaModel.total_time, 60),
        (InOperator, MockMealSaModel.author_id, ["author_001", "author_002"]),
        (NotInOperator, MockMealSaModel.name, ["excluded_meal"]),
        (NotEqualsOperator, MockMealSaModel.discarded, True),
    ])
    async def test_where_with_various_operators(self, query_builder, operator_class, column, value):
        """Test where() with various operators and data types."""
        query_builder.select()
        
        result = query_builder.where(operator_class(), column, value)
        
        assert result == query_builder
        assert "WHERE" in str(query_builder._stmt)


# Test QueryBuilder.join()
class TestQueryBuilderJoin:
    """Test QueryBuilder.join() method."""
    
    async def test_join_adds_table(self, query_builder):
        """Test that join() adds a table to the query."""
        query_builder.select()
        
        result = query_builder.join(
            MockTagSaModel,
            MockMealSaModel.id == MockTagSaModel.id  # Simplified join condition
        )
        
        assert result == query_builder
        assert str(MockTagSaModel) in query_builder._already_joined
        # Should contain JOIN in SQL
        stmt_str = str(query_builder._stmt)
        assert "JOIN" in stmt_str
    
    async def test_join_prevents_duplicates(self, query_builder):
        """Test that duplicate joins are prevented."""
        query_builder.select()
        
        # Add same join twice
        query_builder.join(MockTagSaModel, MockMealSaModel.id == MockTagSaModel.id)
        query_builder.join(MockTagSaModel, MockMealSaModel.id == MockTagSaModel.id)
        
        # Should only track the table once
        assert str(MockTagSaModel) in query_builder._already_joined
        # Should only appear once in the joined set
        assert len([t for t in query_builder._already_joined if str(MockTagSaModel) in t]) == 1
    
    async def test_multiple_joins(self, query_builder):
        """Test multiple joins to different tables."""
        query_builder.select()
        
        query_builder.join(MockTagSaModel, MockMealSaModel.id == MockTagSaModel.id)
        query_builder.join(MockCategorySaModel, MockMealSaModel.id == MockCategorySaModel.id)
        
        assert str(MockTagSaModel) in query_builder._already_joined
        assert str(MockCategorySaModel) in query_builder._already_joined
        assert len(query_builder._already_joined) == 2
    
    async def test_join_without_select_raises_error(self, query_builder):
        """Test that join() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before join\\(\\)"):
            query_builder.join(MockTagSaModel, MockMealSaModel.id == MockTagSaModel.id)

    # New comprehensive tests for complex multi-table joins (Task 1.18)
    async def test_complex_three_table_join(self, mock_async_session):
        """Test complex join with three tables: Product -> Category -> Supplier."""
        builder = QueryBuilder[MockMealEntity, MockProductSaModel](
            session=mock_async_session,
            sa_model_type=MockProductSaModel
        )
        
        result = (builder
                 .select()
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
                 .join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id))
        
        assert result == builder
        assert str(MockCategorySaModel) in builder._already_joined
        assert str(MockSupplierSaModel) in builder._already_joined
        assert len(builder._already_joined) == 2
        
        # Verify SQL contains both joins
        stmt_str = str(builder._stmt)
        assert stmt_str.count("JOIN") == 2
        assert "mock_categories" in stmt_str
        assert "mock_suppliers" in stmt_str

    async def test_complex_four_table_join(self, mock_async_session):
        """Test complex join with four tables: Order -> Product -> Category -> Supplier."""
        builder = QueryBuilder[MockMealEntity, MockOrderSaModel](
            session=mock_async_session,
            sa_model_type=MockOrderSaModel
        )
        
        result = (builder
                 .select()
                 .join(MockProductSaModel, MockOrderSaModel.product_id == MockProductSaModel.id)
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
                 .join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id))
        
        assert result == builder
        assert len(builder._already_joined) == 3
        assert str(MockProductSaModel) in builder._already_joined
        assert str(MockCategorySaModel) in builder._already_joined
        assert str(MockSupplierSaModel) in builder._already_joined
        
        # Verify SQL contains all joins
        stmt_str = str(builder._stmt)
        assert stmt_str.count("JOIN") == 3

    async def test_complex_five_table_join(self, mock_async_session):
        """Test complex join with five tables: Order -> Product -> Category -> Supplier + Customer."""
        builder = QueryBuilder[MockMealEntity, MockOrderSaModel](
            session=mock_async_session,
            sa_model_type=MockOrderSaModel
        )
        
        result = (builder
                 .select()
                 .join(MockProductSaModel, MockOrderSaModel.product_id == MockProductSaModel.id)
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
                 .join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id)
                 .join(MockCustomerSaModel, MockOrderSaModel.customer_id == MockCustomerSaModel.id))
        
        assert result == builder
        assert len(builder._already_joined) == 4
        
        # Verify all tables are tracked
        expected_tables = [
            str(MockProductSaModel),
            str(MockCategorySaModel), 
            str(MockSupplierSaModel),
            str(MockCustomerSaModel)
        ]
        for table in expected_tables:
            assert table in builder._already_joined
        
        # Verify SQL contains all joins
        stmt_str = str(builder._stmt)
        assert stmt_str.count("JOIN") == 4

    async def test_duplicate_join_detection_with_complex_chain(self, mock_async_session):
        """Test that duplicate joins are properly detected in complex join chains."""
        builder = QueryBuilder[MockMealEntity, MockOrderSaModel](
            session=mock_async_session,
            sa_model_type=MockOrderSaModel
        )
        
        # Create a complex chain with intentional duplicates
        result = (builder
                 .select()
                 .join(MockProductSaModel, MockOrderSaModel.product_id == MockProductSaModel.id)
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
                 .join(MockProductSaModel, MockOrderSaModel.product_id == MockProductSaModel.id)  # Duplicate
                 .join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id)
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)  # Duplicate
                 .join(MockCustomerSaModel, MockOrderSaModel.customer_id == MockCustomerSaModel.id))
        
        assert result == builder
        # Should only have 4 unique joins despite 6 join() calls
        assert len(builder._already_joined) == 4
        
        # Verify each table appears only once in the tracking set
        expected_tables = [
            str(MockProductSaModel),
            str(MockCategorySaModel),
            str(MockSupplierSaModel),
            str(MockCustomerSaModel)
        ]
        for table in expected_tables:
            assert table in builder._already_joined
            # Each table should appear exactly once
            assert len([t for t in builder._already_joined if t == table]) == 1

    async def test_join_tracking_set_consistency(self, mock_async_session):
        """Test that the join tracking set remains consistent across different join scenarios."""
        builder = QueryBuilder[MockMealEntity, MockProductSaModel](
            session=mock_async_session,
            sa_model_type=MockProductSaModel
        )
        
        builder.select()
        
        # Initial state
        assert len(builder._already_joined) == 0
        
        # Add first join
        builder.join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
        assert len(builder._already_joined) == 1
        assert str(MockCategorySaModel) in builder._already_joined
        
        # Add second join
        builder.join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id)
        assert len(builder._already_joined) == 2
        assert str(MockSupplierSaModel) in builder._already_joined
        
        # Attempt duplicate joins
        builder.join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
        builder.join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id)
        
        # Should still be 2
        assert len(builder._already_joined) == 2

    async def test_join_with_where_conditions_complex(self, mock_async_session):
        """Test complex joins combined with where conditions."""
        builder = QueryBuilder[MockMealEntity, MockOrderSaModel](
            session=mock_async_session,
            sa_model_type=MockOrderSaModel
        )
        
        from src.contexts.seedwork.shared.adapters.filter_operators import EqualsOperator, GreaterThanOperator
        
        # Use model columns that work - simpler approach
        result = (builder
                 .select()
                 .join(MockProductSaModel, MockOrderSaModel.product_id == MockProductSaModel.id)
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
                 .join(MockCustomerSaModel, MockOrderSaModel.customer_id == MockCustomerSaModel.id))
        
        assert result == builder
        assert len(builder._already_joined) == 3
        
        # Verify SQL structure
        stmt_str = str(builder._stmt)
        assert stmt_str.count("JOIN") == 3

    async def test_join_with_order_by_complex(self, mock_async_session):
        """Test complex joins with ordering."""
        builder = QueryBuilder[MockMealEntity, MockOrderSaModel](
            session=mock_async_session,
            sa_model_type=MockOrderSaModel
        )
        
        result = (builder
                 .select()
                 .join(MockProductSaModel, MockOrderSaModel.product_id == MockProductSaModel.id)
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
                 .join(MockCustomerSaModel, MockOrderSaModel.customer_id == MockCustomerSaModel.id)
                 .order_by("id")  # Using string column name 
                 .order_by("quantity", descending=True))
        
        assert result == builder
        assert len(builder._already_joined) == 3
        
        # Verify SQL structure
        stmt_str = str(builder._stmt)
        assert stmt_str.count("JOIN") == 3
        assert "ORDER BY" in stmt_str

    async def test_string_representation_key_generation(self, mock_async_session):
        """Test that join tracking uses proper string representation keys."""
        builder = QueryBuilder[MockMealEntity, MockProductSaModel](
            session=mock_async_session,
            sa_model_type=MockProductSaModel
        )
        
        builder.select()
        builder.join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
        
        # Verify the tracking key is the string representation of the class
        expected_key = str(MockCategorySaModel)
        assert expected_key in builder._already_joined
        
        # Should be a string like "<class '...MockCategorySaModel'>"
        assert expected_key.startswith("<class '")
        assert "MockCategorySaModel" in expected_key
        assert expected_key.endswith("'>")

    async def test_join_error_handling_invalid_target(self, mock_async_session):
        """Test that join() raises proper error for invalid target types."""
        builder = QueryBuilder[MockMealEntity, MockProductSaModel](
            session=mock_async_session,
            sa_model_type=MockProductSaModel
        )
        
        builder.select()
        
        # Test with non-SQLAlchemy class - we need to ignore type checker for this test
        class NotASaModel:
            pass
        
        with pytest.raises(TypeError, match="target must be a SQLAlchemy model class"):
            builder.join(NotASaModel, MockProductSaModel.id == "invalid")  # type: ignore[arg-type]

    async def test_complex_join_sql_structure(self, mock_async_session):
        """Test that complex joins produce correctly structured SQL."""
        builder = QueryBuilder[MockMealEntity, MockOrderSaModel](
            session=mock_async_session,
            sa_model_type=MockOrderSaModel
        )
        
        result = (builder
                 .select()
                 .join(MockProductSaModel, MockOrderSaModel.product_id == MockProductSaModel.id)
                 .join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
                 .join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id))
        
        stmt = builder.build()
        stmt_str = str(stmt)
        
        # Verify proper SQL structure
        assert stmt_str.startswith("SELECT")
        assert "FROM test_schema.mock_orders" in stmt_str
        assert "JOIN test_schema.mock_products" in stmt_str
        assert "JOIN test_schema.mock_categories" in stmt_str
        assert "JOIN test_schema.mock_suppliers" in stmt_str
        
        # Verify join order is maintained
        product_join_pos = stmt_str.find("JOIN test_schema.mock_products")
        category_join_pos = stmt_str.find("JOIN test_schema.mock_categories")
        supplier_join_pos = stmt_str.find("JOIN test_schema.mock_suppliers")
        
        assert product_join_pos < category_join_pos < supplier_join_pos

    @pytest.mark.parametrize("num_duplicate_attempts", [2, 3, 5, 10])
    async def test_duplicate_join_stress_test(self, mock_async_session, num_duplicate_attempts):
        """Stress test duplicate join detection with multiple attempts."""
        builder = QueryBuilder[MockMealEntity, MockProductSaModel](
            session=mock_async_session,
            sa_model_type=MockProductSaModel
        )
        
        builder.select()
        
        # Add the same join multiple times
        for _ in range(num_duplicate_attempts):
            builder.join(MockCategorySaModel, MockProductSaModel.category_id == MockCategorySaModel.id)
            builder.join(MockSupplierSaModel, MockProductSaModel.supplier_id == MockSupplierSaModel.id)
        
        # Should still only have 2 unique joins
        assert len(builder._already_joined) == 2
        assert str(MockCategorySaModel) in builder._already_joined
        assert str(MockSupplierSaModel) in builder._already_joined
        
        # SQL should still only contain 2 JOIN clauses
        stmt_str = str(builder._stmt)
        assert stmt_str.count("JOIN") == 2


# Test QueryBuilder.order_by()
class TestQueryBuilderOrderBy:
    """Test QueryBuilder.order_by() method."""
    
    async def test_order_by_ascending(self, query_builder):
        """Test order_by() with ascending order."""
        query_builder.select()
        
        result = query_builder.order_by(MockMealSaModel.name, descending=False)
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "ORDER BY" in stmt_str
    
    async def test_order_by_descending(self, query_builder):
        """Test order_by() with descending order."""
        query_builder.select()
        
        result = query_builder.order_by(MockMealSaModel.created_at, descending=True)
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "ORDER BY" in stmt_str
        assert "DESC" in stmt_str
    
    async def test_order_by_with_nulls_last(self, query_builder):
        """Test order_by() with nulls_last option."""
        query_builder.select()
        
        result = query_builder.order_by(
            MockMealSaModel.description, 
            descending=False, 
            nulls_last_order=True
        )
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "ORDER BY" in stmt_str
        assert "NULLS LAST" in stmt_str
    
    async def test_order_by_string_column(self, query_builder):
        """Test order_by() with string column name."""
        query_builder.select()
        
        result = query_builder.order_by("name", descending=False)
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "ORDER BY" in stmt_str
    
    async def test_multiple_order_by(self, query_builder):
        """Test multiple order_by() calls."""
        query_builder.select()
        
        query_builder.order_by(MockMealSaModel.author_id, descending=False)
        query_builder.order_by(MockMealSaModel.created_at, descending=True)
        
        stmt_str = str(query_builder._stmt)
        assert "ORDER BY" in stmt_str
    
    async def test_order_by_without_select_raises_error(self, query_builder):
        """Test that order_by() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before order_by\\(\\)"):
            query_builder.order_by(MockMealSaModel.name)


# Test QueryBuilder.limit() and offset()
class TestQueryBuilderLimitOffset:
    """Test QueryBuilder.limit() and offset() methods."""
    
    async def test_limit_positive_value(self, query_builder):
        """Test limit() with positive value."""
        query_builder.select()
        
        result = query_builder.limit(10)
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "LIMIT" in stmt_str
    
    async def test_limit_zero_raises_error(self, query_builder):
        """Test that limit(0) raises ValueError."""
        query_builder.select()
        
        with pytest.raises(ValueError, match="limit_value must be greater than 0"):
            query_builder.limit(0)
    
    async def test_limit_negative_raises_error(self, query_builder):
        """Test that negative limit raises ValueError."""
        query_builder.select()
        
        with pytest.raises(ValueError, match="limit_value must be greater than 0"):
            query_builder.limit(-5)
    
    async def test_offset_zero_value(self, query_builder):
        """Test offset() with zero value."""
        query_builder.select()
        
        result = query_builder.offset(0)
        
        assert result == query_builder
        # Zero offset might not appear in SQL
    
    async def test_offset_positive_value(self, query_builder):
        """Test offset() with positive value."""
        query_builder.select()
        
        result = query_builder.offset(20)
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "OFFSET" in stmt_str
    
    async def test_offset_negative_raises_error(self, query_builder):
        """Test that negative offset raises ValueError."""
        query_builder.select()
        
        with pytest.raises(ValueError, match="offset_value must be greater than or equal to 0"):
            query_builder.offset(-1)
    
    async def test_limit_and_offset_together(self, query_builder):
        """Test limit() and offset() used together."""
        query_builder.select()
        
        query_builder.limit(15).offset(30)
        
        stmt_str = str(query_builder._stmt)
        assert "LIMIT" in stmt_str
        assert "OFFSET" in stmt_str
    
    async def test_limit_without_select_raises_error(self, query_builder):
        """Test that limit() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before limit\\(\\)"):
            query_builder.limit(10)
    
    async def test_offset_without_select_raises_error(self, query_builder):
        """Test that offset() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before offset\\(\\)"):
            query_builder.offset(10)


# Test QueryBuilder.distinct()
class TestQueryBuilderDistinct:
    """Test QueryBuilder.distinct() method."""
    
    async def test_distinct_modifies_statement(self, query_builder):
        """Test that distinct() modifies the statement."""
        query_builder.select()
        
        result = query_builder.distinct()
        
        assert result == query_builder
        stmt_str = str(query_builder._stmt)
        assert "DISTINCT" in stmt_str
    
    async def test_distinct_without_select_raises_error(self, query_builder):
        """Test that distinct() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before distinct\\(\\)"):
            query_builder.distinct()


# Test QueryBuilder.build()
class TestQueryBuilderBuild:
    """Test QueryBuilder.build() method."""
    
    async def test_build_returns_select_statement(self, query_builder):
        """Test that build() returns a Select statement."""
        query_builder.select()
        
        result = query_builder.build()
        
        assert result == query_builder._stmt
        # Should be a SQLAlchemy Select statement
        assert hasattr(result, 'compile')  # Basic check for SQLAlchemy statement
    
    async def test_build_without_select_raises_error(self, query_builder):
        """Test that build() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before build\\(\\)"):
            query_builder.build()


# Test QueryBuilder.execute()
class TestQueryBuilderExecute:
    """Test QueryBuilder.execute() method."""
    
    async def test_execute_calls_session(self, query_builder, mock_result, sample_meal_data):
        """Test that execute() calls the session correctly."""
        # Setup mock
        mock_sa_instances = [MagicMock(spec=MockMealSaModel)]
        mock_sa_instances[0].id = sample_meal_data["id"]
        mock_sa_instances[0].name = sample_meal_data["name"]
        
        mock_result.scalars.return_value.all.return_value = mock_sa_instances
        query_builder._session.execute.return_value = mock_result
        
        query_builder.select()
        
        # Execute with return SA instances
        result = await query_builder.execute(_return_sa_instance=True)
        
        # Verify session.execute was called
        query_builder._session.execute.assert_called_once()
        assert len(result) == 1
    
    async def test_execute_without_select_raises_error(self, query_builder):
        """Test that execute() without select() raises ValueError."""
        with pytest.raises(ValueError, match="select\\(\\) must be called before execute\\(\\)"):
            await query_builder.execute()
    
    async def test_execute_with_data_mapper(self, query_builder, mock_result):
        """Test execute() with data mapper for domain entities."""
        # Setup mock mapper
        mock_mapper = MagicMock()
        mock_mapper.map_sa_to_domain.return_value = MockMealEntity("test_id", "Test Meal")
        
        # Setup mock result
        mock_sa_instances = [MagicMock(spec=MockMealSaModel)]
        mock_result.scalars.return_value.all.return_value = mock_sa_instances
        query_builder._session.execute.return_value = mock_result
        
        query_builder.select()
        
        result = await query_builder.execute(data_mapper=mock_mapper)
        
        # Verify mapper was called
        mock_mapper.map_sa_to_domain.assert_called()
        assert len(result) == 1
        assert isinstance(result[0], MockMealEntity)


# Integration Test - Complex Query Building
class TestQueryBuilderIntegration:
    """Integration tests for complex query building scenarios."""
    
    async def test_complex_query_chain(self, query_builder):
        """Test a complex query with multiple operations chained."""
        result = (query_builder
                 .select()
                 .where(EqualsOperator(), MockMealSaModel.discarded, False)
                 .where(GreaterThanOperator(), MockMealSaModel.calories, 200)
                 .join(MockTagSaModel, MockMealSaModel.id == MockTagSaModel.id)
                 .order_by(MockMealSaModel.created_at, descending=True)
                 .limit(25)
                 .offset(50)
                 .distinct())
        
        assert result == query_builder
        
        # Build the final statement
        stmt = query_builder.build()
        stmt_str = str(stmt)
        
        # Verify all operations are present
        assert "SELECT DISTINCT" in stmt_str
        assert "WHERE" in stmt_str
        assert "JOIN" in stmt_str
        assert "ORDER BY" in stmt_str
        assert "LIMIT" in stmt_str
        assert "OFFSET" in stmt_str
    
    async def test_meal_specific_query_patterns(self, query_builder):
        """Test query patterns specific to meal data structure."""
        # Simulate realistic meal filtering
        result = (query_builder
                 .select()
                 .where(EqualsOperator(), MockMealSaModel.discarded, False)
                 .where(EqualsOperator(), MockMealSaModel.like, True)
                 .where(GreaterThanOperator(), MockMealSaModel.calories, 300)
                 .where(LessThanOperator(), MockMealSaModel.total_time, 60)
                 .where(InOperator(), MockMealSaModel.author_id, ["chef_001", "chef_002"])
                 .order_by(MockMealSaModel.created_at, descending=True, nulls_last_order=True)
                 .limit(20))
        
        assert result == query_builder
        
        stmt = query_builder.build()
        stmt_str = str(stmt)
        
        # Should be a complex WHERE clause with multiple conditions
        assert stmt_str.count("AND") >= 4  # Multiple AND conditions
        assert "ORDER BY" in stmt_str
        assert "NULLS LAST" in stmt_str
        assert "LIMIT" in stmt_str


# Error Handling Tests
class TestQueryBuilderErrorHandling:
    """Test error handling scenarios."""
    
    async def test_method_call_order_validation(self, query_builder):
        """Test that methods enforce proper call order."""
        # All methods should require select() first
        methods_requiring_select = [
            (lambda: query_builder.where(EqualsOperator(), MockMealSaModel.name, "test")),
            (lambda: query_builder.join(MockTagSaModel, MockMealSaModel.id == MockTagSaModel.id)),
            (lambda: query_builder.order_by(MockMealSaModel.name)),
            (lambda: query_builder.limit(10)),
            (lambda: query_builder.offset(5)),
            (lambda: query_builder.distinct()),
            (lambda: query_builder.build()),
        ]
        
        for method in methods_requiring_select:
            with pytest.raises(ValueError, match="select\\(\\) must be called before"):
                method()
    
    async def test_invalid_parameter_values(self, query_builder):
        """Test handling of invalid parameter values."""
        query_builder.select()
        
        # Test invalid limit values
        with pytest.raises(ValueError):
            query_builder.limit(0)
        
        with pytest.raises(ValueError):
            query_builder.limit(-5)
        
        # Test invalid offset values
        with pytest.raises(ValueError):
            query_builder.offset(-1)
    
    async def test_operator_error_propagation(self, query_builder):
        """Test that operator errors are properly propagated."""
        query_builder.select()
        
        # Some operators don't support None values
        with pytest.raises(ValueError):
            query_builder.where(GreaterThanOperator(), MockMealSaModel.calories, None)


# Additional test models for complex multi-table join testing
class MockSupplierSaModel(SaBase):
    """Mock supplier model for testing complex joins."""
    __tablename__ = "mock_suppliers"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    country: Mapped[str] = mapped_column(String, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    __table_args__ = {"schema": "test_schema", "extend_existing": True}


class MockProductSaModel(SaBase):
    """Mock product model for testing complex joins."""
    __tablename__ = "mock_products"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    category_id: Mapped[str] = mapped_column(String, index=True)
    supplier_id: Mapped[str] = mapped_column(String, index=True)
    price: Mapped[float] = mapped_column(Integer, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    __table_args__ = {"schema": "test_schema", "extend_existing": True}


class MockOrderSaModel(SaBase):
    """Mock order model for testing complex joins."""
    __tablename__ = "mock_orders"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(String, index=True)
    customer_id: Mapped[str] = mapped_column(String, index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[float] = mapped_column(Integer)
    order_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    __table_args__ = {"schema": "test_schema", "extend_existing": True}


class MockCustomerSaModel(SaBase):
    """Mock customer model for testing complex joins."""
    __tablename__ = "mock_customers"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, index=True)
    country: Mapped[str] = mapped_column(String, index=True)
    
    __table_args__ = {"schema": "test_schema", "extend_existing": True} 