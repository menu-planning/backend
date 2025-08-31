#!/usr/bin/env python3
"""
Memory usage analysis script for logging standardization.
Profiles memory usage with structured logging to verify no memory leaks or excessive allocation.
"""

import gc
import json
import sys
import time
import tracemalloc
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.logging.logger import (
        StructlogFactory,
        correlation_id_ctx,
        generate_correlation_id,
        set_correlation_id,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    print("Warning: Could not import logging modules. Using mock implementations for testing.")
    IMPORTS_AVAILABLE = False

    # Mock implementations for testing
    class MockCorrelationCtx:
        def __init__(self):
            self._value = "00000000-0000-0000-0000-000000000000"

        def set(self, value):
            self._value = value

        def get(self):
            return self._value

    class MockLogger:
        def __init__(self, name: str = "test_logger"):
            self.name = name
            # Use a circular buffer to prevent unlimited memory growth
            self.max_messages = 1000
            self.logged_messages = []
            self.total_messages = 0

        def _log_message(self, level: str, message: str, **kwargs):
            """Internal method to handle logging with memory management."""
            # Create log entry (simulating real logging behavior)
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "logger": self.name,
                "message": message,
                "correlation_id": correlation_id_ctx.get(),
                **kwargs
            }
            
            # Simulate writing to output (like real logging would)
            # In real logging, this would go to stdout/file, not accumulate in memory
            self.total_messages += 1
            
            # Keep only recent messages to simulate real logging behavior
            if len(self.logged_messages) >= self.max_messages:
                self.logged_messages.pop(0)  # Remove oldest message
            
            self.logged_messages.append(log_entry)

        def info(self, message, **kwargs):
            self._log_message("info", message, **kwargs)

        def error(self, message, **kwargs):
            self._log_message("error", message, **kwargs)

        def debug(self, message, **kwargs):
            self._log_message("debug", message, **kwargs)

        def warning(self, message, **kwargs):
            self._log_message("warning", message, **kwargs)

    class MockStructlogFactory:
        @classmethod
        def configure(cls, **kwargs):
            pass

        @classmethod
        def get_logger(cls, name=""):
            return MockLogger(name)

    def mock_set_correlation_id(correlation_id):
        correlation_id_ctx.set(correlation_id)

    def mock_generate_correlation_id():
        cid = uuid.uuid4().hex[:8]
        correlation_id_ctx.set(cid)
        return cid

    StructlogFactory = MockStructlogFactory
    correlation_id_ctx = MockCorrelationCtx()
    set_correlation_id = mock_set_correlation_id
    generate_correlation_id = mock_generate_correlation_id


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a specific point in time."""
    timestamp: float
    current_memory_mb: float
    peak_memory_mb: float
    memory_blocks: int
    top_allocations: List[Tuple[str, int]]  # (traceback, size)


@dataclass
class MemoryAnalysisResult:
    """Results from memory usage analysis."""
    test_name: str
    initial_memory_mb: float
    final_memory_mb: float
    peak_memory_mb: float
    memory_growth_mb: float
    memory_growth_percent: float
    total_allocations: int
    potential_leaks_detected: bool
    snapshots: List[MemorySnapshot]
    assessment: str


class MemoryUsageAnalyzer:
    """Analyzes memory usage patterns for structured logging."""

    def __init__(self):
        self.results: List[MemoryAnalysisResult] = []
        self.logger = StructlogFactory.get_logger("memory_analyzer")

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            # Fallback: use tracemalloc if psutil not available
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                return current / 1024 / 1024
            return 0.0

    def take_memory_snapshot(self) -> MemorySnapshot:
        """Take a snapshot of current memory usage."""
        current_memory = self.get_memory_usage()
        
        if tracemalloc.is_tracing():
            current_traced, peak_traced = tracemalloc.get_traced_memory()
            peak_memory = peak_traced / 1024 / 1024
            
            # Get top allocations
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('traceback')
            
            top_allocations = []
            for stat in top_stats[:5]:  # Top 5 allocations
                traceback_str = '\n'.join(stat.traceback.format())
                top_allocations.append((traceback_str, stat.size))
            
            memory_blocks = len(top_stats)
        else:
            peak_memory = current_memory
            top_allocations = []
            memory_blocks = 0

        return MemorySnapshot(
            timestamp=time.perf_counter(),
            current_memory_mb=current_memory,
            peak_memory_mb=peak_memory,
            memory_blocks=memory_blocks,
            top_allocations=top_allocations
        )

    def analyze_basic_logging_memory(self) -> MemoryAnalysisResult:
        """Analyze memory usage for basic logging operations."""
        test_name = "Basic Logging Memory Usage"
        print(f"\n🔍 Analyzing: {test_name}")
        
        # Start memory tracing
        tracemalloc.start()
        gc.collect()  # Clean up before starting
        
        initial_snapshot = self.take_memory_snapshot()
        snapshots = [initial_snapshot]
        
        logger = StructlogFactory.get_logger("memory_test.basic")
        
        # Perform logging operations
        iterations = 10000
        for i in range(iterations):
            correlation_id = generate_correlation_id()
            
            logger.info(
                f"Basic logging test iteration {i}",
                iteration=i,
                correlation_id=correlation_id,
                test_data={"key": f"value_{i}", "timestamp": datetime.now().isoformat()}
            )
            
            if i % 2000 == 0:  # Take snapshots every 2000 iterations
                snapshots.append(self.take_memory_snapshot())
        
        # Take final snapshot
        final_snapshot = self.take_memory_snapshot()
        snapshots.append(final_snapshot)
        
        # Calculate memory growth
        memory_growth_mb = final_snapshot.current_memory_mb - initial_snapshot.current_memory_mb
        memory_growth_percent = (memory_growth_mb / initial_snapshot.current_memory_mb) * 100 if initial_snapshot.current_memory_mb > 0 else 0
        
        # Assess potential leaks
        potential_leaks = memory_growth_mb > 10.0  # More than 10MB growth considered potential leak
        
        assessment = "PASS" if memory_growth_mb < 5.0 else "INVESTIGATE" if memory_growth_mb < 10.0 else "FAIL"
        
        tracemalloc.stop()
        
        result = MemoryAnalysisResult(
            test_name=test_name,
            initial_memory_mb=initial_snapshot.current_memory_mb,
            final_memory_mb=final_snapshot.current_memory_mb,
            peak_memory_mb=final_snapshot.peak_memory_mb,
            memory_growth_mb=memory_growth_mb,
            memory_growth_percent=memory_growth_percent,
            total_allocations=iterations,
            potential_leaks_detected=potential_leaks,
            snapshots=snapshots,
            assessment=assessment
        )
        
        self.results.append(result)
        print(f"   Memory growth: {memory_growth_mb:.2f}MB ({memory_growth_percent:.1f}%)")
        print(f"   Assessment: {assessment}")
        
        return result

    def analyze_high_volume_logging_memory(self) -> MemoryAnalysisResult:
        """Analyze memory usage for high-volume logging scenarios."""
        test_name = "High Volume Logging Memory Usage"
        print(f"\n🔍 Analyzing: {test_name}")
        
        tracemalloc.start()
        gc.collect()
        
        initial_snapshot = self.take_memory_snapshot()
        snapshots = [initial_snapshot]
        
        logger = StructlogFactory.get_logger("memory_test.high_volume")
        
        # High-volume logging with complex data structures
        iterations = 50000
        for i in range(iterations):
            correlation_id = generate_correlation_id()
            
            # Create complex log data to stress test memory usage
            complex_data = {
                "request_id": str(uuid.uuid4()),
                "user_data": {
                    "user_id": f"user_{i}",
                    "session_id": str(uuid.uuid4()),
                    "preferences": {
                        "theme": "dark",
                        "language": "en",
                        "notifications": True,
                        "features": [f"feature_{j}" for j in range(5)]
                    }
                },
                "request_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "ip_address": f"192.168.1.{i % 255}",
                    "user_agent": "Mozilla/5.0 (Test Browser)",
                    "headers": {f"header_{j}": f"value_{j}" for j in range(3)}
                },
                "performance_metrics": {
                    "response_time": 0.123 + (i * 0.001),
                    "memory_usage": 1024 + i,
                    "cpu_usage": 0.5 + (i * 0.0001)
                }
            }
            
            logger.info(
                f"High volume logging iteration {i}",
                iteration=i,
                correlation_id=correlation_id,
                **complex_data
            )
            
            # Occasionally log errors with stack traces
            if i % 1000 == 0:
                try:
                    raise ValueError(f"Test error for iteration {i}")
                except ValueError as e:
                    logger.error(
                        "Test error occurred",
                        iteration=i,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        correlation_id=correlation_id,
                        exc_info=True
                    )
                
                snapshots.append(self.take_memory_snapshot())
        
        final_snapshot = self.take_memory_snapshot()
        snapshots.append(final_snapshot)
        
        memory_growth_mb = final_snapshot.current_memory_mb - initial_snapshot.current_memory_mb
        memory_growth_percent = (memory_growth_mb / initial_snapshot.current_memory_mb) * 100 if initial_snapshot.current_memory_mb > 0 else 0
        
        potential_leaks = memory_growth_mb > 20.0  # Higher threshold for high-volume test
        assessment = "PASS" if memory_growth_mb < 10.0 else "INVESTIGATE" if memory_growth_mb < 20.0 else "FAIL"
        
        tracemalloc.stop()
        
        result = MemoryAnalysisResult(
            test_name=test_name,
            initial_memory_mb=initial_snapshot.current_memory_mb,
            final_memory_mb=final_snapshot.current_memory_mb,
            peak_memory_mb=final_snapshot.peak_memory_mb,
            memory_growth_mb=memory_growth_mb,
            memory_growth_percent=memory_growth_percent,
            total_allocations=iterations,
            potential_leaks_detected=potential_leaks,
            snapshots=snapshots,
            assessment=assessment
        )
        
        self.results.append(result)
        print(f"   Memory growth: {memory_growth_mb:.2f}MB ({memory_growth_percent:.1f}%)")
        print(f"   Assessment: {assessment}")
        
        return result

    def analyze_correlation_id_memory(self) -> MemoryAnalysisResult:
        """Analyze memory usage for correlation ID operations."""
        test_name = "Correlation ID Memory Usage"
        print(f"\n🔍 Analyzing: {test_name}")
        
        tracemalloc.start()
        gc.collect()
        
        initial_snapshot = self.take_memory_snapshot()
        snapshots = [initial_snapshot]
        
        logger = StructlogFactory.get_logger("memory_test.correlation")
        
        # Test correlation ID memory patterns
        iterations = 25000
        correlation_ids = []
        
        for i in range(iterations):
            # Generate and store correlation IDs
            correlation_id = generate_correlation_id()
            correlation_ids.append(correlation_id)
            
            # Set correlation ID context
            set_correlation_id(correlation_id)
            
            logger.info(
                f"Correlation ID test {i}",
                iteration=i,
                correlation_id=correlation_id,
                context_data={"operation": "memory_test", "batch": i // 1000}
            )
            
            # Periodically clear old correlation IDs to test cleanup
            if i % 5000 == 0 and i > 0:
                # Clear some old correlation IDs
                correlation_ids = correlation_ids[-1000:]  # Keep only last 1000
                gc.collect()  # Force garbage collection
                snapshots.append(self.take_memory_snapshot())
        
        final_snapshot = self.take_memory_snapshot()
        snapshots.append(final_snapshot)
        
        memory_growth_mb = final_snapshot.current_memory_mb - initial_snapshot.current_memory_mb
        memory_growth_percent = (memory_growth_mb / initial_snapshot.current_memory_mb) * 100 if initial_snapshot.current_memory_mb > 0 else 0
        
        potential_leaks = memory_growth_mb > 15.0
        assessment = "PASS" if memory_growth_mb < 8.0 else "INVESTIGATE" if memory_growth_mb < 15.0 else "FAIL"
        
        tracemalloc.stop()
        
        result = MemoryAnalysisResult(
            test_name=test_name,
            initial_memory_mb=initial_snapshot.current_memory_mb,
            final_memory_mb=final_snapshot.current_memory_mb,
            peak_memory_mb=final_snapshot.peak_memory_mb,
            memory_growth_mb=memory_growth_mb,
            memory_growth_percent=memory_growth_percent,
            total_allocations=iterations,
            potential_leaks_detected=potential_leaks,
            snapshots=snapshots,
            assessment=assessment
        )
        
        self.results.append(result)
        print(f"   Memory growth: {memory_growth_mb:.2f}MB ({memory_growth_percent:.1f}%)")
        print(f"   Assessment: {assessment}")
        
        return result

    def analyze_long_running_memory(self) -> MemoryAnalysisResult:
        """Analyze memory usage for long-running logging scenarios."""
        test_name = "Long Running Memory Usage"
        print(f"\n🔍 Analyzing: {test_name}")
        
        tracemalloc.start()
        gc.collect()
        
        initial_snapshot = self.take_memory_snapshot()
        snapshots = [initial_snapshot]
        
        logger = StructlogFactory.get_logger("memory_test.long_running")
        
        # Simulate long-running application with periodic logging
        iterations = 20000
        batch_size = 1000
        
        for batch in range(iterations // batch_size):
            # Simulate a batch of operations
            for i in range(batch_size):
                correlation_id = generate_correlation_id()
                
                logger.info(
                    f"Long running operation {batch * batch_size + i}",
                    batch=batch,
                    operation=i,
                    correlation_id=correlation_id,
                    system_state={
                        "active_connections": 50 + (i % 20),
                        "memory_usage": f"{100 + batch}MB",
                        "cpu_usage": f"{20 + (i % 10)}%"
                    }
                )
                
                # Occasionally log warnings and errors
                if i % 100 == 0:
                    logger.warning(
                        "System resource warning",
                        batch=batch,
                        operation=i,
                        warning_type="memory_threshold",
                        threshold_percent=85
                    )
                
                if i % 500 == 0:
                    logger.error(
                        "Simulated error condition",
                        batch=batch,
                        operation=i,
                        error_code="SIM_001",
                        recovery_action="retry_operation"
                    )
            
            # Take snapshot after each batch
            snapshots.append(self.take_memory_snapshot())
            
            # Force garbage collection periodically
            if batch % 5 == 0:
                gc.collect()
        
        final_snapshot = self.take_memory_snapshot()
        snapshots.append(final_snapshot)
        
        memory_growth_mb = final_snapshot.current_memory_mb - initial_snapshot.current_memory_mb
        memory_growth_percent = (memory_growth_mb / initial_snapshot.current_memory_mb) * 100 if initial_snapshot.current_memory_mb > 0 else 0
        
        potential_leaks = memory_growth_mb > 12.0
        assessment = "PASS" if memory_growth_mb < 6.0 else "INVESTIGATE" if memory_growth_mb < 12.0 else "FAIL"
        
        tracemalloc.stop()
        
        result = MemoryAnalysisResult(
            test_name=test_name,
            initial_memory_mb=initial_snapshot.current_memory_mb,
            final_memory_mb=final_snapshot.current_memory_mb,
            peak_memory_mb=final_snapshot.peak_memory_mb,
            memory_growth_mb=memory_growth_mb,
            memory_growth_percent=memory_growth_percent,
            total_allocations=iterations,
            potential_leaks_detected=potential_leaks,
            snapshots=snapshots,
            assessment=assessment
        )
        
        self.results.append(result)
        print(f"   Memory growth: {memory_growth_mb:.2f}MB ({memory_growth_percent:.1f}%)")
        print(f"   Assessment: {assessment}")
        
        return result

    def run_all_memory_analyses(self) -> Dict[str, Any]:
        """Run all memory usage analyses."""
        print("🧠 Starting Memory Usage Analysis")
        print("=" * 60)
        
        # Run all memory analysis scenarios
        self.analyze_basic_logging_memory()
        self.analyze_high_volume_logging_memory()
        self.analyze_correlation_id_memory()
        self.analyze_long_running_memory()
        
        return self.generate_summary()

    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive memory analysis summary."""
        print("\n" + "=" * 60)
        print("🧠 MEMORY USAGE ANALYSIS RESULTS")
        print("=" * 60)
        
        summary = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_scenarios": len(self.results),
                "mock_mode": not IMPORTS_AVAILABLE
            },
            "scenario_results": {},
            "overall_assessment": {}
        }
        
        total_memory_growth = 0
        scenarios_passed = 0
        scenarios_failed = 0
        potential_leaks_detected = False
        
        for result in self.results:
            print(f"\n📊 {result.test_name}:")
            print(f"   Initial Memory: {result.initial_memory_mb:.2f}MB")
            print(f"   Final Memory: {result.final_memory_mb:.2f}MB")
            print(f"   Peak Memory: {result.peak_memory_mb:.2f}MB")
            print(f"   Memory Growth: {result.memory_growth_mb:.2f}MB ({result.memory_growth_percent:.1f}%)")
            print(f"   Total Allocations: {result.total_allocations:,}")
            print(f"   Potential Leaks: {'Yes' if result.potential_leaks_detected else 'No'}")
            print(f"   Assessment: {result.assessment}")
            
            # Add to summary
            summary["scenario_results"][result.test_name] = {
                "initial_memory_mb": result.initial_memory_mb,
                "final_memory_mb": result.final_memory_mb,
                "peak_memory_mb": result.peak_memory_mb,
                "memory_growth_mb": result.memory_growth_mb,
                "memory_growth_percent": result.memory_growth_percent,
                "total_allocations": result.total_allocations,
                "potential_leaks_detected": result.potential_leaks_detected,
                "assessment": result.assessment,
                "snapshots_count": len(result.snapshots)
            }
            
            # Aggregate statistics
            total_memory_growth += result.memory_growth_mb
            if result.assessment == "PASS":
                scenarios_passed += 1
            elif result.assessment == "FAIL":
                scenarios_failed += 1
            
            if result.potential_leaks_detected:
                potential_leaks_detected = True
        
        # Overall assessment
        avg_memory_growth = total_memory_growth / len(self.results) if self.results else 0
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Scenarios Analyzed: {len(self.results)}")
        print(f"   Scenarios Passed: {scenarios_passed}")
        print(f"   Scenarios Failed: {scenarios_failed}")
        print(f"   Average Memory Growth: {avg_memory_growth:.2f}MB")
        print(f"   Potential Leaks Detected: {'Yes' if potential_leaks_detected else 'No'}")
        
        # Determine overall status
        if scenarios_failed == 0 and not potential_leaks_detected and avg_memory_growth < 10.0:
            overall_status = "✅ PASS - Memory usage within acceptable limits"
            assessment = "PASS"
        elif scenarios_failed == 0 and avg_memory_growth < 15.0:
            overall_status = "⚠️ INVESTIGATE - Some memory growth detected"
            assessment = "INVESTIGATE"
        else:
            overall_status = "❌ FAIL - Excessive memory usage or leaks detected"
            assessment = "FAIL"
        
        print(f"   Status: {overall_status}")
        
        summary["overall_assessment"] = {
            "total_scenarios": len(self.results),
            "scenarios_passed": scenarios_passed,
            "scenarios_failed": scenarios_failed,
            "average_memory_growth_mb": avg_memory_growth,
            "potential_leaks_detected": potential_leaks_detected,
            "assessment": assessment,
            "status_message": overall_status
        }
        
        return summary


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze memory usage for structured logging")
    parser.add_argument("--output", help="Output file for results JSON")
    args = parser.parse_args()
    
    analyzer = MemoryUsageAnalyzer()
    results = analyzer.run_all_memory_analyses()
    
    # Save results to file
    output_file = args.output or "tasks/logging-standardization/artifacts/memory_analysis_results.json"
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Exit with appropriate code
    assessment = results["overall_assessment"]["assessment"]
    sys.exit(0 if assessment == "PASS" else 1)


if __name__ == "__main__":
    main()
