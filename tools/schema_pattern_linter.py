#!/usr/bin/env python3
"""
AST-based Schema Pattern Linter for API Schema Standardization

This tool analyzes Python files containing Pydantic API schemas and detects
violations of the standardized patterns defined in the schema guidelines.

Key Pattern Violations Detected:
1. Base class inheritance violations (inheriting from BaseModel instead of proper base classes)
2. Missing required conversion methods (from_domain, to_domain, from_orm_model, to_orm_kwargs)
3. Missing TypeAdapter usage for collection validation
4. Incorrect configuration patterns

Usage:
    poetry run python tools/schema_pattern_linter.py [file_or_directory]
    poetry run python tools/schema_pattern_linter.py --report-format json
    poetry run python tools/schema_pattern_linter.py --context products_catalog
"""

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ViolationType(Enum):
    """Types of pattern violations detected by the linter."""

    INHERITANCE_VIOLATION = "inheritance_violation"
    MISSING_METHOD = "missing_method"
    MISSING_TYPEADAPTER = "missing_typeadapter"
    INVALID_CONFIG = "invalid_config"
    WRONG_BASE_CLASS = "wrong_base_class"


class SchemaType(Enum):
    """Expected schema types based on patterns."""

    VALUE_OBJECT = "value_object"
    ENTITY = "entity"
    COMMAND = "command"
    FILTER = "filter"
    UNKNOWN = "unknown"


@dataclass
class Violation:
    """Represents a pattern violation found in a schema."""

    violation_type: ViolationType
    severity: str  # "critical", "high", "medium", "low"
    schema_class: str
    file_path: str
    line_number: int
    message: str
    expected: str
    actual: str
    context: dict = field(default_factory=dict)


@dataclass
class SchemaAnalysis:
    """Analysis results for a single schema class."""

    class_name: str
    file_path: str
    schema_type: SchemaType
    base_classes: list[str]
    methods: set[str]
    violations: list[Violation]
    has_typeadapter: bool = False
    config_dict: dict | None = None


class SchemaPatternLinter:
    """AST-based linter for API schema pattern compliance."""

    # Expected base classes for different schema types
    EXPECTED_BASE_CLASSES = {
        SchemaType.VALUE_OBJECT: "BaseValueObject",
        SchemaType.ENTITY: "BaseEntity",
        SchemaType.COMMAND: "BaseCommand",
        SchemaType.FILTER: "BaseModel",  # Filters can inherit from BaseModel
    }

    # Required methods for all schemas
    REQUIRED_METHODS = {
        "from_domain": {"required": True, "signature": "classmethod"},
        "to_domain": {"required": True, "signature": "instance"},
        "from_orm_model": {"required": True, "signature": "classmethod"},
        "to_orm_kwargs": {"required": True, "signature": "instance"},
    }

    # API schema file patterns
    API_SCHEMA_PATTERNS = ["**/adapters/api_schemas/**/*.py", "**/api_schemas/**/*.py"]

    def __init__(self):
        self.violations: list[Violation] = []
        self.analyses: list[SchemaAnalysis] = []

    def analyze_file(self, file_path: Path) -> list[SchemaAnalysis]:
        """Analyze a single Python file for schema pattern violations."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            file_analyses = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis = self._analyze_class(node, file_path)
                    if analysis:
                        file_analyses.append(analysis)
                        self.analyses.append(analysis)

            return file_analyses

        except Exception as e:
            violation = Violation(
                violation_type=ViolationType.INVALID_CONFIG,
                severity="high",
                schema_class="FILE_PARSE_ERROR",
                file_path=str(file_path),
                line_number=1,
                message=f"Failed to parse file: {e!s}",
                expected="Valid Python syntax",
                actual="Parse error",
            )
            self.violations.append(violation)
            return []

    def _analyze_class(
        self, node: ast.ClassDef, file_path: Path
    ) -> SchemaAnalysis | None:
        """Analyze a single class definition for schema patterns."""
        # Skip classes that don't appear to be API schemas
        if not self._is_api_schema_class(node, file_path):
            return None

        # Extract class information
        base_classes = [self._get_base_name(base) for base in node.bases]
        methods = self._extract_methods(node)
        schema_type = self._determine_schema_type(node.name, base_classes, file_path)

        analysis = SchemaAnalysis(
            class_name=node.name,
            file_path=str(file_path),
            schema_type=schema_type,
            base_classes=base_classes,
            methods=methods,
            violations=[],
            has_typeadapter=bool(self._find_typeadapter_usage(node)),
        )

        # Check for violations
        self._check_inheritance_violations(analysis, node)
        self._check_missing_methods(analysis, node)
        self._check_typeadapter_usage(analysis, node)
        self._check_config_compliance(analysis, node)

        return analysis

    def _is_api_schema_class(self, node: ast.ClassDef, file_path: Path) -> bool:
        """Determine if a class is an API schema class."""
        # Check if file is in api_schemas directory
        if "api_schemas" not in str(file_path):
            return False

        # Check for common API schema naming patterns
        class_name = node.name
        if class_name.startswith("Api") or class_name.endswith("Schema"):
            return True

        # Check if inherits from known base classes
        base_classes = [self._get_base_name(base) for base in node.bases]
        api_base_classes = {
            "BaseModel",
            "BaseApiModel",
            "BaseValueObject",
            "BaseEntity",
            "BaseCommand",
        }

        return bool(set(base_classes) & api_base_classes)

    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return str(base)

    def _extract_methods(self, node: ast.ClassDef) -> set[str]:
        """Extract method names from class definition."""
        methods = set()
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.add(item.name)
        return methods

    def _determine_schema_type(
        self, class_name: str, base_classes: list[str], file_path: Path
    ) -> SchemaType:
        """Determine the expected schema type based on naming and context."""
        path_str = str(file_path).lower()
        class_lower = class_name.lower()

        # Check directory structure
        if "value_objects" in path_str:
            return SchemaType.VALUE_OBJECT
        if "entities" in path_str:
            return SchemaType.ENTITY
        if "commands" in path_str:
            return SchemaType.COMMAND
        if "filters" in path_str:
            return SchemaType.FILTER

        # Check class naming patterns
        if (
            "command" in class_lower
            or class_name.startswith("ApiCreate")
            or class_name.startswith("ApiUpdate")
        ):
            return SchemaType.COMMAND
        if "filter" in class_lower:
            return SchemaType.FILTER
        if any(base in base_classes for base in ["BaseEntity"]):
            return SchemaType.ENTITY
        if any(base in base_classes for base in ["BaseValueObject"]):
            return SchemaType.VALUE_OBJECT

        return SchemaType.UNKNOWN

    def _check_inheritance_violations(
        self, analysis: SchemaAnalysis, node: ast.ClassDef
    ):
        """Check for base class inheritance violations."""
        expected_base = self.EXPECTED_BASE_CLASSES.get(analysis.schema_type)

        if expected_base and expected_base not in analysis.base_classes:
            # Check if inheriting from BaseModel directly (common violation)
            if "BaseModel" in analysis.base_classes:
                violation = Violation(
                    violation_type=ViolationType.WRONG_BASE_CLASS,
                    severity="critical",
                    schema_class=analysis.class_name,
                    file_path=analysis.file_path,
                    line_number=node.lineno,
                    message=f"Schema inherits from BaseModel instead of {expected_base}",
                    expected=expected_base,
                    actual="BaseModel",
                    context={
                        "schema_type": analysis.schema_type.value,
                        "current_bases": analysis.base_classes,
                    },
                )
            else:
                violation = Violation(
                    violation_type=ViolationType.INHERITANCE_VIOLATION,
                    severity="high",
                    schema_class=analysis.class_name,
                    file_path=analysis.file_path,
                    line_number=node.lineno,
                    message=f"Schema does not inherit from expected base class {expected_base}",
                    expected=expected_base,
                    actual=(
                        ", ".join(analysis.base_classes)
                        if analysis.base_classes
                        else "None"
                    ),
                    context={
                        "schema_type": analysis.schema_type.value,
                        "current_bases": analysis.base_classes,
                    },
                )

            analysis.violations.append(violation)
            self.violations.append(violation)

    def _check_missing_methods(self, analysis: SchemaAnalysis, node: ast.ClassDef):
        """Check for missing required methods and validate their signatures."""
        for method_name, method_info in self.REQUIRED_METHODS.items():
            method_node = self._find_method_in_class(node, method_name)

            if not method_node:
                # Method is completely missing
                severity = (
                    "critical"
                    if method_name in ["from_orm_model", "to_orm_kwargs"]
                    else "high"
                )

                violation = Violation(
                    violation_type=ViolationType.MISSING_METHOD,
                    severity=severity,
                    schema_class=analysis.class_name,
                    file_path=analysis.file_path,
                    line_number=node.lineno,
                    message=f"Missing required method: {method_name}",
                    expected=f"{method_name} method with {method_info['signature']} signature",
                    actual="Method not found",
                    context={
                        "method_type": method_info["signature"],
                        "schema_type": analysis.schema_type.value,
                    },
                )

                analysis.violations.append(violation)
                self.violations.append(violation)
            else:
                # Method exists, validate signature
                self._validate_method_signature(
                    analysis, method_node, method_name, method_info
                )

    def _find_method_in_class(
        self, class_node: ast.ClassDef, method_name: str
    ) -> ast.FunctionDef | None:
        """Find a specific method in a class definition."""
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                return item
        return None

    def _validate_method_signature(
        self,
        analysis: SchemaAnalysis,
        method_node: ast.FunctionDef,
        method_name: str,
        method_info: dict,
    ):
        """Validate that a method has the correct signature."""
        violations = []

        # Check for @classmethod decorator when required
        if method_info["signature"] == "classmethod":
            has_classmethod = any(
                isinstance(decorator, ast.Name) and decorator.id == "classmethod"
                for decorator in method_node.decorator_list
            )

            if not has_classmethod:
                violation = Violation(
                    violation_type=ViolationType.MISSING_METHOD,
                    severity="high",
                    schema_class=analysis.class_name,
                    file_path=analysis.file_path,
                    line_number=method_node.lineno,
                    message=f"Method {method_name} missing @classmethod decorator",
                    expected=f"@classmethod decorator on {method_name}",
                    actual="No @classmethod decorator",
                    context={
                        "method_name": method_name,
                        "schema_type": analysis.schema_type.value,
                    },
                )
                violations.append(violation)

        # Check method parameters for classmethod vs instance method
        if method_info["signature"] == "classmethod":
            # Classmethod should have (cls, domain_obj/orm_model) parameters
            expected_min_params = 2
            param_names = ["cls"]

            if method_name in ["from_domain", "from_orm_model"]:
                param_names.append(
                    "domain_obj" if "domain" in method_name else "orm_model"
                )
        else:
            # Instance method should have (self) + optional parameters
            expected_min_params = 1
            param_names = ["self"]

        actual_params = len(method_node.args.args)
        if actual_params < expected_min_params:
            violation = Violation(
                violation_type=ViolationType.MISSING_METHOD,
                severity="medium",
                schema_class=analysis.class_name,
                file_path=analysis.file_path,
                line_number=method_node.lineno,
                message=f"Method {method_name} has incorrect parameter count",
                expected=f"At least {expected_min_params} parameters: {', '.join(param_names)}",
                actual=f"{actual_params} parameters found",
                context={
                    "method_name": method_name,
                    "expected_params": param_names,
                    "actual_param_count": actual_params,
                },
            )
            violations.append(violation)

        # Check return type annotation
        if not method_node.returns:
            violation = Violation(
                violation_type=ViolationType.MISSING_METHOD,
                severity="low",
                schema_class=analysis.class_name,
                file_path=analysis.file_path,
                line_number=method_node.lineno,
                message=f"Method {method_name} missing return type annotation",
                expected="Return type annotation (Self, D, Dict[str, Any], etc.)",
                actual="No return type annotation",
                context={
                    "method_name": method_name,
                    "method_type": method_info["signature"],
                },
            )
            violations.append(violation)

        # Add violations to analysis
        for violation in violations:
            analysis.violations.append(violation)
            self.violations.append(violation)

    def _check_config_compliance(self, analysis: SchemaAnalysis, node: ast.ClassDef):
        """Check for proper BaseApiModel configuration compliance."""
        # Look for model_config in class body
        has_model_config = False
        config_node = None

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "model_config":
                        has_model_config = True
                        config_node = item
                        break

        # If inheriting from BaseApiModel or derived classes, model_config should be inherited
        # Only flag if explicitly overriding with wrong values
        if has_model_config and config_node:
            self._validate_config_dict(analysis, config_node)
        elif not any(
            base in analysis.base_classes
            for base in ["BaseApiModel", "BaseValueObject", "BaseEntity", "BaseCommand"]
        ):
            # Only require explicit config if not inheriting from base classes
            violation = Violation(
                violation_type=ViolationType.INVALID_CONFIG,
                severity="medium",
                schema_class=analysis.class_name,
                file_path=analysis.file_path,
                line_number=node.lineno,
                message="Schema missing proper configuration (model_config or base class inheritance)",
                expected="Inherit from BaseValueObject/BaseEntity/BaseCommand or define model_config",
                actual="No configuration found",
                context={
                    "base_classes": analysis.base_classes,
                    "schema_type": analysis.schema_type.value,
                },
            )
            analysis.violations.append(violation)
            self.violations.append(violation)

    def _validate_config_dict(self, analysis: SchemaAnalysis, config_node: ast.Assign):
        """Validate the contents of model_config ConfigDict."""
        # This is a simplified validation - would need more sophisticated AST analysis
        # for complete validation of ConfigDict contents
        required_config_keys = ["strict", "frozen", "from_attributes"]

        # For now, just check that it's a ConfigDict call
        if isinstance(config_node.value, ast.Call):
            func = config_node.value.func
            if isinstance(func, ast.Name) and func.id == "ConfigDict":
                # Good - using ConfigDict
                return
            violation = Violation(
                violation_type=ViolationType.INVALID_CONFIG,
                severity="medium",
                schema_class=analysis.class_name,
                file_path=analysis.file_path,
                line_number=config_node.lineno,
                message="model_config should use ConfigDict",
                expected="ConfigDict(...)",
                actual=f"Using {ast.unparse(func) if hasattr(ast, 'unparse') else str(func)}",
                context={"schema_type": analysis.schema_type.value},
            )
            analysis.violations.append(violation)
            self.violations.append(violation)

    def _check_typeadapter_usage(self, analysis: SchemaAnalysis, node: ast.ClassDef):
        """Check for proper TypeAdapter usage for collection fields."""
        collection_fields = self._find_collection_fields(node)
        has_typeadapter_imports = self._has_typeadapter_imports(node)
        typeadapter_usage = self._find_typeadapter_usage(node)

        if collection_fields and not typeadapter_usage:
            severity = "high" if len(collection_fields) > 2 else "medium"

            violation = Violation(
                violation_type=ViolationType.MISSING_TYPEADAPTER,
                severity=severity,
                schema_class=analysis.class_name,
                file_path=analysis.file_path,
                line_number=node.lineno,
                message=f"Schema has {len(collection_fields)} collection fields but no TypeAdapter usage detected",
                expected="TypeAdapter for collection validation",
                actual="No TypeAdapter found",
                context={
                    "schema_type": analysis.schema_type.value,
                    "collection_fields": collection_fields,
                    "has_typeadapter_import": has_typeadapter_imports,
                },
            )

            analysis.violations.append(violation)
            self.violations.append(violation)
        elif collection_fields and not has_typeadapter_imports:
            # Has TypeAdapter usage but missing import
            violation = Violation(
                violation_type=ViolationType.MISSING_TYPEADAPTER,
                severity="medium",
                schema_class=analysis.class_name,
                file_path=analysis.file_path,
                line_number=node.lineno,
                message="Schema uses TypeAdapter but missing import statement",
                expected="from pydantic import TypeAdapter",
                actual="TypeAdapter used without import",
                context={
                    "schema_type": analysis.schema_type.value,
                    "collection_fields": collection_fields,
                },
            )

            analysis.violations.append(violation)
            self.violations.append(violation)

    def _find_collection_fields(self, node: ast.ClassDef) -> list[str]:
        """Find fields that are collections and should use TypeAdapter."""
        collection_fields = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and item.annotation:
                field_name = (
                    item.target.id if isinstance(item.target, ast.Name) else "unknown"
                )
                annotation_str = self._get_annotation_string(item.annotation)

                # Check for collection types that need TypeAdapter
                collection_patterns = [
                    "list[",
                    "List[",
                    "set[",
                    "Set[",
                    "frozenset[",
                    "FrozenSet[",
                    "tuple[",
                    "Tuple[",
                    "dict[",
                    "Dict[",
                    "sequence[",
                    "Sequence[",
                ]

                if any(
                    pattern in annotation_str.lower() for pattern in collection_patterns
                ):
                    # Check if it's a complex collection (not just primitive types)
                    if self._is_complex_collection(annotation_str):
                        collection_fields.append(field_name)

        return collection_fields

    def _get_annotation_string(self, annotation: ast.expr) -> str:
        """Get string representation of type annotation."""
        if hasattr(ast, "unparse"):
            return ast.unparse(annotation)
        # Fallback for older Python versions
        if isinstance(annotation, ast.Name):
            return annotation.id
        if isinstance(annotation, ast.Subscript):
            return f"{self._get_annotation_string(annotation.value)}[...]"
        return str(annotation)

    def _is_complex_collection(self, annotation_str: str) -> bool:
        """Check if collection contains complex types that need TypeAdapter."""
        # Simple heuristic - if contains uppercase names (likely custom classes)
        # or multiple type parameters, it's probably complex
        complex_indicators = [
            "Api",  # API schemas
            "Union[",
            "Optional[",  # Union types
            "|",  # New union syntax
            "Generic[",  # Generic types
        ]

        # Don't flag simple primitive collections
        primitive_collections = [
            "list[str]",
            "List[str]",
            "list[int]",
            "List[int]",
            "list[float]",
            "List[float]",
            "set[str]",
            "Set[str]",
        ]

        if annotation_str.lower() in [p.lower() for p in primitive_collections]:
            return False

        return any(indicator in annotation_str for indicator in complex_indicators)

    def _has_typeadapter_imports(self, class_node: ast.ClassDef) -> bool:
        """Check if file has TypeAdapter import statements."""
        # We need to check the module level, not just the class
        # This is a simplified check - ideally we'd analyze the full module
        return False  # For now, assume import checking happens at module level

    def _find_typeadapter_usage(self, node: ast.ClassDef) -> list[str]:
        """Find TypeAdapter usage in class definition."""
        typeadapter_usage = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Check if assignment involves TypeAdapter
                        if self._involves_typeadapter(item.value):
                            typeadapter_usage.append(var_name)

        return typeadapter_usage

    def _involves_typeadapter(self, value_node: ast.expr) -> bool:
        """Check if an assignment value involves TypeAdapter."""
        if isinstance(value_node, ast.Call):
            func = value_node.func
            if (isinstance(func, ast.Name) and func.id == "TypeAdapter") or (
                isinstance(func, ast.Attribute) and func.attr == "TypeAdapter"
            ):
                return True
        return False

    def analyze_directory(
        self, directory: Path, recursive: bool = True
    ) -> list[SchemaAnalysis]:
        """Analyze all Python files in a directory for schema patterns."""
        all_analyses = []

        if recursive:
            pattern = "**/*.py"
        else:
            pattern = "*.py"

        for file_path in directory.glob(pattern):
            if file_path.is_file() and "api_schemas" in str(file_path):
                file_analyses = self.analyze_file(file_path)
                all_analyses.extend(file_analyses)

        return all_analyses

    def generate_report(self, format_type: str = "text") -> str:
        """Generate a comprehensive report of violations found."""
        if format_type == "json":
            return self._generate_json_report()
        return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """Generate a human-readable text report."""
        report = []
        report.append("🚨 API Schema Pattern Linter Report")
        report.append("=" * 50)
        report.append("")

        # Summary statistics
        total_schemas = len(self.analyses)
        total_violations = len(self.violations)
        critical_violations = len(
            [v for v in self.violations if v.severity == "critical"]
        )
        high_violations = len([v for v in self.violations if v.severity == "high"])

        report.append("📊 Summary:")
        report.append(f"  • Total Schemas Analyzed: {total_schemas}")
        report.append(f"  • Total Violations: {total_violations}")
        report.append(f"  • Critical Violations: {critical_violations}")
        report.append(f"  • High Priority Violations: {high_violations}")
        report.append("")

        # Group violations by type
        violations_by_type = {}
        for violation in self.violations:
            vtype = violation.violation_type.value
            if vtype not in violations_by_type:
                violations_by_type[vtype] = []
            violations_by_type[vtype].append(violation)

        # Report violations by type
        for violation_type, violations in violations_by_type.items():
            report.append(
                f"🔍 {violation_type.upper().replace('_', ' ')} ({len(violations)} violations)"
            )
            report.append("-" * 40)

            for violation in violations[:10]:  # Limit to first 10 per type
                report.append(f"  ❌ {violation.schema_class}")
                report.append(
                    f"     File: {violation.file_path}:{violation.line_number}"
                )
                report.append(f"     Issue: {violation.message}")
                report.append(f"     Expected: {violation.expected}")
                report.append(f"     Actual: {violation.actual}")
                report.append("")

            if len(violations) > 10:
                report.append(
                    f"     ... and {len(violations) - 10} more violations of this type"
                )
                report.append("")

        return "\n".join(report)

    def _generate_json_report(self) -> str:
        """Generate a machine-readable JSON report."""
        report_data = {
            "summary": {
                "total_schemas": len(self.analyses),
                "total_violations": len(self.violations),
                "critical_violations": len(
                    [v for v in self.violations if v.severity == "critical"]
                ),
                "high_violations": len(
                    [v for v in self.violations if v.severity == "high"]
                ),
                "medium_violations": len(
                    [v for v in self.violations if v.severity == "medium"]
                ),
                "low_violations": len(
                    [v for v in self.violations if v.severity == "low"]
                ),
            },
            "violations": [
                {
                    "type": v.violation_type.value,
                    "severity": v.severity,
                    "schema_class": v.schema_class,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "message": v.message,
                    "expected": v.expected,
                    "actual": v.actual,
                    "context": v.context,
                }
                for v in self.violations
            ],
            "schemas": [
                {
                    "class_name": a.class_name,
                    "file_path": a.file_path,
                    "schema_type": a.schema_type.value,
                    "base_classes": a.base_classes,
                    "methods": list(a.methods),
                    "has_typeadapter": a.has_typeadapter,
                    "violation_count": len(a.violations),
                }
                for a in self.analyses
            ],
        }

        return json.dumps(report_data, indent=2)


def main():
    """Main entry point for the schema pattern linter."""
    parser = argparse.ArgumentParser(
        description="AST-based linter for API schema pattern compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific file
  poetry run python tools/schema_pattern_linter.py src/contexts/products_catalog/core/adapters/api_schemas/value_objects/api_score.py
  
  # Analyze entire products catalog context
  poetry run python tools/schema_pattern_linter.py src/contexts/products_catalog/ --context products_catalog
  
  # Generate JSON report for all contexts
  poetry run python tools/schema_pattern_linter.py src/contexts/ --report-format json
        """,
    )

    parser.add_argument("target", help="File or directory to analyze")
    parser.add_argument(
        "--report-format",
        choices=["text", "json"],
        default="text",
        help="Output format for the report",
    )
    parser.add_argument("--context", help="Filter analysis to specific context")
    parser.add_argument(
        "--severity-filter",
        choices=["critical", "high", "medium", "low"],
        help="Show only violations of specified severity or higher",
    )

    args = parser.parse_args()

    # Initialize linter
    linter = SchemaPatternLinter()

    # Analyze target
    target_path = Path(args.target)
    if target_path.is_file():
        linter.analyze_file(target_path)
    elif target_path.is_dir():
        linter.analyze_directory(target_path)
    else:
        print(f"Error: {args.target} is not a valid file or directory")
        sys.exit(1)

    # Filter by context if specified
    if args.context:
        linter.violations = [
            v for v in linter.violations if args.context in v.file_path
        ]
        linter.analyses = [a for a in linter.analyses if args.context in a.file_path]

    # Filter by severity if specified
    if args.severity_filter:
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        min_severity = severity_order[args.severity_filter]
        linter.violations = [
            v for v in linter.violations if severity_order[v.severity] <= min_severity
        ]

    # Generate and print report
    report = linter.generate_report(args.report_format)
    print(report)

    # Exit with error code if critical violations found
    critical_count = len([v for v in linter.violations if v.severity == "critical"])
    if critical_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
