#!/bin/bash
# setenvs.sh - Export environment variables from .env file to current shell
# Usage: source ./scripts/setenvs.sh

# Look for environment file in priority order:
# 1. .env.dev (for FastAPI local development)
# 2. .env (standard environment file)
# 3. env.local (fallback for FastAPI development)

if [[ -f ".env.dev" ]]; then
    ENV_FILE="$(pwd)/.env.dev"
    echo "Loading FastAPI local development environment from .env.dev"
elif [[ -f ".env" ]]; then
    ENV_FILE="$(pwd)/.env"
    echo "Loading environment from .env"
elif [[ -f "env.local" ]]; then
    ENV_FILE="$(pwd)/env.local"
    echo "Loading FastAPI local development environment from env.local"
else
    # Fallback: try to find .env relative to script location
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    if [[ -f "$PROJECT_ROOT/.env.dev" ]]; then
        ENV_FILE="$PROJECT_ROOT/.env.dev"
        echo "Loading FastAPI local development environment from $ENV_FILE"
    elif [[ -f "$PROJECT_ROOT/.env" ]]; then
        ENV_FILE="$PROJECT_ROOT/.env"
        echo "Loading environment from $ENV_FILE"
    elif [[ -f "$PROJECT_ROOT/env.local" ]]; then
        ENV_FILE="$PROJECT_ROOT/env.local"
        echo "Loading FastAPI local development environment from $ENV_FILE"
    else
        ENV_FILE="$PROJECT_ROOT/.env"
    fi
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