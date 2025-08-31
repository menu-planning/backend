#!/usr/bin/env python3
"""
Migration validation script for logging standardization.
Automated checking of migration completeness and correctness.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_files_with_pattern(pattern: str, directory: str = "src") -> list[str]:
    """Find files containing a specific pattern using grep."""
    try:
        result = subprocess.run(
            ["grep", "-r", "-l", pattern, directory, "--include=*.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return []
    except Exception as e:
        print(f"Error searching for pattern '{pattern}': {e}")
        return []


def count_pattern_occurrences(pattern: str, directory: str = "src") -> int:
    """Count occurrences of a pattern using grep."""
    try:
        result = subprocess.run(
            ["grep", "-r", "-c", pattern, directory, "--include=*.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0:
            total = 0
            for line in result.stdout.split('\n'):
                if line.strip() and ':' in line:
                    count = int(line.split(':')[-1])
                    total += count
            return total
        return 0
    except Exception as e:
        print(f"Error counting pattern '{pattern}': {e}")
        return 0


def validate_migration_completeness() -> dict[str, Any]:
    """Validate that migration from standard logging to structlog is complete."""

    # Check for remaining standard logging imports
    standard_logging_files = find_files_with_pattern("import logging")

    # Check for remaining logging.getLogger usage
    get_logger_files = find_files_with_pattern(r"logging\.getLogger")

    # Check for structlog usage
    structlog_files = find_files_with_pattern("StructlogFactory.get_logger")

    # Count remaining standard logger calls
    standard_logger_calls = count_pattern_occurrences(r"logger\.")

    return {
        "migration_complete": len(standard_logging_files) == 0 and len(get_logger_files) == 0,
        "remaining_standard_imports": len(standard_logging_files),
        "remaining_get_logger_usage": len(get_logger_files),
        "structlog_adoptions": len(structlog_files),
        "remaining_logger_calls": standard_logger_calls,
        "files_with_standard_imports": standard_logging_files,
        "files_with_get_logger": get_logger_files,
        "files_with_structlog": structlog_files
    }


def validate_correlation_id_preservation() -> dict[str, Any]:
    """Validate that correlation ID functionality is preserved."""

    # Check for correlation_id usage in log messages
    correlation_files = find_files_with_pattern("correlation_id")

    # Check for correlation_id_ctx usage
    ctx_files = find_files_with_pattern("correlation_id_ctx")

    return {
        "correlation_id_preserved": len(correlation_files) > 0,
        "context_variable_usage": len(ctx_files),
        "files_with_correlation_id": correlation_files,
        "files_with_correlation_ctx": ctx_files
    }


def validate_log_message_quality() -> dict[str, Any]:
    """Validate log message quality and structured format."""

    # Check for structured logging patterns (key=value)
    structured_patterns = count_pattern_occurrences(r'logger\.(info|error|warning|debug)\([^)]*=')

    # Check for old string formatting patterns
    old_format_patterns = count_pattern_occurrences(r'logger\.(info|error|warning|debug)\([^)]*%[sd]')
    f_string_patterns = count_pattern_occurrences(r'logger\.(info|error|warning|debug)\([^)]*f"')

    return {
        "structured_logging_usage": structured_patterns,
        "old_format_usage": old_format_patterns + f_string_patterns,
        "quality_score": structured_patterns / max(1, structured_patterns + old_format_patterns + f_string_patterns)
    }


def validate_performance_impact() -> dict[str, Any]:
    """Validate that performance impact is within acceptable limits."""

    # This would typically run benchmark comparisons
    # For now, we'll check if benchmark files exist
    benchmark_files = []
    artifacts_dir = Path("tasks/logging-standardization/artifacts")

    if (artifacts_dir / "benchmark_logging.py").exists():
        benchmark_files.append("benchmark_logging.py")

    if (artifacts_dir / "baseline_measurements.json").exists():
        benchmark_files.append("baseline_measurements.json")

    return {
        "benchmark_tools_available": len(benchmark_files) > 0,
        "benchmark_files": benchmark_files,
        "performance_validated": False,  # Would be set by actual benchmark runs
        "performance_impact_percent": None  # Would be calculated from benchmarks
    }


def run_linting_validation() -> dict[str, Any]:
    """Run linting validation on the codebase."""
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "src/"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        return {
            "linting_passed": result.returncode == 0,
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr
        }
    except Exception as e:
        return {
            "linting_passed": False,
            "exit_code": -1,
            "output": "",
            "errors": str(e)
        }


def generate_migration_report() -> dict[str, Any]:
    """Generate comprehensive migration validation report."""

    report = {
        "timestamp": str(Path("tasks/logging-standardization/artifacts/baseline_measurements.json").stat().st_mtime) if Path("tasks/logging-standardization/artifacts/baseline_measurements.json").exists() else None,
        "migration_completeness": validate_migration_completeness(),
        "correlation_id_preservation": validate_correlation_id_preservation(),
        "log_message_quality": validate_log_message_quality(),
        "performance_impact": validate_performance_impact(),
        "linting_validation": run_linting_validation()
    }

    # Calculate overall migration status
    migration_complete = report["migration_completeness"]["migration_complete"]
    correlation_preserved = report["correlation_id_preservation"]["correlation_id_preserved"]
    linting_passed = report["linting_validation"]["linting_passed"]

    report["overall_status"] = {
        "migration_ready": migration_complete and correlation_preserved and linting_passed,
        "completion_percentage": calculate_completion_percentage(report),
        "critical_issues": get_critical_issues(report)
    }

    return report


def calculate_completion_percentage(report: dict[str, Any]) -> float:
    """Calculate migration completion percentage."""

    migration_data = report["migration_completeness"]
    total_files = (
        migration_data["remaining_standard_imports"] +
        migration_data["structlog_adoptions"]
    )

    if total_files == 0:
        return 100.0

    completion = (migration_data["structlog_adoptions"] / total_files) * 100
    return min(100.0, completion)


def get_critical_issues(report: dict[str, Any]) -> list[str]:
    """Identify critical issues that need attention."""

    issues = []

    migration_data = report["migration_completeness"]
    if migration_data["remaining_standard_imports"] > 0:
        issues.append(f"{migration_data['remaining_standard_imports']} files still use standard logging imports")

    if migration_data["remaining_get_logger_usage"] > 0:
        issues.append(f"{migration_data['remaining_get_logger_usage']} files still use logging.getLogger()")

    if not report["correlation_id_preservation"]["correlation_id_preserved"]:
        issues.append("Correlation ID functionality may be compromised")

    if not report["linting_validation"]["linting_passed"]:
        issues.append("Linting validation failed")

    quality_data = report["log_message_quality"]
    if quality_data["quality_score"] < 0.8:
        issues.append(f"Log message quality score is low: {quality_data['quality_score']:.2f}")

    return issues


def main():
    """Main execution function."""
    print("Running migration validation...")

    report = generate_migration_report()

    # Save report to file
    output_file = Path("tasks/logging-standardization/artifacts/migration_validation_report.json")
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Validation report saved to: {output_file}")

    # Print summary
    print("\n=== Migration Validation Summary ===")
    print(f"Overall Status: {'✅ READY' if report['overall_status']['migration_ready'] else '❌ NOT READY'}")
    print(f"Completion: {report['overall_status']['completion_percentage']:.1f}%")

    if report['overall_status']['critical_issues']:
        print("\nCritical Issues:")
        for issue in report['overall_status']['critical_issues']:
            print(f"  - {issue}")

    # Exit with appropriate code
    sys.exit(0 if report['overall_status']['migration_ready'] else 1)


if __name__ == "__main__":
    main()
