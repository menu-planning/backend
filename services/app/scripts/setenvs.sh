#!/bin/bash
# setenvs.sh - Export environment variables from .env file to current shell
# Usage: source ./scripts/setenvs.sh

# Look for .env file in the current working directory first
if [[ -f ".env" ]]; then
    ENV_FILE="$(pwd)/.env"
else
    # Fallback: try to find .env relative to script location
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    ENV_FILE="$PROJECT_ROOT/.env"
fi

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: .env file not found at $ENV_FILE" >&2
    return 1 2>/dev/null || exit 1
fi

# Read .env file and export variables
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Check if line contains an equals sign
    if [[ "$line" == *"="* ]]; then
        # Split on first equals sign
        key="${line%%=*}"
        value="${line#*=}"
        
        # Trim whitespace from key
        key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        
        # Skip invalid variable names (must start with letter or underscore, contain only alphanumeric and underscore)
        if [[ ! "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
            echo "Skipping invalid variable name: '$key'"
            continue
        fi
        
        # Remove quotes from value if present
        if [[ "$value" =~ ^\"(.*)\"$ ]] || [[ "$value" =~ ^\'(.*)\'$ ]]; then
            value="${BASH_REMATCH[1]}"
        fi
        
        # Export the variable
        export "$key"="$value"
        echo "Exported: $key"
    fi
done < "$ENV_FILE"

echo "Environment variables from .env have been exported to current shell"