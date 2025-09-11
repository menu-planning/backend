import gc
import time

import pytest
from old_tests_v0.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import (
    create_complex_recipe,
    create_conversion_performance_dataset_for_domain_recipe,
    create_minimal_recipe,
    create_nested_object_validation_dataset_for_domain_recipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)

"""
ApiRecipe Performance Test Suite

Test classes for performance benchmarks, scalability tests, and stress testing.
"""


class TestApiRecipePerformance:
    """
    Test suite for performance tests (environment-agnostic).
    """

    # =============================================================================
    # PERFORMANCE BENCHMARKS (ENVIRONMENT-AGNOSTIC)
    # =============================================================================

    def test_from_domain_conversion_efficiency_per_100_operations_benchmark(
        self, domain_recipe
    ):
        """Test from_domain conversion efficiency using throughput measurement."""
        # Measure baseline with multiple samples for stability
        baseline_times = []
        for _ in range(10):  # Take multiple samples
            start_time = time.perf_counter()
            ApiRecipe.from_domain(domain_recipe)
            baseline_times.append(time.perf_counter() - start_time)

        # Use median to avoid outliers from initialization overhead
        baseline_times.sort()
        single_op_time = baseline_times[len(baseline_times) // 2]

        # Measure batch operations
        start_time = time.perf_counter()
        for _ in range(100):  # Test 100 conversions for reliable timing
            ApiRecipe.from_domain(domain_recipe)
        batch_time = time.perf_counter() - start_time

        # Efficiency test: batch should scale reasonably
        expected_batch_time = single_op_time * 100
        efficiency_ratio = batch_time / expected_batch_time

        # More realistic bounds that account for caching and initialization effects
        assert (
            efficiency_ratio < 3.0
        ), f"from_domain batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert (
            efficiency_ratio > 0.1
        ), f"from_domain batch timing suspiciously fast: {efficiency_ratio:.2f}x expected time"

        # Additional throughput validation
        throughput = 100 / batch_time
        assert (
            throughput > 50
        ), f"from_domain throughput too low: {throughput:.1f} ops/sec"

    def test_to_domain_conversion_efficiency_per_100_operations_benchmark(
        self, complex_recipe
    ):
        """Test to_domain conversion efficiency using throughput measurement."""
        # Measure baseline with multiple samples for stability
        baseline_times = []
        for _ in range(10):  # Take multiple samples
            start_time = time.perf_counter()
            complex_recipe.to_domain()
            baseline_times.append(time.perf_counter() - start_time)

        # Use median to avoid outliers from initialization overhead
        baseline_times.sort()
        single_op_time = baseline_times[len(baseline_times) // 2]

        # Measure batch operations
        start_time = time.perf_counter()
        for _ in range(100):  # Test 100 conversions
            complex_recipe.to_domain()
        batch_time = time.perf_counter() - start_time

        # Efficiency test: batch should scale reasonably
        expected_batch_time = single_op_time * 100
        efficiency_ratio = batch_time / expected_batch_time

        # More realistic bounds that account for caching and initialization effects
        assert (
            efficiency_ratio < 3.0
        ), f"to_domain batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert (
            efficiency_ratio > 0.1
        ), f"to_domain batch timing suspiciously fast: {efficiency_ratio:.2f}x expected time"

        # Additional throughput validation
        throughput = 100 / batch_time
        assert (
            throughput > 50
        ), f"to_domain throughput too low: {throughput:.1f} ops/sec"

    def test_from_orm_model_conversion_efficiency_per_100_operations_benchmark(
        self, real_orm_recipe
    ):
        """Test from_orm_model conversion efficiency using throughput measurement."""
        # Measure baseline with multiple samples for stability
        baseline_times = []
        for _ in range(10):  # Take multiple samples
            start_time = time.perf_counter()
            ApiRecipe.from_orm_model(real_orm_recipe)
            baseline_times.append(time.perf_counter() - start_time)

        # Use median to avoid outliers from initialization overhead
        baseline_times.sort()
        single_op_time = baseline_times[len(baseline_times) // 2]

        # Measure batch operations
        start_time = time.perf_counter()
        for _ in range(100):  # Test 100 conversions
            ApiRecipe.from_orm_model(real_orm_recipe)
        batch_time = time.perf_counter() - start_time

        # Efficiency test: batch should scale reasonably
        expected_batch_time = single_op_time * 100
        efficiency_ratio = batch_time / expected_batch_time

        # More realistic bounds that account for caching and initialization effects
        assert (
            efficiency_ratio < 3.0
        ), f"from_orm_model batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert (
            efficiency_ratio > 0.05
        ), f"from_orm_model batch timing suspiciously fast: {efficiency_ratio:.2f}x expected time"

        # Additional throughput validation
        throughput = 100 / batch_time
        assert (
            throughput > 50
        ), f"from_orm_model throughput too low: {throughput:.1f} ops/sec"

    def test_complete_four_layer_conversion_cycle_efficiency_per_50_operations_benchmark(
        self, simple_recipe
    ):
        """Test complete four-layer conversion cycle efficiency using adaptive measurement."""
        # Measure individual operations with multiple samples
        individual_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            domain_recipe = simple_recipe.to_domain()
            api_from_domain = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            individual_times.append(time.perf_counter() - start_time)

        # Use median for stability
        expected_single_cycle = sorted(individual_times)[len(individual_times) // 2]

        # Measure complete cycle performance
        start_time = time.perf_counter()
        for _ in range(50):  # Test 50 complete cycles
            domain_recipe = simple_recipe.to_domain()
            api_from_domain = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            assert orm_kwargs["id"] == simple_recipe.id

        batch_time = time.perf_counter() - start_time
        expected_batch_time = expected_single_cycle * 50
        efficiency_ratio = batch_time / expected_batch_time

        # Environment-agnostic: Allow wider tolerance for complex operations
        assert (
            efficiency_ratio < 10.0
        ), f"Complete cycle efficiency severely degraded: {efficiency_ratio:.2f}x expected time"
        assert (
            efficiency_ratio > 0.1
        ), f"Complete cycle timing suspiciously fast: {efficiency_ratio:.2f}x expected time"

        # Throughput validation
        throughput = 50 / batch_time
        assert (
            throughput > 5
        ), f"Complete cycle throughput too low: {throughput:.1f} ops/sec"

    def test_large_collection_vs_individual_conversion_efficiency_benchmark(self):
        """Test efficiency of large collection processing using adaptive thresholds."""

        large_recipes = create_nested_object_validation_dataset_for_domain_recipe(
            count=100
        )

        # Measure individual operation baseline with multiple samples
        single_recipe = large_recipes[0]
        individual_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            api_recipe = ApiRecipe.from_domain(single_recipe)
            orm_kwargs = api_recipe.to_orm_kwargs()
            individual_times.append(time.perf_counter() - start_time)

        single_op_time = sorted(individual_times)[len(individual_times) // 2]

        # Measure batch processing
        start_time = time.perf_counter()
        for domain_recipe in large_recipes:
            api_recipe = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_recipe.to_orm_kwargs()
            assert api_recipe.id == domain_recipe.id
            assert orm_kwargs["id"] == domain_recipe.id

        batch_time = time.perf_counter() - start_time

        # Environment-agnostic efficiency test: Focus on scalability rather than absolute ratios
        expected_batch_time = single_op_time * len(large_recipes)
        efficiency_ratio = batch_time / expected_batch_time

        # Allow wide tolerance for environment variations
        assert (
            efficiency_ratio < 20.0
        ), f"Large collection efficiency severely degraded: {efficiency_ratio:.2f}x expected time"
        assert (
            efficiency_ratio > 0.1
        ), f"Large collection timing suspiciously fast: {efficiency_ratio:.2f}x expected time"

        # Throughput-based validation
        throughput = len(large_recipes) / batch_time
        assert (
            throughput > 1
        ), f"Large collection throughput too low: {throughput:.1f} ops/sec"

    def test_conversion_throughput_validation(self):
        """Test conversion throughput meets minimum performance standards."""

        # Create diverse test dataset
        recipes = []
        recipes.extend(
            create_conversion_performance_dataset_for_domain_recipe(count=20)[
                "domain_recipes"
            ]
        )
        recipes.extend([create_minimal_recipe() for _ in range(20)])
        recipes.extend([create_complex_recipe() for _ in range(10)])

        # Measure throughput for different conversion types
        throughput_data = {}

        # from_domain throughput
        start_time = time.perf_counter()
        api_recipes = [ApiRecipe.from_domain(recipe) for recipe in recipes]
        from_domain_time = time.perf_counter() - start_time
        throughput_data["from_domain"] = len(recipes) / from_domain_time

        # to_domain throughput
        start_time = time.perf_counter()
        domain_recipes = [api_recipe.to_domain() for api_recipe in api_recipes]
        to_domain_time = time.perf_counter() - start_time
        throughput_data["to_domain"] = len(api_recipes) / to_domain_time

        # to_orm_kwargs throughput
        start_time = time.perf_counter()
        orm_kwargs_list = [api_recipe.to_orm_kwargs() for api_recipe in api_recipes]
        to_orm_time = time.perf_counter() - start_time
        throughput_data["to_orm_kwargs"] = len(api_recipes) / to_orm_time

        # Validate throughput minimums
        assert (
            throughput_data["from_domain"] > 100
        ), f"from_domain throughput too low: {throughput_data['from_domain']:.1f} ops/sec"
        assert (
            throughput_data["to_domain"] > 100
        ), f"to_domain throughput too low: {throughput_data['to_domain']:.1f} ops/sec"
        assert (
            throughput_data["to_orm_kwargs"] > 100
        ), f"to_orm_kwargs throughput too low: {throughput_data['to_orm_kwargs']:.1f} ops/sec"

        # Validate results
        assert len(api_recipes) == len(recipes)
        assert len(domain_recipes) == len(api_recipes)
        assert len(orm_kwargs_list) == len(api_recipes)

    def test_memory_efficiency_validation(self):
        """Test memory efficiency using adaptive object count thresholds."""
        # Get baseline memory usage with stability
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform operations with smaller dataset for more predictable results
        recipes = create_conversion_performance_dataset_for_domain_recipe(count=20)[
            "domain_recipes"
        ]
        api_recipes = []

        for recipe in recipes:
            api_recipe = ApiRecipe.from_domain(recipe)
            api_recipes.append(api_recipe)

            # Validate operation
            domain_back = api_recipe.to_domain()
            assert domain_back.id == recipe.id

        # Check object growth
        gc.collect()
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Environment-agnostic memory validation: Focus on reasonable growth
        objects_per_operation = object_growth / len(recipes)
        assert (
            objects_per_operation < 500
        ), f"Excessive objects created per operation: {objects_per_operation:.1f}"
        assert (
            objects_per_operation > 0
        ), f"No objects created: {objects_per_operation:.1f}"

        # Ensure operations complete successfully
        assert len(api_recipes) == len(recipes), "Not all operations completed"

        # Clean up
        del api_recipes, recipes
        gc.collect()

    @pytest.mark.parametrize("size", [10, 50, 100])
    def test_scalability_performance(self, size, simple_recipe):
        """Test scalability with different dataset sizes."""
        # Measure performance for this size
        start_time = time.perf_counter()
        for _ in range(size):
            domain_recipe = simple_recipe.to_domain()
            api_recipe = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_recipe.to_orm_kwargs()
            assert api_recipe.id == simple_recipe.id

        operation_time = time.perf_counter() - start_time
        per_operation_time = operation_time / size

        # Performance should be reasonable for this size
        assert (
            per_operation_time < 0.01
        ), f"Per-operation time too high for size {size}: {per_operation_time:.6f}s"

        # Throughput should be reasonable
        throughput = size / operation_time
        assert (
            throughput > 100
        ), f"Throughput too low for size {size}: {throughput:.1f} ops/sec"

    def test_scalability_performance_relationship(self, simple_recipe):
        """Test relationship between different dataset sizes for scaling efficiency."""
        sizes = [10, 50, 100]
        performance_data = []

        for size in sizes:
            # Measure performance for this size
            start_time = time.perf_counter()
            for _ in range(size):
                domain_recipe = simple_recipe.to_domain()
                api_recipe = ApiRecipe.from_domain(domain_recipe)
                orm_kwargs = api_recipe.to_orm_kwargs()
                assert api_recipe.id == simple_recipe.id

            operation_time = time.perf_counter() - start_time
            performance_data.append((size, operation_time))

        # Check that performance scales reasonably
        first_count, first_time = performance_data[0]
        last_count, last_time = performance_data[-1]

        # Calculate scaling factor
        count_ratio = last_count / first_count
        time_ratio = last_time / first_time

        # Performance should scale better than quadratically
        scaling_efficiency = time_ratio / (count_ratio**2)
        assert (
            scaling_efficiency < 1.0
        ), f"Performance scales worse than quadratically: {scaling_efficiency:.2f}"

        # Performance should scale at least linearly (some overhead is expected)
        linear_efficiency = time_ratio / count_ratio
        assert (
            linear_efficiency < 3.0
        ), f"Performance scales too poorly: {linear_efficiency:.2f}x linear"


class TestApiRecipeStressAndPerformance:
    """
    Test suite for stress and performance testing (environment-agnostic).
    """

    def test_massive_collections_handling(self):
        """Test handling of massive collections using throughput efficiency."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_massive_collections,
        )

        massive_kwargs = create_api_recipe_with_massive_collections()

        # Measure creation throughput
        start_time = time.perf_counter()
        recipe = ApiRecipe(**massive_kwargs)
        creation_time = time.perf_counter() - start_time

        # Assess collection sizes
        assert recipe.ingredients is not None
        assert recipe.ratings is not None
        assert recipe.tags is not None
        collection_sizes = {
            "ingredients": len(recipe.ingredients),
            "ratings": len(recipe.ratings),
            "tags": len(recipe.tags),
            "total_elements": len(recipe.ingredients)
            + len(recipe.ratings)
            + len(recipe.tags),
        }

        # Should handle massive collections efficiently
        assert collection_sizes["ingredients"] == 100
        assert collection_sizes["ratings"] == 1000
        assert collection_sizes["tags"] == 100

        # Throughput should scale sub-linearly with collection size
        throughput_efficiency = creation_time / max(
            1, collection_sizes["total_elements"] / 1000
        )
        assert (
            throughput_efficiency < 0.1
        ), f"Massive collection throughput inefficient: {throughput_efficiency:.6f}s per 1000 elements"

    def test_stress_dataset_performance(self):
        """Test performance with stress dataset using success rate and efficiency metrics."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_stress_test_dataset_for_api_recipe,
        )

        stress_dataset = create_stress_test_dataset_for_api_recipe(count=100)

        # Measure processing efficiency
        start_time = time.perf_counter()
        created_recipes = []
        failed_count = 0

        for stress_kwargs in stress_dataset:
            try:
                recipe = ApiRecipe(**stress_kwargs)
                created_recipes.append(recipe)

                # Validate round-trip works
                domain_recipe = recipe.to_domain()
                assert domain_recipe.id == recipe.id

            except Exception:
                failed_count += 1
                # Some stress test cases might intentionally fail
                if failed_count > len(stress_dataset) * 0.1:  # Allow up to 10% failures
                    raise

        processing_time = time.perf_counter() - start_time
        success_rate = len(created_recipes) / len(stress_dataset)

        # Stress testing validation
        assert success_rate > 0.8, f"Success rate too low: {success_rate:.2f}"

        # Processing efficiency
        throughput = len(stress_dataset) / processing_time
        assert (
            throughput > 10
        ), f"Stress test throughput too low: {throughput:.1f} ops/sec"

    @pytest.mark.parametrize(
        "scenario_name,conversion_func",
        [
            ("to_domain", lambda r: r.to_domain()),
            ("to_orm_kwargs", lambda r: r.to_orm_kwargs()),
        ],
    )
    def test_bulk_conversion_performance(
        self, scenario_name, conversion_func, simple_recipe
    ):
        """Test bulk conversion performance for specific conversion scenario."""
        # Measure bulk performance
        start_time = time.perf_counter()
        results = []

        for _ in range(200):  # Bulk operations
            result = conversion_func(simple_recipe)
            results.append(result)

            # Validate some results
            if scenario_name == "to_domain":
                assert result.id == simple_recipe.id
            elif scenario_name == "to_orm_kwargs":
                assert result["id"] == simple_recipe.id

        bulk_time = time.perf_counter() - start_time
        throughput = len(results) / bulk_time

        # Bulk performance validation
        assert (
            throughput > 50
        ), f"Bulk {scenario_name} throughput too low: {throughput:.1f} ops/sec"
        assert len(results) == 200, f"Not all {scenario_name} operations completed"
