#!/usr/bin/env python3
"""
API Schema Pattern Analysis Script

This script discovers and analyzes all API schemas in the codebase to:
1. Generate comprehensive inventory of existing patterns
2. Extract class definitions, inheritance patterns, and method signatures  
3. Document type conversion patterns and TypeAdapter usage
4. Identify inconsistencies and anti-patterns
5. Create foundation for documentation-driven refactoring

Usage:
    poetry run python scripts/analyze_api_patterns.py
    poetry run python scripts/analyze_api_patterns.py --output-format json
    poetry run python scripts/analyze_api_patterns.py --detailed --performance-metrics
"""

import ast
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import click


@dataclass
class MethodSignature:
    """Represents a method signature analysis."""
    name: str
    args: List[str]
    return_type: Optional[str]
    decorators: List[str]
    is_classmethod: bool = False
    is_staticmethod: bool = False
    docstring: Optional[str] = None


@dataclass
class TypeAdapterUsage:
    """Represents TypeAdapter usage patterns."""
    name: str
    type_definition: str
    file_path: str
    line_number: int
    usage_context: str


@dataclass
class TypeConversion:
    """Represents type conversion patterns between layers."""
    domain_type: str
    api_type: str
    orm_type: str
    conversion_direction: str
    file_path: str
    method_name: str


@dataclass
class SchemaClass:
    """Represents an API schema class analysis."""
    name: str
    file_path: str
    line_number: int
    base_classes: List[str]
    fields: Dict[str, str]
    methods: List[MethodSignature]
    type_adapters: List[TypeAdapterUsage]
    type_conversions: List[TypeConversion]
    imports: List[str]
    docstring: Optional[str] = None
    validation_patterns: List[str] = field(default_factory=list)
    computed_properties: List[str] = field(default_factory=list)


@dataclass
class AnalysisResults:
    """Complete analysis results."""
    schemas: List[SchemaClass]
    inheritance_tree: Dict[str, List[str]]
    type_adapter_inventory: List[TypeAdapterUsage]
    conversion_patterns: List[TypeConversion]
    inconsistencies: List[str]
    performance_metrics: Dict[str, float]
    file_errors: List[Tuple[str, str]]
    total_files_scanned: int
    total_schemas_found: int


class ApiSchemaAnalyzer:
    """Comprehensive API schema pattern analyzer."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.results = AnalysisResults(
            schemas=[],
            inheritance_tree=defaultdict(list),
            type_adapter_inventory=[],
            conversion_patterns=[],
            inconsistencies=[],
            performance_metrics={},
            file_errors=[],
            total_files_scanned=0,
            total_schemas_found=0
        )
    
    def discover_api_schema_files(self) -> List[Path]:
        """Discover all API schema files using the **/api_schemas/**/*.py pattern."""
        schema_files = []
        
        # Search pattern: **/api_schemas/**/*.py
        for path in self.root_path.rglob("**/api_schemas/**/*.py"):
            if path.name != "__init__.py":
                schema_files.append(path)
        
        return sorted(schema_files)
    
    def parse_file_safely(self, file_path: Path) -> Optional[ast.AST]:
        """Parse Python file with comprehensive error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content)
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            error_msg = f"Failed to parse {file_path}: {type(e).__name__}: {str(e)}"
            self.results.file_errors.append((str(file_path), error_msg))
            return None
        except Exception as e:
            error_msg = f"Unexpected error parsing {file_path}: {type(e).__name__}: {str(e)}"
            self.results.file_errors.append((str(file_path), error_msg))
            return None
    
    def extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements from the AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
        
        return imports
    
    def extract_type_adapters(self, tree: ast.AST, file_path: Path) -> List[TypeAdapterUsage]:
        """Extract TypeAdapter usage patterns."""
        type_adapters = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                        if (isinstance(node.value.func, ast.Name) and 
                            node.value.func.id == "TypeAdapter"):
                            
                            # Extract type definition
                            type_def = ast.unparse(node.value.args[0]) if node.value.args else "Unknown"
                            
                            type_adapters.append(TypeAdapterUsage(
                                name=target.id,
                                type_definition=type_def,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                usage_context="module_level"
                            ))
        
        return type_adapters
    
    def extract_method_signature(self, func_node: ast.FunctionDef) -> MethodSignature:
        """Extract comprehensive method signature information."""
        # Extract argument names
        args = [arg.arg for arg in func_node.args.args]
        
        # Extract return type annotation
        return_type = None
        if func_node.returns:
            return_type = ast.unparse(func_node.returns)
        
        # Extract decorators
        decorators = []
        is_classmethod = False
        is_staticmethod = False
        
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorator_name = decorator.id
                decorators.append(decorator_name)
                if decorator_name == "classmethod":
                    is_classmethod = True
                elif decorator_name == "staticmethod":
                    is_staticmethod = True
            else:
                decorators.append(ast.unparse(decorator))
        
        # Extract docstring
        docstring = None
        if (func_node.body and isinstance(func_node.body[0], ast.Expr) and
            isinstance(func_node.body[0].value, ast.Constant) and
            isinstance(func_node.body[0].value.value, str)):
            docstring = func_node.body[0].value.value
        
        return MethodSignature(
            name=func_node.name,
            args=args,
            return_type=return_type,
            decorators=decorators,
            is_classmethod=is_classmethod,
            is_staticmethod=is_staticmethod,
            docstring=docstring
        )
    
    def extract_field_annotations(self, class_node: ast.ClassDef) -> Dict[str, str]:
        """Extract field type annotations from class definition."""
        fields = {}
        
        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                field_name = node.target.id
                field_type = ast.unparse(node.annotation) if node.annotation else "Any"
                fields[field_name] = field_type
        
        return fields
    
    def analyze_type_conversions(self, methods: List[MethodSignature], file_path: Path) -> List[TypeConversion]:
        """Analyze type conversion patterns in the four-layer methods."""
        conversions = []
        
        conversion_methods = {
            "to_domain": "api_to_domain",
            "from_domain": "domain_to_api", 
            "from_orm_model": "orm_to_api",
            "to_orm_kwargs": "api_to_orm"
        }
        
        for method in methods:
            if method.name in conversion_methods:
                # Extract type information from method signature and return type
                domain_type = "Unknown"
                api_type = "Unknown"
                orm_type = "Unknown"
                
                if method.return_type:
                    if method.name == "to_domain":
                        domain_type = method.return_type
                    elif method.name in ["from_domain", "from_orm_model"]:
                        api_type = method.return_type
                
                conversions.append(TypeConversion(
                    domain_type=domain_type,
                    api_type=api_type,
                    orm_type=orm_type,
                    conversion_direction=conversion_methods[method.name],
                    file_path=str(file_path),
                    method_name=method.name
                ))
        
        return conversions
    
    def extract_validation_patterns(self, class_node: ast.ClassDef) -> List[str]:
        """Extract field validation patterns."""
        patterns = []
        
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                # Look for field_validator decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                        if decorator.func.id == "field_validator":
                            field_names = []
                            for arg in decorator.args:
                                if isinstance(arg, ast.Constant):
                                    field_names.append(str(arg.value))
                            patterns.append(f"field_validator({', '.join(field_names)}) -> {node.name}")
        
        return patterns
    
    def analyze_schema_class(self, class_node: ast.ClassDef, file_path: Path) -> SchemaClass:
        """Analyze a single schema class comprehensively."""
        # Extract base classes
        base_classes = []
        for base in class_node.bases:
            base_classes.append(ast.unparse(base))
        
        # Extract class docstring
        docstring = None
        if (class_node.body and isinstance(class_node.body[0], ast.Expr) and
            isinstance(class_node.body[0].value, ast.Constant) and
            isinstance(class_node.body[0].value.value, str)):
            docstring = class_node.body[0].value.value
        
        # Extract fields
        fields = self.extract_field_annotations(class_node)
        
        # Extract methods
        methods = []
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                methods.append(self.extract_method_signature(node))
        
        # Analyze type conversions
        type_conversions = self.analyze_type_conversions(methods, file_path)
        
        # Extract validation patterns
        validation_patterns = self.extract_validation_patterns(class_node)
        
        # Find computed properties
        computed_properties = []
        for method in methods:
            if "cached_property" in method.decorators or "computed_field" in method.decorators:
                computed_properties.append(method.name)
        
        return SchemaClass(
            name=class_node.name,
            file_path=str(file_path),
            line_number=class_node.lineno,
            base_classes=base_classes,
            fields=fields,
            methods=methods,
            type_adapters=[],  # Will be populated later
            type_conversions=type_conversions,
            imports=[],  # Will be populated later
            docstring=docstring,
            validation_patterns=validation_patterns,
            computed_properties=computed_properties
        )
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single API schema file."""
        tree = self.parse_file_safely(file_path)
        if not tree:
            return
        
        self.results.total_files_scanned += 1
        
        # Extract imports
        imports = self.extract_imports(tree)
        
        # Extract TypeAdapters
        type_adapters = self.extract_type_adapters(tree, file_path)
        self.results.type_adapter_inventory.extend(type_adapters)
        
        # Find and analyze schema classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this is likely an API schema class
                if (node.name.startswith(('Api', 'Base')) or 
                    any('BaseApiModel' in base_name or 'BaseEntity' in base_name or 
                        'BaseValueObject' in base_name or 'BaseCommand' in base_name
                        for base_name in [ast.unparse(base) for base in node.bases])):
                    
                    schema = self.analyze_schema_class(node, file_path)
                    schema.imports = imports
                    schema.type_adapters = type_adapters
                    
                    self.results.schemas.append(schema)
                    self.results.total_schemas_found += 1
                    
                    # Update inheritance tree
                    for base_class in schema.base_classes:
                        self.results.inheritance_tree[base_class].append(schema.name)
                    
                    # Collect type conversion patterns
                    self.results.conversion_patterns.extend(schema.type_conversions)
    
    def identify_inconsistencies(self) -> None:
        """Identify pattern inconsistencies and anti-patterns."""
        inconsistencies = []
        
        # Check for missing conversion methods
        required_methods = {"to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"}
        
        for schema in self.results.schemas:
            if any(base for base in schema.base_classes if "BaseEntity" in base):
                schema_methods = {method.name for method in schema.methods}
                missing_methods = required_methods - schema_methods
                
                if missing_methods:
                    inconsistencies.append(
                        f"{schema.name} ({schema.file_path}) missing required methods: {missing_methods}"
                    )
        
        # Check for TypeAdapter naming conventions
        for adapter in self.results.type_adapter_inventory:
            if not adapter.name.endswith("Adapter"):
                inconsistencies.append(
                    f"TypeAdapter naming issue: {adapter.name} should end with 'Adapter' "
                    f"({adapter.file_path}:{adapter.line_number})"
                )
        
        # Check for validation patterns
        for schema in self.results.schemas:
            if schema.fields and not schema.validation_patterns:
                inconsistencies.append(
                    f"{schema.name} has fields but no validation patterns defined"
                )
        
        self.results.inconsistencies = inconsistencies
    
    def run_analysis(self, include_performance: bool = False) -> AnalysisResults:
        """Run comprehensive API schema analysis."""
        start_time = time.time()
        
        print("🔍 Discovering API schema files...")
        schema_files = self.discover_api_schema_files()
        print(f"Found {len(schema_files)} API schema files")
        
        print("📊 Analyzing schema patterns...")
        for i, file_path in enumerate(schema_files, 1):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(schema_files)} files...")
            self.analyze_file(file_path)
        
        print("🔎 Identifying inconsistencies...")
        self.identify_inconsistencies()
        
        # Performance metrics
        analysis_time = time.time() - start_time
        self.results.performance_metrics = {
            "analysis_time_seconds": analysis_time,
            "files_per_second": len(schema_files) / analysis_time if analysis_time > 0 else 0,
            "average_schemas_per_file": (
                self.results.total_schemas_found / self.results.total_files_scanned 
                if self.results.total_files_scanned > 0 else 0
            )
        }
        
        return self.results


def format_results_text(results: AnalysisResults) -> str:
    """Format analysis results as human-readable text."""
    output = []
    
    output.append("=" * 80)
    output.append("API SCHEMA PATTERN ANALYSIS REPORT")
    output.append("=" * 80)
    output.append("")
    
    # Summary
    output.append("📊 SUMMARY")
    output.append("-" * 40)
    output.append(f"Total files scanned: {results.total_files_scanned}")
    output.append(f"Total schemas found: {results.total_schemas_found}")
    output.append(f"TypeAdapters found: {len(results.type_adapter_inventory)}")
    output.append(f"Conversion patterns: {len(results.conversion_patterns)}")
    output.append(f"File errors: {len(results.file_errors)}")
    output.append(f"Inconsistencies found: {len(results.inconsistencies)}")
    output.append("")
    
    # Performance metrics
    if results.performance_metrics:
        output.append("⚡ PERFORMANCE METRICS")
        output.append("-" * 40)
        for key, value in results.performance_metrics.items():
            output.append(f"{key}: {value:.2f}")
        output.append("")
    
    # Inheritance tree
    if results.inheritance_tree:
        output.append("🌳 INHERITANCE PATTERNS")
        output.append("-" * 40)
        for base_class, subclasses in results.inheritance_tree.items():
            if subclasses:
                output.append(f"{base_class}:")
                for subclass in sorted(subclasses):
                    output.append(f"  └── {subclass}")
        output.append("")
    
    # TypeAdapter inventory
    if results.type_adapter_inventory:
        output.append("🔧 TYPEADAPTER INVENTORY")
        output.append("-" * 40)
        for adapter in results.type_adapter_inventory[:10]:  # Show first 10
            output.append(f"{adapter.name}: {adapter.type_definition}")
            output.append(f"  Location: {adapter.file_path}:{adapter.line_number}")
        if len(results.type_adapter_inventory) > 10:
            output.append(f"  ... and {len(results.type_adapter_inventory) - 10} more")
        output.append("")
    
    # Conversion patterns summary
    if results.conversion_patterns:
        output.append("🔄 CONVERSION PATTERNS SUMMARY")
        output.append("-" * 40)
        
        conversion_counts = defaultdict(int)
        for conversion in results.conversion_patterns:
            conversion_counts[conversion.conversion_direction] += 1
        
        for direction, count in conversion_counts.items():
            output.append(f"{direction}: {count} implementations")
        output.append("")
    
    # Inconsistencies
    if results.inconsistencies:
        output.append("⚠️  INCONSISTENCIES AND ANTI-PATTERNS")
        output.append("-" * 40)
        for inconsistency in results.inconsistencies:
            output.append(f"• {inconsistency}")
        output.append("")
    
    # File errors
    if results.file_errors:
        output.append("❌ FILE PARSING ERRORS")
        output.append("-" * 40)
        for file_path, error in results.file_errors:
            output.append(f"• {file_path}: {error}")
        output.append("")
    
    # Schema examples
    if results.schemas:
        output.append("📝 SCHEMA EXAMPLES")
        output.append("-" * 40)
        
        # Show a few representative schemas
        example_schemas = [s for s in results.schemas if "BaseEntity" in str(s.base_classes)][:3]
        
        for schema in example_schemas:
            output.append(f"\n{schema.name} ({schema.file_path})")
            output.append(f"  Base classes: {', '.join(schema.base_classes)}")
            output.append(f"  Fields: {len(schema.fields)}")
            output.append(f"  Methods: {', '.join(m.name for m in schema.methods)}")
            output.append(f"  TypeAdapters: {len(schema.type_adapters)}")
            output.append(f"  Validation patterns: {len(schema.validation_patterns)}")
    
    return "\n".join(output)


@click.command()
@click.option('--output-format', '-f', default='text', type=click.Choice(['text', 'json']),
              help='Output format (text or json)')
@click.option('--output-file', '-o', help='Output file path (default: stdout)')
@click.option('--detailed', '-d', is_flag=True, help='Include detailed analysis')
@click.option('--performance-metrics', '-p', is_flag=True, help='Include performance metrics')
@click.option('--root-path', '-r', default='src', help='Root path to scan (default: src)')
def main(output_format: str, output_file: Optional[str], detailed: bool, 
         performance_metrics: bool, root_path: str):
    """Analyze API schema patterns in the codebase."""
    
    # Determine root path
    project_root = Path.cwd()
    scan_root = project_root / root_path
    
    if not scan_root.exists():
        click.echo(f"❌ Root path {scan_root} does not exist", err=True)
        sys.exit(1)
    
    # Run analysis
    analyzer = ApiSchemaAnalyzer(scan_root)
    results = analyzer.run_analysis(include_performance=performance_metrics)
    
    # Format output
    if output_format == 'json':
        # Convert to JSON-serializable format
        output_data = {
            "summary": {
                "total_files_scanned": results.total_files_scanned,
                "total_schemas_found": results.total_schemas_found,
                "type_adapters_found": len(results.type_adapter_inventory),
                "conversion_patterns": len(results.conversion_patterns),
                "inconsistencies_found": len(results.inconsistencies),
                "file_errors": len(results.file_errors)
            },
            "schemas": [
                {
                    "name": schema.name,
                    "file_path": schema.file_path,
                    "base_classes": schema.base_classes,
                    "field_count": len(schema.fields),
                    "method_names": [m.name for m in schema.methods],
                    "type_adapters": len(schema.type_adapters),
                    "validation_patterns": schema.validation_patterns
                }
                for schema in results.schemas
            ],
            "type_adapters": [
                {
                    "name": adapter.name,
                    "type_definition": adapter.type_definition,
                    "file_path": adapter.file_path,
                    "line_number": adapter.line_number
                }
                for adapter in results.type_adapter_inventory
            ],
            "inconsistencies": results.inconsistencies,
            "file_errors": [{"file": f, "error": e} for f, e in results.file_errors],
            "performance_metrics": results.performance_metrics
        }
        
        if detailed:
            # Add detailed information
            output_data["detailed_schemas"] = [
                {
                    "name": schema.name,
                    "file_path": schema.file_path,
                    "line_number": schema.line_number,
                    "base_classes": schema.base_classes,
                    "fields": schema.fields,
                    "methods": [
                        {
                            "name": method.name,
                            "args": method.args,
                            "return_type": method.return_type,
                            "decorators": method.decorators,
                            "is_classmethod": method.is_classmethod
                        }
                        for method in schema.methods
                    ],
                    "docstring": schema.docstring,
                    "validation_patterns": schema.validation_patterns,
                    "computed_properties": schema.computed_properties
                }
                for schema in results.schemas
            ]
        
        output_content = json.dumps(output_data, indent=2)
    else:
        output_content = format_results_text(results)
    
    # Write output
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        click.echo(f"✅ Analysis results written to {output_file}")
    else:
        click.echo(output_content)
    
    # Summary
    click.echo(f"\n✅ Analysis complete: {results.total_schemas_found} schemas found in {results.total_files_scanned} files")
    if results.inconsistencies:
        click.echo(f"⚠️  Found {len(results.inconsistencies)} inconsistencies")
    if results.file_errors:
        click.echo(f"❌ {len(results.file_errors)} files had parsing errors")


if __name__ == "__main__":
    main() 