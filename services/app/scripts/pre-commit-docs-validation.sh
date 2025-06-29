#!/bin/bash

# Pre-commit Documentation Validation Script
# Validates documentation accuracy and consistency before commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="docs/architecture"
TEMP_DIR="/tmp/pre-commit-docs-validation"
EXIT_CODE=0

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    EXIT_CODE=1
}

log_section() {
    echo -e "${BLUE}[DOCS-VALIDATION]${NC} $1"
}

# Create temp directory
mkdir -p "$TEMP_DIR"

# Main validation function
main() {
    log_section "🔍 Pre-commit Documentation Validation"
    
    # Quick prerequisite checks
    check_prerequisites_quick
    
    # Fast validation checks suitable for pre-commit
    validate_file_existence_quick
    validate_basic_syntax
    validate_critical_examples
    validate_cross_references_quick
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_info "✅ Documentation validation passed"
    else
        log_error "❌ Documentation validation failed"
        echo ""
        echo "💡 To fix documentation issues:"
        echo "   • Run full validation: scripts/validate-docs.sh"
        echo "   • Check specific examples that failed"
        echo "   • Ensure all file references are correct"
        echo "   • Validate code examples work in environment"
    fi
    
    exit $EXIT_CODE
}

# Quick prerequisite check
check_prerequisites_quick() {
    log_section "📋 Checking Prerequisites"
    
    # Check poetry is available
    if ! command -v poetry >/dev/null 2>&1; then
        log_error "❌ poetry is not available"
        return
    fi
    
    # Quick environment check - don't install, just verify
    if ! poetry env info >/dev/null 2>&1; then
        log_warn "⚠️  Poetry environment not configured (skipping example tests)"
        SKIP_EXAMPLES=true
    else
        log_info "✅ Poetry environment available"
        SKIP_EXAMPLES=false
    fi
}

# Quick file existence validation
validate_file_existence_quick() {
    log_section "📁 Validating File References"
    
    local critical_files=(
        "$DOCS_DIR/quick-start-guide.md"
        "$DOCS_DIR/technical-specifications.md"
        "$DOCS_DIR/ai-agent-workflows.md"
        "$DOCS_DIR/decision-trees.md"
        "$DOCS_DIR/pattern-library.md"
        "$DOCS_DIR/troubleshooting-guide.md"
        "$DOCS_DIR/domain-rules-reference.md"
    )
    
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            log_info "✅ $file exists"
        else
            log_error "❌ Critical file missing: $file"
        fi
    done
    
    # Check for broken internal file references in changed docs
    if git diff --cached --name-only | grep -q '\.md$'; then
        log_section "🔗 Checking Internal File References"
        
        # Extract file paths from staged markdown files
        git diff --cached --name-only | grep '\.md$' | while read -r file; do
            if [ -f "$file" ]; then
                # Look for file references that might be broken
                if grep -n "src/contexts/" "$file" > "$TEMP_DIR/file_refs.txt" 2>/dev/null; then
                    while IFS=: read -r line_num line_content; do
                        # Extract potential file path
                        file_path=$(echo "$line_content" | grep -o 'src/contexts/[^)]*\.py' | head -1)
                        if [ -n "$file_path" ] && [ ! -f "$file_path" ]; then
                            log_error "❌ Broken file reference in $file:$line_num - $file_path"
                        fi
                    done < "$TEMP_DIR/file_refs.txt"
                fi
            fi
        done
    fi
}

# Basic syntax validation
validate_basic_syntax() {
    log_section "📝 Validating Basic Syntax"
    
    # Check staged markdown files for basic syntax issues
    if git diff --cached --name-only | grep -q '\.md$'; then
        git diff --cached --name-only | grep '\.md$' | while read -r file; do
            if [ -f "$file" ]; then
                log_info "Checking syntax: $file"
                
                # Check for common markdown issues
                # Unclosed code blocks
                if ! awk '/^```/{f=!f} END{if(f) exit 1}' "$file"; then
                    log_error "❌ Unclosed code block in $file"
                fi
                
                # Missing space after hash for headers
                if grep -n '^#[^# ]' "$file" | head -5; then
                    log_warn "⚠️  Potential header formatting issues in $file"
                fi
                
                # Basic link syntax check
                if grep -n '\]\(' "$file" | grep -v 'http' | grep -v '\.md' | head -3; then
                    log_info "ℹ️  Found internal links in $file (will validate separately)"
                fi
            fi
        done
    fi
}

# Validate critical code examples
validate_critical_examples() {
    log_section "🐍 Validating Critical Code Examples"
    
    if [ "$SKIP_EXAMPLES" = "true" ]; then
        log_warn "⚠️  Skipping example validation (no poetry environment)"
        return
    fi
    
    # Test critical imports that are commonly referenced in docs
    log_info "Testing critical domain imports..."
    
    # Create a temporary test script
    cat > "$TEMP_DIR/test_imports.py" << 'EOF'
#!/usr/bin/env python3
"""Quick validation of critical imports for documentation."""

import sys
import traceback

def test_critical_imports():
    """Test imports that are commonly referenced in documentation."""
    critical_imports = [
        "from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal",
        "from src.contexts.recipes_catalog.core.domain.recipe.root_aggregate.recipe import Recipe",
        "from src.contexts.seedwork.shared.domain.entity import Entity",
        "from src.contexts.seedwork.shared.domain.repositories import SaGenericRepository",
    ]
    
    failed_imports = []
    
    for import_statement in critical_imports:
        try:
            exec(import_statement)
            print(f"✅ {import_statement}")
        except Exception as e:
            print(f"❌ {import_statement}")
            print(f"   Error: {e}")
            failed_imports.append(import_statement)
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} critical imports failed")
        return 1
    else:
        print(f"\n✅ All {len(critical_imports)} critical imports successful")
        return 0

if __name__ == "__main__":
    sys.exit(test_critical_imports())
EOF

    # Run the import test
    if poetry run python "$TEMP_DIR/test_imports.py" > "$TEMP_DIR/import_results.txt" 2>&1; then
        log_info "✅ Critical imports validation passed"
        cat "$TEMP_DIR/import_results.txt" | grep "✅"
    else
        log_error "❌ Critical imports validation failed"
        cat "$TEMP_DIR/import_results.txt"
    fi
}

# Quick cross-reference validation
validate_cross_references_quick() {
    log_section "🔗 Validating Cross-References"
    
    # Check for references to other documentation files
    if git diff --cached --name-only | grep -q '\.md$'; then
        git diff --cached --name-only | grep '\.md$' | while read -r file; do
            if [ -f "$file" ]; then
                # Look for markdown links to other docs
                if grep -n '\[.*\](\..*\.md)' "$file" > "$TEMP_DIR/cross_refs.txt" 2>/dev/null; then
                    while IFS=: read -r line_num line_content; do
                        # Extract the linked file
                        linked_file=$(echo "$line_content" | grep -o '](\..*\.md)' | sed 's/](\.\///' | sed 's/)//')
                        if [ -n "$linked_file" ]; then
                            # Check if relative to docs directory
                            full_path="docs/architecture/$linked_file"
                            if [ ! -f "$full_path" ]; then
                                log_error "❌ Broken cross-reference in $file:$line_num - $linked_file"
                            else
                                log_info "✅ Valid cross-reference: $linked_file"
                            fi
                        fi
                    done < "$TEMP_DIR/cross_refs.txt"
                fi
            fi
        done
    fi
}

# Run main function
main "$@" 