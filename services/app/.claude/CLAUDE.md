# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Dependencies and Setup
```bash
# Install all dependencies
poetry install

# Add new dependency
poetry add <package>

# Add development dependency
poetry add --group dev <package>
```

### Testing
```bash
# Run all tests (sets up Docker containers automatically)
python manage.py test

# Run only unit tests
pytest

# Run integration tests
python manage.py test integration
# or
pytest --integration

# Run e2e tests
python manage.py test e2e
# or
pytest --e2e

# Run specific test file or directory
python manage.py test <path>
pytest <path>
```

### Database Management
```bash
# Run all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

### Linting and Type Checking
```bash
# The project uses ruff for linting (check pyproject.toml for configuration)
ruff check .
ruff format .
```

## Architecture Overview

This is a Domain-Driven Design (DDD) microservices application for menu planning. The architecture follows these key patterns:

### Bounded Contexts
- **iam**: Identity and Access Management
- **products_catalog**: Product management with classifications, brands, and sources
- **recipes_catalog**: Recipes, meals, menus, and client management
- **shared_kernel**: Common domain objects (NutriFacts, Tags, Address, etc.)
- **seedwork**: Base classes and shared infrastructure

### Architecture Pattern
Each context follows a hexagonal architecture with these layers:
1. **Domain Layer** (`core/domain/`): Pure business logic, entities, value objects, commands, events
2. **Application Layer** (`core/services/`): Command handlers, event handlers, Unit of Work
3. **Infrastructure Layer** (`core/adapters/`): Repository implementations, ORM mappings, API schemas
4. **Entry Points** (`aws_lambda/`, `endpoints/`): HTTP endpoints and Lambda functions

### Command and Event Flow
1. Commands are dispatched through the MessageBus
2. Command handlers execute business logic using repositories and domain entities
3. Domain entities emit events during state changes
4. Unit of Work commits changes and collects events
5. Events are dispatched to all registered event handlers
6. Cross-context communication happens through events

### Key Patterns
- **Repository Pattern**: Abstract persistence with SQLAlchemy implementation
- **Unit of Work**: Transaction management and event collection
- **Message Bus**: Central command/event routing
- **Value Objects**: Immutable domain concepts
- **Soft Deletes**: Entities use `discarded` flag instead of hard deletes

### Testing Strategy
- **Unit Tests**: Test domain logic in isolation
- **Integration Tests**: Test with real database using Docker
- **E2E Tests**: Test complete workflows including AWS Lambda handlers

The `manage.py test` command automatically:
- Starts PostgreSQL, RabbitMQ, and Mailhog containers
- Runs migrations
- Executes tests
- Cleans up resources

### Cross-Context Communication
Contexts communicate via:
1. **Domain Events**: Asynchronous event-driven communication
2. **Internal API Providers**: Synchronous queries between contexts
3. **Shared Kernel**: Common value objects and types

Never directly import domain models from other contexts.