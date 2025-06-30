#!/usr/bin/env python3
"""
Four-Layer Conversion Pattern Analysis Script

This script performs detailed analysis of API schema conversion patterns:
1. Maps all four-layer conversion implementations (to_domain, from_domain, from_orm_model, to_orm_kwargs)
2. Documents type conversion patterns (set ↔ frozenset ↔ list transformations)
3. Identifies missing conversion methods and inconsistencies
4. Creates comprehensive type conversion matrix with real examples

Usage:
    poetry run python scripts/analyze_conversion_patterns.py
    poetry run python scripts/analyze_conversion_patterns.py --output-format json
    poetry run python scripts/analyze_conversion_patterns.py --detailed
"""

import ast
import json
import sys
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import click


@dataclass
class ConversionMethod:
    """Represents a conversion method implementation."""
    method_name: str
    schema_class: str
    file_path: str
    line_number: int
    return_type: Optional[str]
    body_ast: ast.AST
    type_conversions: List[str] = field(default_factory=list)
    validation_calls: List[str] = field(default_factory=list)
    computed_fields: List[str] = field(default_factory=list)


@dataclass
class TypeTransformation:
    """Represents a type transformation pattern."""
    source_type: str
    target_type: str
    transformation_code: str
    conversion_direction: str
    schema_class: str
    field_name: str
    file_path: str


@dataclass
class SchemaConversionProfile:
    """Complete conversion profile for a schema."""
    schema_name: str
    file_path: str
    base_class: str
    domain_type: str
    orm_type: str
    has_to_domain: bool = False
    has_from_domain: bool = False
    has_from_orm_model: bool = False
    has_to_orm_kwargs: bool = False
    conversion_methods: List[ConversionMethod] = field(default_factory=list)
    type_transformations: List[TypeTransformation] = field(default_factory=list)
    missing_methods: Set[str] = field(default_factory=set)


@dataclass
class ConversionAnalysisResults:
    """Complete four-layer conversion analysis results."""
    schema_profiles: List[SchemaConversionProfile]
    type_transformation_matrix: Dict[str, List[TypeTransformation]]
    missing_implementations: List[Tuple[str, Set[str]]]
    type_adapter_usage: Dict[str, List[str]]
    conversion_complexity_metrics: Dict[str, int]
    common_patterns: Dict[str, int]
    anti_patterns: List[str]


class ConversionPatternAnalyzer:
    """Analyzer for four-layer conversion patterns."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.results = ConversionAnalysisResults(
            schema_profiles=[],
            type_transformation_matrix=defaultdict(list),
            missing_implementations=[],
            type_adapter_usage=defaultdict(list),
            conversion_complexity_metrics=defaultdict(int),
            common_patterns=defaultdict(int),
            anti_patterns=[]
        )
        
        # Required methods for BaseEntity schemas
        self.required_methods = {"to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"}
    
    def discover_api_schema_files(self) -> List[Path]:
        """Discover all API schema files."""
        schema_files = []
        for path in self.root_path.rglob("**/api_schemas/**/*.py"):
            if path.name != "__init__.py":
                schema_files.append(path)
        return sorted(schema_files)
    
    def parse_file_safely(self, file_path: Path) -> Optional[ast.AST]:
        """Parse Python file safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content)
        except Exception:
            return None
    
    def extract_type_from_annotation(self, annotation: ast.AST) -> str:
        """Extract clean type string from AST annotation."""
        try:
            return ast.unparse(annotation)
        except Exception:
            return "Unknown"
    
    def analyze_conversion_body(self, method_node: ast.FunctionDef) -> Tuple[List[str], List[str], List[str]]:
        """Analyze conversion method body for patterns."""
        type_conversions = []
        validation_calls = []
        computed_fields = []
        
        for node in ast.walk(method_node):
            # Look for TypeAdapter validate calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "validate_python":
                        # Found TypeAdapter usage
                        if isinstance(node.func.value, ast.Name):
                            adapter_name = node.func.value.id
                            validation_calls.append(adapter_name)
                        elif isinstance(node.func.value, ast.Attribute):
                            adapter_name = ast.unparse(node.func.value)
                            validation_calls.append(adapter_name)
                
                # Look for type conversions
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in ["list", "set", "frozenset", "tuple"]:
                        arg_code = ast.unparse(node.args[0]) if node.args else ""
                        type_conversions.append(f"{func_name}({arg_code})")
            
            # Look for list/set comprehensions
            if isinstance(node, (ast.ListComp, ast.SetComp)):
                conversion_code = ast.unparse(node)
                type_conversions.append(conversion_code)
            
            # Look for computed field access (attribute access patterns)
            if isinstance(node, ast.Attribute):
                if node.attr in ["nutri_facts", "computed_value"]:
                    computed_fields.append(node.attr)
        
        return type_conversions, validation_calls, computed_fields
    
    def extract_type_transformations(self, method: ConversionMethod) -> List[TypeTransformation]:
        """Extract type transformation patterns from conversion method."""
        transformations = []
        
        # Analyze assignment patterns in the method body
        for node in ast.walk(method.body_ast):
            if isinstance(node, ast.Call):
                # Look for constructor calls with type conversions
                if isinstance(node.func, ast.Name):
                    if node.func.id in method.schema_class:  # Schema constructor
                        for keyword in node.keywords:
                            if keyword.value and keyword.arg:  # Ensure both value and arg are not None
                                # Extract transformation pattern
                                field_name = keyword.arg
                                value_code = ast.unparse(keyword.value)
                                
                                # Detect type transformation patterns
                                if "frozenset" in value_code and "set" in value_code:
                                    transformations.append(TypeTransformation(
                                        source_type="set",
                                        target_type="frozenset", 
                                        transformation_code=value_code,
                                        conversion_direction=method.method_name,
                                        schema_class=method.schema_class,
                                        field_name=field_name,
                                        file_path=method.file_path
                                    ))
                                elif "list" in value_code and ("frozenset" in value_code or "set" in value_code):
                                    source = "frozenset" if "frozenset" in value_code else "set"
                                    transformations.append(TypeTransformation(
                                        source_type=source,
                                        target_type="list",
                                        transformation_code=value_code,
                                        conversion_direction=method.method_name,
                                        schema_class=method.schema_class,
                                        field_name=field_name,
                                        file_path=method.file_path
                                    ))
        
        return transformations
    
    def analyze_conversion_method(self, func_node: ast.FunctionDef, schema_class: str, file_path: Path) -> ConversionMethod:
        """Analyze a single conversion method."""
        # Extract return type
        return_type = None
        if func_node.returns:
            return_type = self.extract_type_from_annotation(func_node.returns)
        
        # Analyze method body
        type_conversions, validation_calls, computed_fields = self.analyze_conversion_body(func_node)
        
        method = ConversionMethod(
            method_name=func_node.name,
            schema_class=schema_class,
            file_path=str(file_path),
            line_number=func_node.lineno,
            return_type=return_type,
            body_ast=func_node,
            type_conversions=type_conversions,
            validation_calls=validation_calls,
            computed_fields=computed_fields
        )
        
        return method
    
    def extract_generic_types(self, base_class_str: str) -> Tuple[str, str]:
        """Extract domain and ORM types from generic base class."""
        # Pattern: BaseEntity[DomainType, OrmType]
        match = re.search(r'BaseEntity\[(.+?),\s*(.+?)\]', base_class_str)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        match = re.search(r'BaseValueObject\[(.+?),\s*(.+?)\]', base_class_str) 
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        match = re.search(r'BaseCommand\[(.+?),\s*(.+?)\]', base_class_str)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        return "Unknown", "Unknown"
    
    def analyze_schema_class(self, class_node: ast.ClassDef, file_path: Path) -> Optional[SchemaConversionProfile]:
        """Analyze a schema class for conversion patterns."""
        schema_name = class_node.name
        
        # Extract base classes
        base_classes = [ast.unparse(base) for base in class_node.bases]
        
        # Check if this is a schema we're interested in
        relevant_bases = ["BaseEntity", "BaseValueObject", "BaseCommand"]
        if not any(base_name in " ".join(base_classes) for base_name in relevant_bases):
            return None
        
        # Determine primary base class
        primary_base = "Unknown"
        for base in base_classes:
            if any(rb in base for rb in relevant_bases):
                primary_base = base
                break
        
        # Extract domain and ORM types
        domain_type, orm_type = self.extract_generic_types(primary_base)
        
        # Create profile
        profile = SchemaConversionProfile(
            schema_name=schema_name,
            file_path=str(file_path),
            base_class=primary_base,
            domain_type=domain_type,
            orm_type=orm_type
        )
        
        # Analyze conversion methods
        found_methods = set()
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_name = node.name
                if method_name in self.required_methods:
                    found_methods.add(method_name)
                    
                    # Analyze the method
                    method_analysis = self.analyze_conversion_method(node, schema_name, file_path)
                    profile.conversion_methods.append(method_analysis)
                    
                    # Extract type transformations
                    transformations = self.extract_type_transformations(method_analysis)
                    profile.type_transformations.extend(transformations)
                    
                    # Update profile flags
                    if method_name == "to_domain":
                        profile.has_to_domain = True
                    elif method_name == "from_domain":
                        profile.has_from_domain = True
                    elif method_name == "from_orm_model":
                        profile.has_from_orm_model = True
                    elif method_name == "to_orm_kwargs":
                        profile.has_to_orm_kwargs = True
        
        # Identify missing methods (only for BaseEntity schemas)
        if "BaseEntity" in primary_base:
            profile.missing_methods = self.required_methods - found_methods
        
        return profile
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for conversion patterns."""
        tree = self.parse_file_safely(file_path)
        if not tree:
            return
        
        # Find schema classes and analyze them
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                profile = self.analyze_schema_class(node, file_path)
                if profile:
                    self.results.schema_profiles.append(profile)
                    
                    # Collect type transformations
                    for transformation in profile.type_transformations:
                        key = f"{transformation.source_type}_to_{transformation.target_type}"
                        self.results.type_transformation_matrix[key].append(transformation)
                    
                    # Collect missing implementations
                    if profile.missing_methods:
                        self.results.missing_implementations.append(
                            (profile.schema_name, profile.missing_methods)
                        )
                    
                    # Track TypeAdapter usage
                    for method in profile.conversion_methods:
                        for adapter in method.validation_calls:
                            self.results.type_adapter_usage[adapter].append(
                                f"{profile.schema_name}.{method.method_name}"
                            )
    
    def identify_patterns_and_anti_patterns(self) -> None:
        """Identify common patterns and anti-patterns."""
        # Count conversion complexity
        for profile in self.results.schema_profiles:
            complexity = len(profile.conversion_methods)
            self.results.conversion_complexity_metrics[profile.schema_name] = complexity
        
        # Identify common transformation patterns
        for transform_type, transformations in self.results.type_transformation_matrix.items():
            self.results.common_patterns[transform_type] = len(transformations)
        
        # Identify anti-patterns
        for profile in self.results.schema_profiles:
            # Missing required methods for BaseEntity
            if "BaseEntity" in profile.base_class and profile.missing_methods:
                self.results.anti_patterns.append(
                    f"{profile.schema_name}: Missing required methods {profile.missing_methods}"
                )
            
            # Inconsistent type handling
            transformations_by_field = defaultdict(list)
            for transform in profile.type_transformations:
                transformations_by_field[transform.field_name].append(transform)
            
            for field_name, transforms in transformations_by_field.items():
                if len(set(t.transformation_code for t in transforms)) > 2:
                    self.results.anti_patterns.append(
                        f"{profile.schema_name}.{field_name}: Inconsistent type transformations"
                    )
    
    def run_analysis(self) -> ConversionAnalysisResults:
        """Run comprehensive conversion pattern analysis."""
        print("🔍 Discovering API schema files...")
        schema_files = self.discover_api_schema_files()
        print(f"Found {len(schema_files)} API schema files")
        
        print("📊 Analyzing conversion patterns...")
        for file_path in schema_files:
            self.analyze_file(file_path)
        
        print("🔎 Identifying patterns and anti-patterns...")
        self.identify_patterns_and_anti_patterns()
        
        return self.results


def format_results_text(results: ConversionAnalysisResults) -> str:
    """Format conversion analysis results as human-readable text."""
    output = []
    
    output.append("=" * 80)
    output.append("FOUR-LAYER CONVERSION PATTERN ANALYSIS REPORT")
    output.append("=" * 80)
    output.append("")
    
    # Summary
    output.append("📊 CONVERSION SUMMARY")
    output.append("-" * 40)
    output.append(f"Total schemas analyzed: {len(results.schema_profiles)}")
    output.append(f"Schemas with complete implementations: {len([p for p in results.schema_profiles if not p.missing_methods])}")
    output.append(f"Missing implementations: {len(results.missing_implementations)}")
    output.append(f"Type transformation patterns: {len(results.type_transformation_matrix)}")
    output.append(f"TypeAdapter usage patterns: {len(results.type_adapter_usage)}")
    output.append(f"Anti-patterns found: {len(results.anti_patterns)}")
    output.append("")
    
    # Implementation completeness
    output.append("🎯 IMPLEMENTATION COMPLETENESS")
    output.append("-" * 40)
    complete_schemas = [p for p in results.schema_profiles if not p.missing_methods and "BaseEntity" in p.base_class]
    incomplete_schemas = [p for p in results.schema_profiles if p.missing_methods]
    
    output.append(f"Complete BaseEntity schemas: {len(complete_schemas)}")
    output.append(f"Incomplete schemas: {len(incomplete_schemas)}")
    
    if incomplete_schemas:
        output.append("\nIncomplete schemas:")
        for profile in incomplete_schemas[:10]:  # Show first 10
            output.append(f"  • {profile.schema_name}: missing {profile.missing_methods}")
    output.append("")
    
    # Type transformation matrix
    output.append("🔄 TYPE TRANSFORMATION MATRIX")
    output.append("-" * 40)
    for transform_type, transformations in results.type_transformation_matrix.items():
        output.append(f"{transform_type}: {len(transformations)} implementations")
        if transformations:
            # Show example
            example = transformations[0]
            output.append(f"  Example: {example.schema_class}.{example.field_name}")
            output.append(f"  Code: {example.transformation_code[:80]}...")
    output.append("")
    
    # TypeAdapter usage
    output.append("🔧 TYPEADAPTER USAGE PATTERNS")
    output.append("-" * 40)
    for adapter_name, usages in results.type_adapter_usage.items():
        output.append(f"{adapter_name}: used in {len(usages)} places")
        for usage in usages[:3]:  # Show first 3
            output.append(f"  • {usage}")
        if len(usages) > 3:
            output.append(f"  ... and {len(usages) - 3} more")
    output.append("")
    
    # Common patterns
    output.append("📈 COMMON CONVERSION PATTERNS")
    output.append("-" * 40)
    sorted_patterns = sorted(results.common_patterns.items(), key=lambda x: x[1], reverse=True)
    for pattern, count in sorted_patterns:
        output.append(f"{pattern}: {count} occurrences")
    output.append("")
    
    # Anti-patterns
    if results.anti_patterns:
        output.append("⚠️  ANTI-PATTERNS AND ISSUES")
        output.append("-" * 40)
        for anti_pattern in results.anti_patterns:
            output.append(f"• {anti_pattern}")
        output.append("")
    
    # Detailed schema examples
    output.append("📝 DETAILED SCHEMA EXAMPLES")
    output.append("-" * 40)
    
    # Show examples of well-implemented schemas
    complete_examples = [p for p in complete_schemas if len(p.type_transformations) > 2][:3]
    
    for profile in complete_examples:
        output.append(f"\n{profile.schema_name} ({profile.file_path})")
        output.append(f"  Base: {profile.base_class}")
        output.append(f"  Domain type: {profile.domain_type}")
        output.append(f"  ORM type: {profile.orm_type}")
        output.append(f"  Conversion methods: {len(profile.conversion_methods)}")
        output.append(f"  Type transformations: {len(profile.type_transformations)}")
        
        if profile.type_transformations:
            output.append("  Key transformations:")
            for transform in profile.type_transformations[:2]:
                output.append(f"    • {transform.field_name}: {transform.source_type} → {transform.target_type}")
    
    return "\n".join(output)


@click.command()
@click.option('--output-format', '-f', default='text', type=click.Choice(['text', 'json']),
              help='Output format (text or json)')
@click.option('--output-file', '-o', help='Output file path (default: stdout)')
@click.option('--detailed', '-d', is_flag=True, help='Include detailed analysis')
@click.option('--root-path', '-r', default='src', help='Root path to scan (default: src)')
def main(output_format: str, output_file: Optional[str], detailed: bool, root_path: str):
    """Analyze four-layer conversion patterns in API schemas."""
    
    # Determine root path
    project_root = Path.cwd()
    scan_root = project_root / root_path
    
    if not scan_root.exists():
        click.echo(f"❌ Root path {scan_root} does not exist", err=True)
        sys.exit(1)
    
    # Run analysis
    analyzer = ConversionPatternAnalyzer(scan_root)
    results = analyzer.run_analysis()
    
    # Format output
    if output_format == 'json':
        # Convert to JSON-serializable format
        output_data = {
            "summary": {
                "total_schemas": len(results.schema_profiles),
                "complete_implementations": len([p for p in results.schema_profiles if not p.missing_methods]),
                "missing_implementations": len(results.missing_implementations),
                "type_transformations": len(results.type_transformation_matrix),
                "anti_patterns": len(results.anti_patterns)
            },
            "schema_profiles": [
                {
                    "schema_name": profile.schema_name,
                    "file_path": profile.file_path,
                    "base_class": profile.base_class,
                    "domain_type": profile.domain_type,
                    "orm_type": profile.orm_type,
                    "has_to_domain": profile.has_to_domain,
                    "has_from_domain": profile.has_from_domain,
                    "has_from_orm_model": profile.has_from_orm_model,
                    "has_to_orm_kwargs": profile.has_to_orm_kwargs,
                    "missing_methods": list(profile.missing_methods),
                    "conversion_methods": [
                        {
                            "method_name": method.method_name,
                            "return_type": method.return_type,
                            "type_conversions": method.type_conversions,
                            "validation_calls": method.validation_calls,
                            "computed_fields": method.computed_fields
                        }
                        for method in profile.conversion_methods
                    ],
                    "type_transformations": [
                        {
                            "source_type": t.source_type,
                            "target_type": t.target_type,
                            "field_name": t.field_name,
                            "conversion_direction": t.conversion_direction,
                            "transformation_code": t.transformation_code
                        }
                        for t in profile.type_transformations
                    ] if detailed else []
                }
                for profile in results.schema_profiles
            ],
            "type_transformation_matrix": {
                key: len(transformations)
                for key, transformations in results.type_transformation_matrix.items()
            },
            "missing_implementations": [
                {"schema": schema, "missing_methods": list(methods)}
                for schema, methods in results.missing_implementations
            ],
            "type_adapter_usage": dict(results.type_adapter_usage),
            "common_patterns": dict(results.common_patterns),
            "anti_patterns": results.anti_patterns
        }
        
        output_content = json.dumps(output_data, indent=2)
    else:
        output_content = format_results_text(results)
    
    # Write output
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        click.echo(f"✅ Conversion analysis results written to {output_file}")
    else:
        click.echo(output_content)
    
    # Summary
    complete_count = len([p for p in results.schema_profiles if not p.missing_methods])
    click.echo(f"\n✅ Analysis complete: {complete_count}/{len(results.schema_profiles)} schemas have complete implementations")
    if results.anti_patterns:
        click.echo(f"⚠️  Found {len(results.anti_patterns)} anti-patterns")


if __name__ == "__main__":
    main() 