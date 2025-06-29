#!/bin/bash

# Pre-commit Documentation Style Check Script
# Validates documentation formatting and style guidelines

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo -e "${BLUE}[DOCS-STYLE]${NC} $1"
}

# Style guidelines validation
validate_style_guidelines() {
    local file="$1"
    local filename=$(basename "$file")
    
    log_section "📝 Checking style: $filename"
    
    # Check file structure and formatting
    check_file_structure "$file"
    check_heading_structure "$file"
    check_code_block_formatting "$file"
    check_link_formatting "$file"
    check_list_formatting "$file"
    check_table_formatting "$file"
}

# Check file structure requirements
check_file_structure() {
    local file="$1"
    
    # Check for required sections in architecture docs
    if [[ "$file" == *"/docs/architecture/"* ]]; then
        # Should have a purpose/overview section
        if ! grep -q "## 🎯 Purpose\|## Overview\|## 📋 Overview" "$file"; then
            log_warn "⚠️  Missing purpose/overview section in $(basename "$file")"
        fi
        
        # Should have proper emoji usage for sections
        if ! grep -q "^## [🎯📋🔍💡⚡🔧📊🚀📝🔄]" "$file"; then
            log_warn "⚠️  Consider using emojis for section headers in $(basename "$file")"
        fi
    fi
    
    # Check for proper front matter or title
    if ! head -10 "$file" | grep -q "^# \|^## \|---"; then
        log_warn "⚠️  Missing title or header in $(basename "$file")"
    fi
}

# Check heading structure
check_heading_structure() {
    local file="$1"
    
    # Check heading hierarchy
    local prev_level=0
    local line_num=0
    
    while IFS= read -r line; do
        ((line_num++))
        
        # Count heading levels
        if [[ "$line" =~ ^(#+)[[:space:]] ]]; then
            local current_level=${#BASH_REMATCH[1]}
            
            # Skip if it's the first heading
            if [ $prev_level -eq 0 ]; then
                prev_level=$current_level
                continue
            fi
            
            # Check for proper hierarchy (no skipping levels)
            if [ $current_level -gt $((prev_level + 1)) ]; then
                log_warn "⚠️  Heading hierarchy skip in $(basename "$file"):$line_num (h$prev_level -> h$current_level)"
            fi
            
            prev_level=$current_level
        fi
    done < "$file"
    
    # Check for space after # in headings
    if grep -n '^#[^# ]' "$file" >/dev/null; then
        log_error "❌ Missing space after # in headings in $(basename "$file")"
        grep -n '^#[^# ]' "$file" | head -3
    fi
}

# Check code block formatting
check_code_block_formatting() {
    local file="$1"
    
    # Check for properly closed code blocks
    local in_code_block=false
    local line_num=0
    local code_block_start=0
    
    while IFS= read -r line; do
        ((line_num++))
        
        if [[ "$line" =~ ^\`\`\` ]]; then
            if [ "$in_code_block" = false ]; then
                in_code_block=true
                code_block_start=$line_num
            else
                in_code_block=false
            fi
        fi
    done < "$file"
    
    if [ "$in_code_block" = true ]; then
        log_error "❌ Unclosed code block starting at line $code_block_start in $(basename "$file")"
    fi
    
    # Check for language specification in code blocks
    if grep -n '^```$' "$file" >/dev/null; then
        log_warn "⚠️  Code blocks without language specification in $(basename "$file")"
        grep -n '^```$' "$file" | head -3
    fi
    
    # Check for inline code formatting consistency
    if grep -n '`[^`]*`[a-zA-Z]' "$file" >/dev/null; then
        log_warn "⚠️  Inline code might need spacing in $(basename "$file")"
    fi
}

# Check link formatting
check_link_formatting() {
    local file="$1"
    
    # Check for proper link formatting
    # Look for malformed links
    if grep -n '\](' "$file" | grep -v 'http\|\.md\|\.py\|\.sh\|\.yaml\|\.yml\|\.json' >/dev/null; then
        log_warn "⚠️  Potentially malformed links in $(basename "$file")"
        grep -n '\](' "$file" | grep -v 'http\|\.md\|\.py\|\.sh\|\.yaml\|\.yml\|\.json' | head -3
    fi
    
    # Check for consistent link formatting in documentation
    if grep -n '\[.*\](\.\./\.\./\.\.)' "$file" >/dev/null; then
        log_warn "⚠️  Deep relative links found - consider using absolute paths in $(basename "$file")"
    fi
}

# Check list formatting
check_list_formatting() {
    local file="$1"
    
    # Check for consistent list formatting
    local has_dash_lists=$(grep -c '^[[:space:]]*-[[:space:]]' "$file" || true)
    local has_star_lists=$(grep -c '^[[:space:]]*\*[[:space:]]' "$file" || true)
    
    if [ "$has_dash_lists" -gt 0 ] && [ "$has_star_lists" -gt 0 ]; then
        log_warn "⚠️  Mixed list markers (- and *) in $(basename "$file")"
    fi
    
    # Check for proper spacing in lists
    if grep -n '^[[:space:]]*[-*][[:space:]]\{2,\}' "$file" >/dev/null; then
        log_warn "⚠️  Extra spaces in list items in $(basename "$file")"
    fi
    
    # Check for missing space after list markers
    if grep -n '^[[:space:]]*[-*][^[:space:]]' "$file" >/dev/null; then
        log_error "❌ Missing space after list marker in $(basename "$file")"
        grep -n '^[[:space:]]*[-*][^[:space:]]' "$file" | head -3
    fi
}

# Check table formatting
check_table_formatting() {
    local file="$1"
    
    # Check for table formatting consistency
    if grep -q '|' "$file"; then
        # Check for proper table header separators
        local in_table=false
        local prev_line=""
        local line_num=0
        
        while IFS= read -r line; do
            ((line_num++))
            
            if [[ "$line" =~ \| ]]; then
                if [ "$in_table" = false ]; then
                    in_table=true
                    prev_line="$line"
                    continue
                fi
                
                # Check if this looks like a header separator
                if [[ "$line" =~ ^[[:space:]]*\|[[:space:]]*:?-+:?[[:space:]]*\| ]]; then
                    # This is a valid separator
                    in_table=true
                elif [ "$in_table" = true ] && [ -n "$prev_line" ]; then
                    # Check column count consistency
                    local prev_cols=$(echo "$prev_line" | tr -cd '|' | wc -c)
                    local curr_cols=$(echo "$line" | tr -cd '|' | wc -c)
                    
                    if [ "$prev_cols" -ne "$curr_cols" ]; then
                        log_warn "⚠️  Table column count mismatch in $(basename "$file"):$line_num"
                    fi
                fi
                
                prev_line="$line"
            else
                in_table=false
            fi
        done < "$file"
    fi
}

# Check for AI agent onboarding specific style guidelines
check_ai_agent_style() {
    local file="$1"
    
    # Check for proper use of action items and checklists
    if grep -q '\- \[ \]' "$file"; then
        log_info "✅ Contains interactive checklists in $(basename "$file")"
        
        # Check for proper checkbox formatting
        if grep -n '\-\[ \]\|\-\[x\]' "$file" >/dev/null; then
            log_warn "⚠️  Missing space in checkbox formatting in $(basename "$file")"
        fi
    fi
    
    # Check for code examples with proper context
    if grep -q '```' "$file"; then
        # Look for code examples without explanation
        local prev_line=""
        local in_code=false
        local line_num=0
        
        while IFS= read -r line; do
            ((line_num++))
            
            if [[ "$line" =~ ^\`\`\` ]]; then
                if [ "$in_code" = false ]; then
                    # Starting code block
                    if [ -z "$prev_line" ] || [[ ! "$prev_line" =~ [.:]$ ]]; then
                        log_warn "⚠️  Code block without context at line $line_num in $(basename "$file")"
                    fi
                    in_code=true
                else
                    in_code=false
                fi
            fi
            
            if [ "$in_code" = false ]; then
                prev_line="$line"
            fi
        done < "$file"
    fi
}

# Main function
main() {
    log_section "🎨 Pre-commit Documentation Style Check"
    
    # Process all staged markdown files
    local files_checked=0
    
    if [ $# -eq 0 ]; then
        # No files passed, check all staged markdown files
        git diff --cached --name-only | grep '\.md$' | while read -r file; do
            if [ -f "$file" ]; then
                validate_style_guidelines "$file"
                check_ai_agent_style "$file"
                ((files_checked++))
            fi
        done
    else
        # Files passed as arguments
        for file in "$@"; do
            if [ -f "$file" ] && [[ "$file" == *.md ]]; then
                validate_style_guidelines "$file"
                check_ai_agent_style "$file"
                ((files_checked++))
            fi
        done
    fi
    
    if [ $files_checked -eq 0 ]; then
        log_info "ℹ️  No markdown files to check"
    fi
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_info "✅ Documentation style check passed"
    else
        log_error "❌ Documentation style check failed"
        echo ""
        echo "💡 Style fix suggestions:"
        echo "   • Ensure proper heading hierarchy (no level skipping)"
        echo "   • Add space after # in headings"
        echo "   • Close all code blocks properly"
        echo "   • Use consistent list markers"
        echo "   • Provide context for code examples"
    fi
    
    exit $EXIT_CODE
}

# Run main function
main "$@" 