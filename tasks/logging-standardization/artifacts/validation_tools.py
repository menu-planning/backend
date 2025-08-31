#!/usr/bin/env python3
"""
Validation tools for logging standardization project.

This module provides utilities to validate the migration from standard logging
to structured logging across the codebase.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_files_with_pattern(pattern: str, directory: str = "src") -> list[str]:
    """Find files containing a specific pattern."""
    try:
        result = subprocess.run(
            ["grep", "-r", "-l", pattern, directory, "--include=*.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def count_pattern_occurrences(pattern: str, directory: str = "src") -> int:
    """Count occurrences of a pattern in files."""
    try:
        result = subprocess.run(
            ["grep", "-r", pattern, directory, "--include=*.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    except subprocess.CalledProcessError:
        return 0


def validate_imports() -> dict[str, Any]:
    """Validate logging import patterns."""
    standard_logging_files = find_files_with_pattern("import logging")
    structlog_files = find_files_with_pattern("structlog")

    return {
        "standard_logging_imports": len(standard_logging_files),
        "structlog_imports": len(structlog_files),
        "files_with_standard_logging": standard_logging_files,
        "files_with_structlog": structlog_files,
    }


def validate_logger_usage() -> dict[str, Any]:
    """Validate logger instantiation patterns."""
    get_logger_files = find_files_with_pattern("logging.getLogger")
    structlog_factory_files = find_files_with_pattern("StructlogFactory.get_logger")

    return {
        "logging_get_logger_usage": len(get_logger_files),
        "structlog_factory_usage": len(structlog_factory_files),
        "files_with_get_logger": get_logger_files,
        "files_with_structlog_factory": structlog_factory_files,
    }


def validate_log_calls() -> dict[str, Any]:
    """Validate log call patterns."""
    info_calls = count_pattern_occurrences(r"logger\.info")
    error_calls = count_pattern_occurrences(r"logger\.error")
    warning_calls = count_pattern_occurrences(r"logger\.warning")
    debug_calls = count_pattern_occurrences(r"logger\.debug")

    return {
        "info_calls": info_calls,
        "error_calls": error_calls,
        "warning_calls": warning_calls,
        "debug_calls": debug_calls,
        "total_log_calls": info_calls + error_calls + warning_calls + debug_calls,
    }


def validate_correlation_ids() -> dict[str, Any]:
    """Validate correlation ID usage."""
    correlation_id_files = find_files_with_pattern("correlation_id")

    return {
        "files_with_correlation_id": len(correlation_id_files),
        "correlation_id_files": correlation_id_files,
    }


def run_lint_check() -> dict[str, Any]:
    """Run ruff linting check."""
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "src/"],
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr,
            "passed": result.returncode == 0,
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": str(e),
            "passed": False,
        }


def run_type_check() -> dict[str, Any]:
    """Run mypy type checking."""
    try:
        result = subprocess.run(
            ["uv", "run", "mypy", "src/"],
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr,
            "passed": result.returncode == 0,
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": str(e),
            "passed": False,
        }


def generate_baseline_report() -> dict[str, Any]:
    """Generate comprehensive baseline report."""
    return {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "imports": validate_imports(),
        "logger_usage": validate_logger_usage(),
        "log_calls": validate_log_calls(),
        "correlation_ids": validate_correlation_ids(),
        "linting": run_lint_check(),
        "type_checking": run_type_check(),
    }


def main() -> None:
    """Main validation function."""
    if len(sys.argv) > 1 and sys.argv[1] == "baseline":
        report = generate_baseline_report()
        print(json.dumps(report, indent=2))
    else:
        print("Usage: python validation_tools.py baseline")
        print("This will generate a comprehensive baseline report.")


if __name__ == "__main__":
    main()
