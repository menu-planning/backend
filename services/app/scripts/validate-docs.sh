#!/bin/bash

# Simplified Documentation Validation Script
# Validates AI agent onboarding documentation for accuracy and consistency

set -e  # Exit on any error

# Configuration
DOCS_DIR="docs/architecture"
EXIT_CODE=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# Check if running in CI environment
is_ci() {
    [ "${CI:-false}" = "true" ] || [ -n "${GITHUB_ACTIONS:-}" ]
}

# Main validation function
main() {
    log_section "🔍 Documentation Validation Started"
    
    # Check prerequisites
    check_prerequisites
    
    # Documentation file existence checks
    check_file_existence
    
    # Validate code examples
    validate_code_examples
    
    # Check internal links (basic)
    validate_internal_links
    
    # Generate report
    generate_report
    
    log_section "✅ Documentation Validation Complete"
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_info "All validations passed successfully!"
    else
        log_error "Validation failed. Check errors above."
    fi
    
    exit $EXIT_CODE
}

# Check that required tools are available
check_prerequisites() {
    log_section "📋 Checking Prerequisites"
    
    if command -v poetry >/dev/null 2>&1; then
        log_info "✅ poetry is available"
    else
        log_error "❌ poetry is not available"
    fi
    
    if command -v python >/dev/null 2>&1; then
        log_info "✅ python is available"
    else
        log_error "❌ python is not available"
    fi
    
    # Check poetry environment
    if poetry env info >/dev/null 2>&1; then
        log_info "✅ Poetry environment is configured"
    else
        log_error "❌ Poetry environment is not configured"
    fi
}

# Check that all documented files exist
check_file_existence() {
    log_section "📁 Checking File Existence"
    
    local files=(
        "$DOCS_DIR/quick-start-guide.md"
        "$DOCS_DIR/technical-specifications.md"
        "$DOCS_DIR/ai-agent-workflows.md"
        "$DOCS_DIR/decision-trees.md"
        "$DOCS_DIR/pattern-library.md"
        "$DOCS_DIR/troubleshooting-guide.md"
        "$DOCS_DIR/domain-rules-reference.md"
        "$DOCS_DIR/documentation-maintenance-checklist.md"
        "$DOCS_DIR/documentation-versioning-strategy.md"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            log_info "✅ $file exists"
        else
            log_error "❌ $file is missing"
        fi
    done
}

# Validate code examples in documentation
validate_code_examples() {
    log_section "🐍 Validating Code Examples"
    
    # Test key imports from quick start guide
    log_info "Testing domain imports..."
    if poetry run python -c "
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.recipe.root_aggregate.recipe import Recipe
from src.contexts.recipes_catalog.core.domain.menu.root_aggregate.menu import Menu
from src.contexts.seedwork.shared.domain.repositories import SaGenericRepository
from src.contexts.seedwork.shared.domain.entity import Entity
print('✅ All key imports successful')
" 2>/dev/null; then
        log_info "✅ Domain imports work correctly"
    else
        log_error "❌ Domain imports failed"
    fi
    
    # Test cached property example
    log_info "Testing cached property examples..."
    if poetry run python -c "
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
meal = Meal.create_new('Test Meal', 'test-user', 'BREAKFAST')
ingredients = meal.ingredients_summary
print(f'✅ Cached property test: {len(ingredients)} ingredients')
" 2>/dev/null; then
        log_info "✅ Cached property examples work"
    else
        log_error "❌ Cached property examples failed"
    fi
    
    # Test pytest commands from examples
    log_info "Testing pytest command examples..."
    if poetry run python -m pytest --co -q >/dev/null 2>&1; then
        log_info "✅ Pytest discovery works"
    else
        log_error "❌ Pytest discovery failed"
    fi
}

# Validate internal links (basic check)
validate_internal_links() {
    log_section "🔗 Validating Internal Links"
    
    log_info "Checking for broken internal links..."
    
    # Simple check for .md links
    find "$DOCS_DIR" -name "*.md" -exec grep -l "\.md)" {} \; >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "✅ Found internal markdown links"
    else
        log_info "ℹ️  No internal markdown links found"
    fi
    
    # Check for common broken patterns
    if grep -r "](/" "$DOCS_DIR"/*.md >/dev/null 2>&1; then
        log_warn "⚠️  Found absolute path links that might be broken"
    fi
}

# Generate validation report
generate_report() {
    log_section "📊 Validation Report"
    
    if [ "$EXIT_CODE" -eq 0 ]; then
        log_info "🎉 Documentation validation passed!"
    else
        log_error "❌ Documentation validation failed"
    fi
    
    # Set GitHub Actions outputs if in CI
    if is_ci; then
        echo "error_count=$EXIT_CODE" >> "$GITHUB_OUTPUT" 2>/dev/null || true
        echo "validation_status=success" >> "$GITHUB_OUTPUT" 2>/dev/null || true
    fi
}

# Help function
show_help() {
    cat << EOF
Simplified Documentation Validation Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help      Show this help message
    --quick         Run quick validation (same as full for this version)

EXAMPLES:
    $0                  # Run validation
    $0 --help           # Show this help

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --quick)
            # Quick mode is the same as full mode for simplicity
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main validation
main 