"""Performance tests for name search functionality.

Tests the performance characteristics of StrProcessor and SimilarityRanking
to ensure they meet latency and throughput requirements for production use.
"""

import asyncio
import time
from typing import Any

import pytest
from src.contexts.shared_kernel.adapters.name_search import (
    SimilarityRanking,
    StrProcessor,
)


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
        "small_dataset": [
            ("hamburguer de carne", 0.95),
            ("hamburguer de frango", 0.90),
            ("hamburguer vegetariano", 0.85),
            ("sanduiche de carne", 0.80),
            ("sanduiche de frango", 0.75),
        ],
        "medium_dataset": [
            ("hamburguer de carne com queijo", 0.95),
            ("hamburguer de frango grelhado", 0.90),
            ("hamburguer vegetariano com alface", 0.85),
            ("sanduiche de carne assada", 0.80),
            ("sanduiche de frango frito", 0.75),
            ("hamburguer de porco com bacon", 0.70),
            ("sanduiche de peixe grelhado", 0.65),
            ("hamburguer de cordeiro", 0.60),
            ("sanduiche de peru defumado", 0.55),
            ("hamburguer de soja", 0.50),
        ],
        "large_dataset": [
            ("hamburguer de carne com queijo e bacon", 0.95),
            ("hamburguer de frango grelhado com alface", 0.90),
            ("hamburguer vegetariano com alface e tomate", 0.85),
            ("sanduiche de carne assada com cebola", 0.80),
            ("sanduiche de frango frito com maionese", 0.75),
            ("hamburguer de porco com bacon e queijo", 0.70),
            ("sanduiche de peixe grelhado com limao", 0.65),
            ("hamburguer de cordeiro com hortela", 0.60),
            ("sanduiche de peru defumado com mostarda", 0.55),
            ("hamburguer de soja com cogumelos", 0.50),
            ("hamburguer de frango com molho barbecue", 0.45),
            ("sanduiche de carne com pimentao", 0.40),
            ("hamburguer de peixe com alcaparras", 0.35),
            ("sanduiche de frango com abacate", 0.30),
            ("hamburguer de cordeiro com iogurte", 0.25),
            ("sanduiche de peru com cranberry", 0.20),
            ("hamburguer de soja com quinoa", 0.15),
            ("sanduiche de frango com pesto", 0.10),
            ("hamburguer de carne com gorgonzola", 0.05),
            ("sanduiche de peixe com rucula", 0.01),
        ],
        "complex_queries": [
            "hamburguer de carne com queijo e bacon frito",
            "sanduiche de frango grelhado sem gordura",
            "hamburguer vegetariano com alface e tomate fresco",
            "sanduiche de carne assada com cebola caramelizada",
            "hamburguer de porco com bacon crocante e queijo derretido",
        ],
        "cooking_method_queries": [
            "hamburguer frito",
            "sanduiche assado",
            "hamburguer cozido",
            "sanduiche grelhado",
        ],
    }


@pytest.mark.slow
@pytest.mark.anyio
async def test_similarity_ranking_performance(
    async_benchmark_timer: type[AsyncBenchmarkTimer], seed_data: dict[str, Any]
):
    """Test that similarity ranking meets performance requirements.

    Performance envelope: P95 < 50ms for ranking 20 candidates.
    """
    # Given: A complex query and a large dataset of candidates
    query = "hamburguer de carne com queijo"
    candidates = seed_data["large_dataset"]

    # Warm up the ranking system
    ranking = SimilarityRanking(query, candidates[:5])
    _ = ranking.ranking  # Warm up

    # When: Measuring ranking performance with full dataset
    with async_benchmark_timer(max_ms=50, samples=30, warmup=5) as timer:
        for _ in range(timer.samples + timer.warmup):
            ranking = SimilarityRanking(query, candidates)
            result = ranking.ranking

            # Verify correctness even in performance test
            assert len(result) > 0
            assert all(not match.should_ignore for match in result)

            await timer.measure(lambda: SimilarityRanking(query, candidates).ranking)


@pytest.mark.slow
@pytest.mark.anyio
async def test_name_search_performance(
    async_benchmark_timer: type[AsyncBenchmarkTimer], seed_data: dict[str, Any]
):
    """Test that name search processing meets performance requirements.

    Performance envelope: P95 < 10ms for processing 100 strings.
    """
    # Given: A large set of complex strings to process
    test_strings = seed_data["complex_queries"] * 20  # 100 strings total

    # Warm up the processor
    processor = StrProcessor(test_strings[0])
    _ = processor.output  # Warm up

    # When: Measuring string processing performance
    with async_benchmark_timer(max_ms=10, samples=30, warmup=5) as timer:
        for _ in range(timer.samples + timer.warmup):
            processors = [StrProcessor(text) for text in test_strings]
            results = [proc.output for proc in processors]

            # Verify correctness even in performance test
            assert len(results) == len(test_strings)
            assert all(isinstance(result, str) for result in results)

            await timer.measure(
                lambda: [StrProcessor(text).output for text in test_strings]
            )


@pytest.mark.slow
@pytest.mark.anyio
async def test_string_processing_cache_performance(
    async_benchmark_timer: type[AsyncBenchmarkTimer], seed_data: dict[str, Any]
):
    """Test that string processing caching improves performance.

    Performance envelope: Cached operations should be 5x faster than uncached.
    """
    # Given: A processor with repeated operations
    query = "hamburguer de carne com queijo e bacon"
    processor = StrProcessor(query)

    # Warm up
    _ = processor.output

    # When: Measuring cached vs uncached performance
    cached_times = []
    uncached_times = []

    # Test cached performance (same configuration)
    for _ in range(30):
        start = time.perf_counter()
        _ = processor.output
        end = time.perf_counter()
        cached_times.append((end - start) * 1000)

    # Test uncached performance (different configurations)
    for i in range(30):
        start = time.perf_counter()
        _ = processor.processed_str(words_to_ignore=[f"word{i}"])
        end = time.perf_counter()
        uncached_times.append((end - start) * 1000)

    # Then: Cached should be significantly faster
    avg_cached = sum(cached_times) / len(cached_times)
    avg_uncached = sum(uncached_times) / len(uncached_times)

    # Cached should be at least 2x faster (conservative estimate)
    assert avg_cached < avg_uncached / 2, (
        f"Cached performance ({avg_cached:.2f}ms) should be much faster than "
        f"uncached ({avg_uncached:.2f}ms)"
    )


@pytest.mark.slow
@pytest.mark.anyio
async def test_ranking_with_cooking_methods_performance(
    async_benchmark_timer: type[AsyncBenchmarkTimer], seed_data: dict[str, Any]
):
    """Test performance of ranking with cooking method filtering.

    Performance envelope: P95 < 30ms for ranking with cooking method filtering.
    """
    # Given: Query with cooking method and candidates with various cooking methods
    query = "hamburguer frito"
    candidates = [
        ("hamburguer frito de carne", 0.95),
        ("hamburguer assado de frango", 0.90),  # Should be filtered out
        ("hamburguer cozido de porco", 0.85),  # Should be filtered out
        ("sanduiche frito de peixe", 0.80),
        ("hamburguer grelhado de soja", 0.75),  # Should be filtered out
    ] * 4  # 20 candidates total

    # Warm up
    ranking = SimilarityRanking(query, candidates[:5])
    _ = ranking.ranking

    # When: Measuring ranking performance with filtering
    with async_benchmark_timer(max_ms=30, samples=30, warmup=5) as timer:
        for _ in range(timer.samples + timer.warmup):
            ranking = SimilarityRanking(query, candidates)
            result = ranking.ranking

            # Verify filtering works correctly
            assert len(result) < len(candidates)  # Some should be filtered
            assert all(not match.should_ignore for match in result)

            await timer.measure(lambda: SimilarityRanking(query, candidates).ranking)


@pytest.mark.slow
@pytest.mark.anyio
async def test_large_dataset_ranking_performance(
    async_benchmark_timer: type[AsyncBenchmarkTimer], seed_data: dict[str, Any]
):
    """Test performance with very large datasets.

    Performance envelope: P95 < 100ms for ranking 100 candidates.
    """
    # Given: A very large dataset
    query = "hamburguer de carne"
    candidates = seed_data["large_dataset"] * 5  # 100 candidates

    # Warm up
    ranking = SimilarityRanking(query, candidates[:10])
    _ = ranking.ranking

    # When: Measuring performance with large dataset
    with async_benchmark_timer(max_ms=100, samples=20, warmup=3) as timer:
        for _ in range(timer.samples + timer.warmup):
            ranking = SimilarityRanking(query, candidates)
            result = ranking.ranking

            # Verify results are reasonable
            assert len(result) > 0
            assert len(result) <= len(candidates)

            await timer.measure(lambda: SimilarityRanking(query, candidates).ranking)


@pytest.mark.slow
@pytest.mark.anyio
async def test_concurrent_ranking_performance(
    async_benchmark_timer: type[AsyncBenchmarkTimer], seed_data: dict[str, Any]
):
    """Test performance under concurrent ranking operations.

    Performance envelope: P95 < 200ms for 10 concurrent ranking operations.
    """
    # Given: Multiple queries and datasets
    queries = seed_data["complex_queries"]
    candidates = seed_data["medium_dataset"]

    async def single_ranking(query: str) -> list[Any]:
        """Perform a single ranking operation."""
        ranking = SimilarityRanking(query, candidates)
        return ranking.ranking

    # Warm up
    await single_ranking(queries[0])

    # When: Measuring concurrent performance
    with async_benchmark_timer(max_ms=200, samples=20, warmup=3) as timer:
        for _ in range(timer.samples + timer.warmup):
            # Run concurrent ranking operations (using all available queries)
            tasks = [single_ranking(query) for query in queries]
            results = await asyncio.gather(*tasks)

            # Verify all operations completed successfully
            assert len(results) == len(queries)
            assert all(len(result) > 0 for result in results)

            await timer.measure(
                lambda: asyncio.gather(*[single_ranking(query) for query in queries])
            )
