# Deployment Configuration

This project supports multiple deployment targets with clean dependency separation.

## File Structure

- `pyproject.toml` - Main project file (core dependencies + AWS Lambda)
- `pyproject.railway.toml` - Railway-specific dependencies (FastAPI)
- `railway.json` - Railway deployment configuration

## Deployment Targets

### Railway (FastAPI)
**File**: `pyproject.railway.toml`
**Dependencies**: Core + FastAPI-specific
**Configuration**: `railway.json`

Railway will automatically:
1. Detect `pyproject.railway.toml` and install those dependencies
2. Read `railway.json` for deployment configuration
3. Start the FastAPI app with uvicorn

**Local Development**:
```bash
# Install FastAPI dependencies for local development
uv sync --file pyproject.railway.toml

# Run FastAPI app locally
uv run uvicorn src.runtimes.fastapi.main:app --reload
```

### AWS Lambda (CDK)
**File**: `pyproject.toml`
**Dependencies**: Core + AWS-specific
**Configuration**: CDK deployment

**Local Development**:
```bash
# Install AWS dependencies
uv sync --group aws

# Run Lambda functions locally (using local lambda server)
uv run python tests/local_lambda_server.py
```

### Development Environment
**File**: `pyproject.toml`
**Dependencies**: Core + dev tools

```bash
# Install development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

## Dependency Groups

- **Core**: Shared business logic dependencies
- **aws**: AWS Lambda deployment (boto3)
- **dev**: General development tools

## Railway Configuration

The `railway.json` file configures:
- Start command: `uvicorn src.runtimes.fastapi.main:app --host 0.0.0.0 --port $PORT`
- Health check endpoint: `/health`
- Restart policy and timeouts
