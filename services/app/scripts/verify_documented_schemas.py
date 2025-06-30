#!/usr/bin/env python3
"""
Schema Documentation Verification Script

This script verifies that all documented API schemas:
1. Actually exist in the codebase
2. Compile without syntax errors
3. Have the documented conversion methods
4. Follow the documented type conversion patterns

Usage:
    poetry run python scripts/verify_documented_schemas.py
"""

import importlib.util
import sys
from pathlib import Path
from typing import List, Tuple

import click


def verify_schema_file_exists_and_compiles(file_path: str) -> Tuple[bool, str]:
    """Verify that a schema file exists and compiles."""
    try:
        path = Path(file_path)
        if not path.exists():
            return False, f"File does not exist: {file_path}"
        
        # Try to compile the file
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, file_path, 'exec')
        return True, "File exists and compiles successfully"
        
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def verify_schema_methods(file_path: str, expected_methods: List[str]) -> Tuple[bool, str]:
    """Verify that a schema has the expected conversion methods."""
    try:
        # This is a simplified check - in practice, we'd use AST parsing
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_methods = []
        for method in expected_methods:
            if f"def {method}(" not in content:
                missing_methods.append(method)
        
        if missing_methods:
            return False, f"Missing methods: {missing_methods}"
        
        return True, "All expected methods found"
        
    except Exception as e:
        return False, f"Error checking methods: {e}"


@click.command()
def main():
    """Verify documented API schemas exist and compile."""
    
    # Key schemas referenced in documentation with expected methods
    documented_schemas = [
        {
            "file": "src/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/api_meal.py",
            "methods": ["to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"]
        },
        {
            "file": "src/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/api_recipe.py", 
            "methods": ["to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"]
        },
        {
            "file": "src/contexts/seedwork/shared/adapters/api_schemas/base_api_model.py",
            "methods": ["to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"]
        },
        {
            "file": "src/contexts/shared_kernel/adapters/api_schemas/value_objects/tag/tag.py",
            "methods": ["to_domain", "from_domain", "from_orm_model", "to_orm_kwargs"]
        }
    ]
    
    # TypeAdapter definitions to verify
    type_adapters = [
        {
            "file": "src/contexts/shared_kernel/adapters/api_schemas/value_objects/tag/tag.py",
            "adapter": "TagFrozensetAdapter"
        },
        {
            "file": "src/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/api_recipe.py",
            "adapter": "RecipeListAdapter"
        }
    ]
    
    print("🔍 Verifying documented API schemas...")
    
    success_count = 0
    total_tests = 0
    
    # Verify schema files exist and compile
    for schema in documented_schemas:
        file_path = schema["file"]
        methods = schema["methods"]
        
        total_tests += 1
        exists, message = verify_schema_file_exists_and_compiles(file_path)
        
        if exists:
            print(f"✅ {file_path}: {message}")
            
            # Verify methods exist
            total_tests += 1
            has_methods, method_message = verify_schema_methods(file_path, methods)
            
            if has_methods:
                print(f"✅ {file_path} methods: {method_message}")
                success_count += 2
            else:
                print(f"❌ {file_path} methods: {method_message}")
                success_count += 1
        else:
            print(f"❌ {file_path}: {message}")
    
    # Verify TypeAdapter definitions
    for adapter_def in type_adapters:
        file_path = adapter_def["file"]
        adapter_name = adapter_def["adapter"]
        
        total_tests += 1
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if f"{adapter_name} = TypeAdapter(" in content:
                print(f"✅ TypeAdapter {adapter_name} found in {file_path}")
                success_count += 1
            else:
                print(f"❌ TypeAdapter {adapter_name} not found in {file_path}")
                
        except Exception as e:
            print(f"❌ Error checking TypeAdapter {adapter_name}: {e}")
    
    # Summary
    print(f"\n📊 Verification Summary: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All documented schemas verified successfully!")
        return 0
    else:
        print(f"⚠️  {total_tests - success_count} verification(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 