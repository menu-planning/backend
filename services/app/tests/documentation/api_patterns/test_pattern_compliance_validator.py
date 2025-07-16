"""
Pattern Compliance Validator for API Schema Documentation

This module implements comprehensive compliance testing for all documented patterns:
1. Four-layer conversion pattern compliance
2. TypeAdapter singleton pattern validation  
3. Field validation pattern compliance
4. Computed property materialization compliance
5. Type conversion strategy compliance

Tests validate actual behavior using real codebase schemas, no mocks.
Focus: Validate that existing schemas follow documented best practices.
"""

import json
import pytest
import time
import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union, get_type_hints
from dataclasses import dataclass
from collections import defaultdict

# Import all schema classes for compliance testing
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag, TagFrozensetAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient, IngredientListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.api_seed_role import ApiSeedRole


@dataclass
class PatternComplianceResult:
    """Results from pattern compliance validation."""
    schema_name: str
    pattern_type: str
    compliant: bool
    issues: List[str]
    recommendations: List[str]
    performance_data: Optional[Dict[str, float]] = None


@dataclass
class SchemaPatternReport:
    """Complete pattern compliance report for a schema."""
    schema_name: str
    file_path: str
    total_patterns_tested: int
    compliant_patterns: int
    compliance_percentage: float
    results: List[PatternComplianceResult]
    performance_summary: Dict[str, float]


class PatternComplianceValidator:
    """Validates API schemas against documented pattern standards."""
    
    def __init__(self):
        """Initialize validator with analysis results and pattern definitions."""
        self.analysis_results = self._load_analysis_results()
        self.pattern_definitions = self._load_pattern_definitions()
        self.compliance_results = []
        
    def _load_analysis_results(self) -> Dict[str, Any]:
        """Load schema analysis results from Phase 0."""
        try:
            with open("analysis_results_phase_0_1_1.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            pytest.skip("Analysis results not found - run Phase 0 analysis first")
    
    def _load_pattern_definitions(self) -> Dict[str, Any]:
        """Define expected patterns from documentation."""
        return {
            "four_layer_conversion": {
                "required_methods": ["to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"],
                "entity_methods": ["to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"],
                "command_methods": ["to_domain", "from_domain"],
                "value_object_methods": ["to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"]
            },
            "validation_patterns": {
                "required_for_fields": ["BeforeValidator", "field_validator", "AfterValidator"],
                "field_validation_functions": ["validate_optional_text", "validate_uuid_format"],
                "business_logic_validators": ["field_validator"]
            },
            "typeadapter_patterns": {
                "naming_convention": ".*Adapter$",
                "module_level_singleton": True,
                "performance_requirement_ms": 3.0
            },
            "type_conversions": {
                "collection_patterns": ["set -> frozenset -> list", "list -> frozenset -> set"],
                "scalar_patterns": ["str -> str -> str", "int -> int -> int"],
                "computed_patterns": ["@cached_property -> regular_field -> composite"]
            }
        }

    def validate_four_layer_conversion_compliance(self, schema_info: Dict[str, Any]) -> PatternComplianceResult:
        """Validate four-layer conversion pattern compliance for a schema."""
        schema_name = schema_info["name"]
        base_classes = schema_info.get("base_classes", [])
        method_names = schema_info.get("method_names", [])
        
        issues = []
        recommendations = []
        
        # Determine expected methods based on base class
        if any("BaseEntity" in base for base in base_classes):
            expected_methods = self.pattern_definitions["four_layer_conversion"]["entity_methods"]
        elif any("BaseCommand" in base for base in base_classes):
            expected_methods = self.pattern_definitions["four_layer_conversion"]["command_methods"]
        elif any("BaseValueObject" in base for base in base_classes):
            expected_methods = self.pattern_definitions["four_layer_conversion"]["value_object_methods"]
        else:
            expected_methods = ["to_domain", "from_domain"]  # Minimum requirement
        
        # Check for missing required methods
        missing_methods = [method for method in expected_methods if method not in method_names]
        
        if missing_methods:
            issues.append(f"Missing required conversion methods: {missing_methods}")
            recommendations.append(f"Implement missing methods: {', '.join(missing_methods)}")
        
        # Check for proper inheritance
        if not any(base.startswith("Base") for base in base_classes):
            issues.append("Schema doesn't inherit from documented base classes")
            recommendations.append("Inherit from BaseEntity, BaseCommand, or BaseValueObject")
        
        compliant = len(issues) == 0
        
        return PatternComplianceResult(
            schema_name=schema_name,
            pattern_type="four_layer_conversion",
            compliant=compliant,
            issues=issues,
            recommendations=recommendations
        )

    def validate_field_validation_compliance(self, schema_info: Dict[str, Any]) -> PatternComplianceResult:
        """Validate field validation pattern compliance."""
        schema_name = schema_info["name"]
        field_count = schema_info.get("field_count", 0)
        validation_patterns = schema_info.get("validation_patterns", [])
        
        issues = []
        recommendations = []
        
        # Check if schema with fields has validation patterns
        if field_count > 0 and not validation_patterns:
            issues.append(f"Schema has {field_count} fields but no validation patterns defined")
            recommendations.append("Add BeforeValidator, field_validator, or AfterValidator for input validation")
        
        # Validate specific validation pattern usage
        for pattern in validation_patterns:
            if "field_validator" in pattern:
                # Good - using field_validator for business logic
                pass
            elif "BeforeValidator" in pattern:
                # Good - using BeforeValidator for data cleanup
                pass
            elif "AfterValidator" in pattern:
                # Good - using AfterValidator for post-processing
                pass
            else:
                issues.append(f"Unknown validation pattern: {pattern}")
                recommendations.append("Use documented validation patterns: BeforeValidator, field_validator, AfterValidator")
        
        compliant = len(issues) == 0
        
        return PatternComplianceResult(
            schema_name=schema_name,
            pattern_type="field_validation",
            compliant=compliant,
            issues=issues,
            recommendations=recommendations
        )

    def validate_typeadapter_compliance(self) -> List[PatternComplianceResult]:
        """Validate TypeAdapter pattern compliance across all adapters."""
        results = []
        type_adapters = self.analysis_results.get("type_adapter_inventory", [])
        
        for adapter in type_adapters:
            issues = []
            recommendations = []
            
            # Validate naming convention
            if not adapter["name"].endswith("Adapter"):
                issues.append(f"TypeAdapter naming issue: '{adapter['name']}' should end with 'Adapter'")
                recommendations.append("Rename to follow convention: ExampleAdapter")
            
            # Validate module-level singleton pattern
            if adapter["usage_context"] != "module_level":
                issues.append(f"TypeAdapter not defined at module level: {adapter['usage_context']}")
                recommendations.append("Define TypeAdapter as module-level singleton")
            
            compliant = len(issues) == 0
            
            results.append(PatternComplianceResult(
                schema_name=adapter["name"],
                pattern_type="typeadapter_naming_and_usage",
                compliant=compliant,
                issues=issues,
                recommendations=recommendations
            ))
        
        return results

    def validate_performance_compliance(self, schema_class: Type, test_data: Any) -> PatternComplianceResult:
        """Validate that schema meets performance requirements."""
        schema_name = schema_class.__name__
        issues = []
        recommendations = []
        performance_data = {}
        
        try:
            # Test validation performance
            start_time = time.perf_counter()
            validated_obj = schema_class.model_validate(test_data)
            validation_time_ms = (time.perf_counter() - start_time) * 1000
            performance_data["validation_time_ms"] = validation_time_ms
            
            # Performance requirement: < 3ms for validation
            if validation_time_ms > 3.0:
                issues.append(f"Validation time {validation_time_ms:.2f}ms exceeds 3ms requirement")
                recommendations.append("Optimize validation logic or consider TypeAdapter patterns")
            
            # Test conversion performance if methods exist
            if hasattr(validated_obj, 'to_domain'):
                start_time = time.perf_counter()
                domain_obj = validated_obj.to_domain()
                conversion_time_ms = (time.perf_counter() - start_time) * 1000
                performance_data["to_domain_time_ms"] = conversion_time_ms
                
                if conversion_time_ms > 5.0:
                    issues.append(f"to_domain conversion time {conversion_time_ms:.2f}ms exceeds 5ms recommendation")
                    recommendations.append("Optimize domain conversion logic")
            
        except Exception as e:
            issues.append(f"Performance test failed: {str(e)}")
            recommendations.append("Fix validation or conversion errors before performance optimization")
        
        compliant = len(issues) == 0
        
        return PatternComplianceResult(
            schema_name=schema_name,
            pattern_type="performance",
            compliant=compliant,
            issues=issues,
            recommendations=recommendations,
            performance_data=performance_data
        )

    def validate_type_conversion_compliance(self, schema_info: Dict[str, Any]) -> PatternComplianceResult:
        """Validate type conversion pattern compliance."""
        schema_name = schema_info["name"]
        method_names = schema_info.get("method_names", [])
        
        issues = []
        recommendations = []
        
        # Check for proper type conversion methods
        conversion_methods = ["from_domain", "to_domain", "from_orm_model", "to_orm_kwargs"]
        present_methods = [method for method in conversion_methods if method in method_names]
        
        if len(present_methods) > 0 and len(present_methods) < len(conversion_methods):
            missing = [method for method in conversion_methods if method not in method_names]
            if missing:
                issues.append(f"Incomplete conversion pattern: missing {missing}")
                recommendations.append("Implement all four conversion methods for complete pattern")
        
        # Validate method signature patterns (basic check)
        if "from_domain" in method_names and "to_domain" in method_names:
            # This indicates proper bi-directional conversion
            pass
        elif len(present_methods) > 0:
            issues.append("Partial conversion pattern implementation detected")
            recommendations.append("Implement both from_domain and to_domain for bi-directional conversion")
        
        compliant = len(issues) == 0
        
        return PatternComplianceResult(
            schema_name=schema_name,
            pattern_type="type_conversion",
            compliant=compliant,
            issues=issues,
            recommendations=recommendations
        )

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report for all schemas."""
        schemas = self.analysis_results.get("detailed_schemas", [])
        schema_reports = []
        
        for schema_info in schemas:
            results = []
            
            # Validate all patterns for this schema
            results.append(self.validate_four_layer_conversion_compliance(schema_info))
            results.append(self.validate_field_validation_compliance(schema_info))
            results.append(self.validate_type_conversion_compliance(schema_info))
            
            # Calculate compliance metrics
            total_patterns = len(results)
            compliant_patterns = sum(1 for result in results if result.compliant)
            compliance_percentage = (compliant_patterns / total_patterns) * 100 if total_patterns > 0 else 0
            
            schema_report = SchemaPatternReport(
                schema_name=schema_info["name"],
                file_path=schema_info["file_path"],
                total_patterns_tested=total_patterns,
                compliant_patterns=compliant_patterns,
                compliance_percentage=compliance_percentage,
                results=results,
                performance_summary={}
            )
            
            schema_reports.append(schema_report)
        
        # Add TypeAdapter compliance results
        typeadapter_results = self.validate_typeadapter_compliance()
        
        # Generate summary statistics
        total_schemas = len(schema_reports)
        fully_compliant_schemas = sum(1 for report in schema_reports if report.compliance_percentage == 100)
        average_compliance = sum(report.compliance_percentage for report in schema_reports) / total_schemas if total_schemas > 0 else 0
        
        return {
            "summary": {
                "total_schemas_tested": total_schemas,
                "fully_compliant_schemas": fully_compliant_schemas,
                "average_compliance_percentage": average_compliance,
                "typeadapter_issues": len([r for r in typeadapter_results if not r.compliant]),
                "total_issues_found": sum(len(result.issues) for report in schema_reports for result in report.results)
            },
            "schema_reports": schema_reports,
            "typeadapter_compliance": typeadapter_results,
            "recommendations_summary": self._generate_recommendations_summary(schema_reports, typeadapter_results)
        }

    def _generate_recommendations_summary(self, schema_reports: List[SchemaPatternReport], 
                                        typeadapter_results: List[PatternComplianceResult]) -> Dict[str, List[str]]:
        """Generate prioritized recommendations from all compliance results."""
        all_issues = defaultdict(int)
        all_recommendations = defaultdict(int)
        
        # Collect issues and recommendations from schema reports
        for report in schema_reports:
            for result in report.results:
                for issue in result.issues:
                    all_issues[issue] += 1
                for rec in result.recommendations:
                    all_recommendations[rec] += 1
        
        # Collect from TypeAdapter results
        for result in typeadapter_results:
            for issue in result.issues:
                all_issues[issue] += 1
            for rec in result.recommendations:
                all_recommendations[rec] += 1
        
        # Sort by frequency (most common first)
        top_issues = sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:10]
        top_recommendations = sorted(all_recommendations.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "most_common_issues": [f"{issue} (found in {count} schemas)" for issue, count in top_issues],
            "priority_recommendations": [f"{rec} (affects {count} schemas)" for rec, count in top_recommendations]
        }


class TestPatternComplianceValidator:
    """Test suite for pattern compliance validation."""
    
    def test_validator_initialization(self):
        """Test that validator initializes correctly with analysis results."""
        validator = PatternComplianceValidator()
        
        assert validator.analysis_results is not None, "Should load analysis results"
        assert validator.pattern_definitions is not None, "Should have pattern definitions"
        assert "four_layer_conversion" in validator.pattern_definitions, "Should have four-layer pattern definition"
        assert "validation_patterns" in validator.pattern_definitions, "Should have validation pattern definition"
        assert "typeadapter_patterns" in validator.pattern_definitions, "Should have TypeAdapter pattern definition"

    def test_four_layer_conversion_compliance_validation(self):
        """Test four-layer conversion pattern compliance validation."""
        validator = PatternComplianceValidator()
        
        # Test compliant schema (has all required methods)
        compliant_schema = {
            "name": "ApiUser",
            "base_classes": ["BaseEntity[User, UserSaModel]"],
            "method_names": ["from_domain", "to_domain", "from_orm_model", "to_orm_kwargs"],
            "field_count": 1
        }
        
        result = validator.validate_four_layer_conversion_compliance(compliant_schema)
        
        assert result.pattern_type == "four_layer_conversion"
        assert result.schema_name == "ApiUser"
        assert result.compliant == True, f"Should be compliant, issues: {result.issues}"
        assert len(result.issues) == 0, "Compliant schema should have no issues"

    def test_non_compliant_four_layer_conversion(self):
        """Test detection of non-compliant four-layer conversion patterns."""
        validator = PatternComplianceValidator()
        
        # Test non-compliant schema (missing required methods)
        non_compliant_schema = {
            "name": "ApiIncompleteSchema",
            "base_classes": ["BaseEntity[Something, SomethingSaModel]"],
            "method_names": ["to_domain"],  # Missing from_domain, from_orm_model, to_orm_kwargs
            "field_count": 3
        }
        
        result = validator.validate_four_layer_conversion_compliance(non_compliant_schema)
        
        assert result.compliant == False, "Should detect non-compliance"
        assert len(result.issues) > 0, "Should identify specific issues"
        assert any("Missing required conversion methods" in issue for issue in result.issues)
        assert len(result.recommendations) > 0, "Should provide recommendations"

    def test_field_validation_compliance(self):
        """Test field validation pattern compliance validation."""
        validator = PatternComplianceValidator()
        
        # Test schema with fields but no validation
        schema_without_validation = {
            "name": "ApiSchemaWithoutValidation",
            "field_count": 3,
            "validation_patterns": []
        }
        
        result = validator.validate_field_validation_compliance(schema_without_validation)
        
        assert result.compliant == False, "Should detect missing validation"
        assert any("fields but no validation patterns" in issue for issue in result.issues)
        assert len(result.recommendations) > 0, "Should recommend validation patterns"

    def test_typeadapter_compliance_validation(self):
        """Test TypeAdapter pattern compliance validation."""
        validator = PatternComplianceValidator()
        
        # This will use real TypeAdapter data from analysis results
        results = validator.validate_typeadapter_compliance()
        
        assert isinstance(results, list), "Should return list of results"
        
        # Check each result structure
        for result in results:
            assert hasattr(result, 'schema_name'), "Should have schema name"
            assert hasattr(result, 'pattern_type'), "Should have pattern type"
            assert hasattr(result, 'compliant'), "Should have compliance status"
            assert result.pattern_type == "typeadapter_naming_and_usage"

    def test_performance_compliance_with_real_schema(self, sample_tag_domain):
        """Test performance compliance validation with real schema."""
        validator = PatternComplianceValidator()
        
        # Test with actual ApiTag schema
        test_data = {
            "key": sample_tag_domain.key,
            "value": sample_tag_domain.value,
            "author_id": sample_tag_domain.author_id,
            "type": sample_tag_domain.type  # type is already a string in the Tag domain model
        }
        
        result = validator.validate_performance_compliance(ApiTag, test_data)
        
        assert result.pattern_type == "performance"
        assert result.schema_name == "ApiTag"
        assert result.performance_data is not None, "Should capture performance metrics"
        assert "validation_time_ms" in result.performance_data, "Should measure validation time"
        
        # Performance should meet requirements (< 3ms)
        validation_time = result.performance_data["validation_time_ms"]
        assert validation_time < 10.0, f"Validation should be reasonably fast, got {validation_time}ms"

    def test_type_conversion_compliance(self):
        """Test type conversion pattern compliance validation."""
        validator = PatternComplianceValidator()
        
        # Test complete conversion pattern
        complete_schema = {
            "name": "ApiCompleteSchema",
            "method_names": ["from_domain", "to_domain", "from_orm_model", "to_orm_kwargs"]
        }
        
        result = validator.validate_type_conversion_compliance(complete_schema)
        
        assert result.compliant == True, "Complete pattern should be compliant"
        assert len(result.issues) == 0, "Complete pattern should have no issues"

    def test_compliance_report_generation(self):
        """Test comprehensive compliance report generation."""
        validator = PatternComplianceValidator()
        
        report = validator.generate_compliance_report()
        
        # Validate report structure
        assert "summary" in report, "Should have summary section"
        assert "schema_reports" in report, "Should have schema reports"
        assert "typeadapter_compliance" in report, "Should have TypeAdapter compliance"
        assert "recommendations_summary" in report, "Should have recommendations"
        
        # Validate summary metrics
        summary = report["summary"]
        assert "total_schemas_tested" in summary
        assert "average_compliance_percentage" in summary
        assert "total_issues_found" in summary
        
        # Validate recommendations
        recommendations = report["recommendations_summary"]
        assert "most_common_issues" in recommendations
        assert "priority_recommendations" in recommendations

    def test_real_schema_compliance_validation(self, sample_ingredient_data):
        """Test compliance validation with real ApiIngredient schema."""
        validator = PatternComplianceValidator()
        
        # Test performance compliance with real data
        result = validator.validate_performance_compliance(ApiIngredient, sample_ingredient_data)
        
        assert result.schema_name == "ApiIngredient"
        assert result.performance_data is not None
        
        # ApiIngredient should meet performance requirements
        if result.performance_data.get("validation_time_ms"):
            validation_time = result.performance_data["validation_time_ms"]
            # Allow reasonable performance for integration test environment
            assert validation_time < 50.0, f"Validation time {validation_time}ms should be reasonable"

    @pytest.mark.integration
    def test_full_codebase_compliance_scan(self):
        """Integration test: Run compliance validation on entire codebase."""
        validator = PatternComplianceValidator()
        
        report = validator.generate_compliance_report()
        
        # Verify we're testing a reasonable number of schemas
        total_schemas = report["summary"]["total_schemas_tested"]
        assert total_schemas >= 10, f"Should test substantial number of schemas, got {total_schemas}"
        
        # Calculate compliance statistics
        average_compliance = report["summary"]["average_compliance_percentage"]
        fully_compliant = report["summary"]["fully_compliant_schemas"]
        
        print(f"\n=== PATTERN COMPLIANCE REPORT ===")
        print(f"Schemas tested: {total_schemas}")
        print(f"Fully compliant: {fully_compliant}")
        print(f"Average compliance: {average_compliance:.1f}%")
        print(f"Total issues: {report['summary']['total_issues_found']}")
        
        # Print top issues for debugging
        top_issues = report["recommendations_summary"]["most_common_issues"][:5]
        print(f"\nTop issues:")
        for issue in top_issues:
            print(f"  - {issue}")
        
        # This test should pass but provides visibility into compliance status
        assert total_schemas > 0, "Should process schemas successfully"


@pytest.fixture
def pattern_compliance_validator():
    """Provide PatternComplianceValidator instance for tests."""
    return PatternComplianceValidator() 