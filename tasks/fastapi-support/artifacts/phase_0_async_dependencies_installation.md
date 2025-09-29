# Phase 0.2.1: FastAPI and Async Dependencies Installation Report

## Task: Install FastAPI and async dependencies
**Files modified**: `pyproject.toml`
**Purpose**: Add FastAPI, asyncpg, httpx, anyio dependencies

## Implementation Summary

### 1. Clean Dependency Separation (Option 1 - Recommended)

#### 1.1 Main Project File
**File**: `pyproject.toml`
**Purpose**: Core dependencies + AWS Lambda deployment

```toml
dependencies = [
    # Core application dependencies (shared by AWS Lambda and FastAPI)
    "dependency-injector>=4.41.0",
    "attrs>=25.1.0",
    "python-dotenv>=1.0.0",
    "python-multipart>=0.0.9",
    "Unidecode>=1.3.8",
    "asyncpg>=0.29.0",        # ✅ Async PostgreSQL driver
    "yarl>=1.9.4",
    "anyio>=4.0.0",          # ✅ Async concurrency library
    "colorlog>=6.8.0",
    "sqlalchemy>=2.0.25",    # ✅ Async SQLAlchemy
    "pydantic>=2.5.2",
    "pydantic-settings>=2.1.0",
    "python-json-logger>=3.2.1",
    "email-validator>=2.2.0",
    "greenlet>=3.1.1,<4.0.0", # ✅ Required for async SQLAlchemy
    "structlog>=25.4.0,<26.0.0",
    "psutil>=7.0.0,<8.0.0",
]
```

#### 1.2 Railway-Specific File
**File**: `pyproject.railway.toml`
**Purpose**: FastAPI deployment for Railway

```toml
dependencies = [
    # Core application dependencies
    "dependency-injector>=4.41.0",
    "attrs>=25.1.0",
    "python-dotenv>=1.0.0",
    "python-multipart>=0.0.9",
    "Unidecode>=1.3.8",
    "asyncpg>=0.29.0",
    "yarl>=1.9.4",
    "anyio>=4.0.0",
    "colorlog>=6.8.0",
    "sqlalchemy>=2.0.25",
    "pydantic>=2.5.2",
    "pydantic-settings>=2.1.0",
    "python-json-logger>=3.2.1",
    "email-validator>=2.2.0",
    "greenlet>=3.1.1,<4.0.0",
    "structlog>=25.4.0,<26.0.0",
    "psutil>=7.0.0,<8.0.0",
    # FastAPI-specific dependencies
    "fastapi>=0.116.2",      # ✅ FastAPI framework
    "uvicorn>=0.32.1",      # ✅ ASGI server
    "httpx>=0.28.1,<0.29.0", # ✅ Async HTTP client
    "starlette>=0.41.0",    # ✅ FastAPI's underlying framework
]
```

#### 1.3 Railway Configuration
**File**: `railway.json`
**Purpose**: Railway deployment configuration

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "uv sync --group fastapi"
  },
  "deploy": {
    "startCommand": "uvicorn src.runtimes.fastapi.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. Deployment-Specific Usage

#### 2.1 Railway Deployment (FastAPI)
**Railway Behavior**: 
- Automatically detects `pyproject.railway.toml`
- Installs dependencies from that file
- Uses `railway.json` for build and deployment configuration
- Starts FastAPI app with uvicorn

**Local Development**:
```bash
# Install FastAPI dependencies for local development
uv sync --group fastapi-dev

# Run FastAPI app locally
uv run uvicorn src.runtimes.fastapi.main:app --reload
```

#### 2.2 AWS CDK Deployment (Lambda)
**CDK Behavior**:
- Uses main `pyproject.toml`
- Installs core dependencies + AWS-specific groups
- Deploys Lambda functions

**Local Development**:
```bash
# Install AWS dependencies
uv sync --group aws

# Run Lambda functions locally
uv run python tests/local_lambda_server.py
```

#### 2.3 Development Environment
**Command**: `uv sync --group dev`
**Dependencies**: Core + dev tools
**Result**: Development environment with testing tools

### 3. Benefits of This Structure

#### 3.1 Clean Separation
- ✅ **Railway**: Gets exactly FastAPI dependencies it needs
- ✅ **AWS CDK**: Gets exactly Lambda dependencies it needs
- ✅ **Development**: Flexible dependency groups for different scenarios
- ✅ **No duplication**: Each dependency defined once in appropriate file

#### 3.2 Deployment Flexibility
- ✅ **Railway**: Automatic detection of `pyproject.railway.toml`
- ✅ **AWS CDK**: Uses main `pyproject.toml` with AWS groups
- ✅ **Development**: Multiple dependency groups for different needs

#### 3.3 Size Optimization
- ✅ **Smaller deployments**: Only necessary dependencies per platform
- ✅ **Faster builds**: Fewer dependencies to install per platform
- ✅ **Better security**: Minimal attack surface per deployment

### 4. Files Created

- ✅ `pyproject.railway.toml` - Railway-specific dependencies
- ✅ `railway.json` - Railway deployment configuration  
- ✅ `DEPLOYMENT.md` - Deployment documentation
- ✅ Updated `pyproject.toml` - Clean core + AWS dependencies

### 5. Validation Commands

#### 5.1 Core Dependencies Validation
```bash
# Validate core async dependencies
uv run python -c "import asyncpg, anyio, sqlalchemy; print('Core async deps OK')"
```

#### 5.2 FastAPI Dependencies Validation
```bash
# Install FastAPI dependencies
uv sync --group fastapi-dev

# Validate FastAPI dependencies
uv run python -c "import fastapi, uvicorn, httpx; print('FastAPI deps OK')"
```

#### 5.3 AWS Dependencies Validation
```bash
# Install AWS dependencies
uv sync --group aws

# Validate AWS dependencies
uv run python -c "import boto3, mangum; print('AWS deps OK')"
```

## Summary
Successfully implemented clean dependency separation with:
- **Railway**: `pyproject.railway.toml` + `railway.json` → FastAPI deployment
- **AWS CDK**: `pyproject.toml` + dependency groups → Lambda deployment
- **Development**: Flexible dependency groups for different scenarios

This structure provides maximum flexibility for different deployment targets while maintaining clean dependency management and optimal deployment sizes.
