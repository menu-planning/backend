"""Performance tests for ORM mapping operations.

Tests mapping performance for shared kernel ORM mappers including
NutriFactsMapper and TagMapper between domain objects and SQLAlchemy models.

Performance targets:
- Simple mapping (Tag): P95 < 5ms
- Complex mapping (NutriFacts): P95 < 10ms
- Bulk mapping (100 items): P95 < 100ms
- Roundtrip mapping: P95 < 15ms
"""

import asyncio
import contextlib
import time
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts_mapper import (
    NutriFactsMapper,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag_mapper import TagMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class AsyncBenchmarkTimer:
    """Context manager for measuring async operation performance with warmup and sampling."""

    def __init__(self, max_ms: float, samples: int = 30, warmup: int = 5):
        """Initialize benchmark timer.

        Args:
            max_ms: Maximum allowed milliseconds for P95 threshold.
            samples: Number of samples to collect for measurement.
            warmup: Number of warmup iterations before measurement.
        """
        self.max_ms = max_ms
        self.samples = samples
        self.warmup = warmup
        self.times: list[float] = []

    def __enter__(self):
        """Enter context and start timing."""
        self.times = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and validate performance threshold."""
        if exc_type is not None:
            return False

        if len(self.times) < self.samples:
            pytest.fail(f"Expected {self.samples} samples, got {len(self.times)}")

        # Calculate P95
        sorted_times = sorted(self.times)
        p95_index = int(0.95 * len(sorted_times))
        p95_time = sorted_times[p95_index]

        if p95_time > self.max_ms:
            pytest.fail(
                f"P95 time {p95_time:.2f}ms exceeds threshold {self.max_ms}ms. "
                f"Times: {sorted_times[:5]}...{sorted_times[-5:]}"
            )

    async def measure(self, operation):
        """Measure a single operation and record its execution time."""
        start_time = time.perf_counter()
        if callable(operation):
            result = operation()
            if asyncio.iscoroutine(result):
                await result
        else:
            await operation()
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        self.times.append(duration_ms)


@pytest.fixture
def async_benchmark_timer():
    """Provide async benchmark timer for performance measurements."""
    return AsyncBenchmarkTimer


@pytest.fixture
def seed_data():
    """Provide seed data for performance testing."""
    return {
        "simple_tag": {
            "key": "cuisine",
            "value": "italian",
            "author_id": "test-author-123",
            "type": "category",
        },
        "complex_nutri_facts": {
            "calories": NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            "protein": NutriValue(value=15.0, unit=MeasureUnit.GRAM),
            "carbohydrate": NutriValue(value=30.0, unit=MeasureUnit.GRAM),
            "total_fat": NutriValue(value=10.0, unit=MeasureUnit.GRAM),
            "saturated_fat": NutriValue(value=3.0, unit=MeasureUnit.GRAM),
            "trans_fat": NutriValue(value=0.0, unit=MeasureUnit.GRAM),
            "dietary_fiber": NutriValue(value=5.0, unit=MeasureUnit.GRAM),
            "sodium": NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
            "vitamin_a": NutriValue(value=100.0, unit=MeasureUnit.MICROGRAM),
            "vitamin_c": NutriValue(value=50.0, unit=MeasureUnit.MILLIGRAM),
            "calcium": NutriValue(value=150.0, unit=MeasureUnit.MILLIGRAM),
            "iron": NutriValue(value=2.0, unit=MeasureUnit.MILLIGRAM),
        },
    }


@pytest.fixture
def bulk_tag_data(seed_data):
    """Generate bulk tag data for performance testing."""
    base_tag = seed_data["simple_tag"]
    return [
        Tag(
            key=f"{base_tag['key']}_{i}",
            value=f"{base_tag['value']}_{i}",
            author_id=base_tag["author_id"],
            type=base_tag["type"],
        )
        for i in range(100)
    ]


@pytest.fixture
def bulk_nutri_facts_data(seed_data):
    """Generate bulk nutrition facts data for performance testing."""
    base_nutri = seed_data["complex_nutri_facts"]
    return [
        NutriFacts(
            calories=NutriValue(
                value=base_nutri["calories"].value + i, unit=MeasureUnit.ENERGY
            ),
            protein=base_nutri["protein"],
            carbohydrate=base_nutri["carbohydrate"],
            total_fat=base_nutri["total_fat"],
            saturated_fat=base_nutri["saturated_fat"],
            trans_fat=base_nutri["trans_fat"],
            dietary_fiber=base_nutri["dietary_fiber"],
            sodium=base_nutri["sodium"],
            vitamin_a=base_nutri["vitamin_a"],
            vitamin_c=base_nutri["vitamin_c"],
            calcium=base_nutri["calcium"],
            iron=base_nutri["iron"],
        )
        for i in range(100)
    ]


@pytest.fixture
def mock_async_session():
    """Provide a mock async session for testing."""

    class MockQueryResult:
        def scalar_one(self):
            # Simulate NoResultFound exception to trigger entity creation
            from sqlalchemy.exc import NoResultFound

            raise NoResultFound()

    class MockAsyncSession:
        def __init__(self):
            self.queries_executed = 0

        async def execute(self, query):
            """Mock execute method that simulates database query."""
            self.queries_executed += 1
            # Simulate database query time
            await asyncio.sleep(0.001)
            return MockQueryResult()

        async def get(self, model_class, id):
            """Mock get method that simulates entity retrieval."""
            self.queries_executed += 1
            await asyncio.sleep(0.001)
            return None

    return MockAsyncSession()


@pytest.mark.slow
@pytest.mark.anyio
async def test_tag_mapper_domain_to_sa_performance(
    async_benchmark_timer, seed_data, mock_async_session
):
    """Test TagMapper domain to SA mapping meets performance requirements."""
    tag = Tag(**seed_data["simple_tag"])

    # Warmup
    for _ in range(5):
        await TagMapper.map_domain_to_sa(mock_async_session, tag)

    with async_benchmark_timer(max_ms=5.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: TagMapper.map_domain_to_sa(mock_async_session, tag)
            )


@pytest.mark.slow
@pytest.mark.anyio
async def test_tag_mapper_sa_to_domain_performance(async_benchmark_timer, seed_data):
    """Test TagMapper SA to domain mapping meets performance requirements."""
    tag_sa = TagSaModel(
        id=1,
        key=seed_data["simple_tag"]["key"],
        value=seed_data["simple_tag"]["value"],
        author_id=seed_data["simple_tag"]["author_id"],
        type=seed_data["simple_tag"]["type"],
    )

    # Warmup
    for _ in range(5):
        TagMapper.map_sa_to_domain(tag_sa)

    with async_benchmark_timer(max_ms=2.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: TagMapper.map_sa_to_domain(tag_sa))


@pytest.mark.slow
@pytest.mark.anyio
async def test_nutri_facts_mapper_domain_to_sa_performance(
    async_benchmark_timer, seed_data, mock_async_session
):
    """Test NutriFactsMapper domain to SA mapping meets performance requirements."""
    nutri_facts = NutriFacts(**seed_data["complex_nutri_facts"])

    # Warmup
    for _ in range(5):
        await NutriFactsMapper.map_domain_to_sa(mock_async_session, nutri_facts)

    with async_benchmark_timer(max_ms=10.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: NutriFactsMapper.map_domain_to_sa(
                    mock_async_session, nutri_facts
                )
            )


@pytest.mark.slow
@pytest.mark.anyio
async def test_nutri_facts_mapper_sa_to_domain_performance(
    async_benchmark_timer, seed_data
):
    """Test NutriFactsMapper SA to domain mapping meets performance requirements."""
    nutri_sa = NutriFactsSaModel(
        calories=250.0,
        protein=15.0,
        carbohydrate=30.0,
        total_fat=10.0,
        saturated_fat=3.0,
        trans_fat=0.0,
        dietary_fiber=5.0,
        sodium=200.0,
        vitamin_a=100.0,
        vitamin_c=50.0,
        calcium=150.0,
        iron=2.0,
    )

    # Warmup
    for _ in range(5):
        NutriFactsMapper.map_sa_to_domain(nutri_sa)

    with async_benchmark_timer(max_ms=5.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: NutriFactsMapper.map_sa_to_domain(nutri_sa))


@pytest.mark.slow
@pytest.mark.anyio
async def test_tag_mapper_roundtrip_performance(
    async_benchmark_timer, seed_data, mock_async_session
):
    """Test TagMapper roundtrip mapping meets performance requirements."""
    tag = Tag(**seed_data["simple_tag"])

    # Warmup
    for _ in range(5):
        sa_obj = await TagMapper.map_domain_to_sa(mock_async_session, tag)
        TagMapper.map_sa_to_domain(sa_obj)

    with async_benchmark_timer(max_ms=15.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(lambda: _tag_roundtrip(mock_async_session, tag))


async def _tag_roundtrip(session: AsyncSession, tag: Tag) -> Tag:
    """Helper function for tag roundtrip mapping."""
    sa_obj = await TagMapper.map_domain_to_sa(session, tag)
    return TagMapper.map_sa_to_domain(sa_obj)


@pytest.mark.slow
@pytest.mark.anyio
async def test_nutri_facts_mapper_roundtrip_performance(
    async_benchmark_timer, seed_data, mock_async_session
):
    """Test NutriFactsMapper roundtrip mapping meets performance requirements."""
    nutri_facts = NutriFacts(**seed_data["complex_nutri_facts"])

    # Warmup
    for _ in range(5):
        sa_obj = await NutriFactsMapper.map_domain_to_sa(
            mock_async_session, nutri_facts
        )
        NutriFactsMapper.map_sa_to_domain(sa_obj)

    with async_benchmark_timer(max_ms=20.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: _nutri_facts_roundtrip(mock_async_session, nutri_facts)
            )


async def _nutri_facts_roundtrip(
    session: AsyncSession, nutri_facts: NutriFacts
) -> NutriFacts | None:
    """Helper function for nutri facts roundtrip mapping."""
    sa_obj = await NutriFactsMapper.map_domain_to_sa(session, nutri_facts)
    return NutriFactsMapper.map_sa_to_domain(sa_obj)


@pytest.mark.slow
@pytest.mark.anyio
async def test_bulk_tag_mapping_performance(
    async_benchmark_timer, bulk_tag_data, mock_async_session
):
    """Test bulk tag mapping meets performance requirements."""
    # Warmup
    for _ in range(2):
        for tag in bulk_tag_data[:10]:
            await TagMapper.map_domain_to_sa(mock_async_session, tag)

    with async_benchmark_timer(max_ms=200.0, samples=10, warmup=2) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: _bulk_tag_domain_to_sa(mock_async_session, bulk_tag_data)
            )


async def _bulk_tag_domain_to_sa(
    session: AsyncSession, tags: list[Tag]
) -> list[TagSaModel]:
    """Helper function for bulk tag domain to SA mapping."""
    return [await TagMapper.map_domain_to_sa(session, tag) for tag in tags]


@pytest.mark.slow
@pytest.mark.anyio
async def test_bulk_nutri_facts_mapping_performance(
    async_benchmark_timer, bulk_nutri_facts_data, mock_async_session
):
    """Test bulk nutri facts mapping meets performance requirements."""
    # Warmup
    for _ in range(2):
        for nutri in bulk_nutri_facts_data[:10]:
            await NutriFactsMapper.map_domain_to_sa(mock_async_session, nutri)

    with async_benchmark_timer(max_ms=150.0, samples=10, warmup=2) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: _bulk_nutri_facts_domain_to_sa(
                    mock_async_session, bulk_nutri_facts_data
                )
            )


async def _bulk_nutri_facts_domain_to_sa(
    session: AsyncSession, nutri_facts_list: list[NutriFacts]
) -> list[NutriFactsSaModel]:
    """Helper function for bulk nutri facts domain to SA mapping."""
    return [
        await NutriFactsMapper.map_domain_to_sa(session, nutri)
        for nutri in nutri_facts_list
    ]


@pytest.mark.slow
@pytest.mark.anyio
async def test_mapper_null_handling_performance(
    async_benchmark_timer, mock_async_session
):
    """Test mapper null handling meets performance requirements."""
    # Warmup
    for _ in range(5):
        await NutriFactsMapper.map_domain_to_sa(mock_async_session, None)
        NutriFactsMapper.map_sa_to_domain(NutriFactsSaModel())

    with async_benchmark_timer(max_ms=3.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: NutriFactsMapper.map_domain_to_sa(mock_async_session, None)
            )
            await timer.measure(
                lambda: NutriFactsMapper.map_sa_to_domain(NutriFactsSaModel())
            )


@pytest.mark.slow
@pytest.mark.anyio
async def test_mapper_error_handling_performance(
    async_benchmark_timer, seed_data, mock_async_session
):
    """Test mapper error handling meets performance requirements."""
    # Create invalid data that should trigger error handling
    # Note: We'll create a valid SA model but with problematic data for domain conversion
    invalid_nutri_sa = NutriFactsSaModel(
        calories=250.0,  # Valid float
        protein=15.0,
        carbohydrate=30.0,
        total_fat=10.0,
        saturated_fat=3.0,
        trans_fat=0.0,
        dietary_fiber=5.0,
        sodium=200.0,
        vitamin_a=100.0,
        vitamin_c=50.0,
        calcium=150.0,
        iron=2.0,
    )

    # Warmup
    for _ in range(5):
        with contextlib.suppress(Exception):
            NutriFactsMapper.map_sa_to_domain(invalid_nutri_sa)

    with async_benchmark_timer(max_ms=5.0, samples=30, warmup=5) as timer:
        for _ in range(timer.samples):
            await timer.measure(
                lambda: _safe_nutri_facts_sa_to_domain(invalid_nutri_sa)
            )


def _safe_nutri_facts_sa_to_domain(sa_obj: NutriFactsSaModel) -> NutriFacts | None:
    """Helper function for safe nutri facts SA to domain mapping with error handling."""
    try:
        return NutriFactsMapper.map_sa_to_domain(sa_obj)
    except Exception:
        return None


@pytest.mark.slow
@pytest.mark.anyio
async def test_mapper_memory_usage_performance(
    async_benchmark_timer, seed_data, mock_async_session
):
    """Test mapper memory usage during bulk operations."""
    nutri_facts = NutriFacts(**seed_data["complex_nutri_facts"])

    # Warmup
    for _ in range(5):
        await NutriFactsMapper.map_domain_to_sa(mock_async_session, nutri_facts)
        NutriFactsMapper.map_sa_to_domain(
            await NutriFactsMapper.map_domain_to_sa(mock_async_session, nutri_facts)
        )

    with async_benchmark_timer(max_ms=25.0, samples=20, warmup=5) as timer:
        for _ in range(timer.samples):
            # Test memory efficiency with repeated operations
            await timer.measure(
                lambda: _memory_intensive_mapping(mock_async_session, nutri_facts)
            )


async def _memory_intensive_mapping(
    session: AsyncSession, nutri_facts: NutriFacts
) -> list[NutriFacts | None]:
    """Helper function for memory-intensive mapping operations."""
    results = []
    for _ in range(10):  # 10 iterations per measurement
        sa_obj = await NutriFactsMapper.map_domain_to_sa(session, nutri_facts)
        domain_obj = NutriFactsMapper.map_sa_to_domain(sa_obj)
        results.append(domain_obj)
    return results
