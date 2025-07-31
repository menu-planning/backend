# MessageBus Command/Query Pattern Analysis

## Overview
Analysis of MessageBus usage patterns across all contexts to understand command/query handling variations and identify opportunities for standardization.

## MessageBus Architecture

### Shared Infrastructure
All contexts use the same MessageBus implementation:
```python
# src/contexts/shared_kernel/services/messagebus.MessageBus
class MessageBus(Generic[U]):
    def __init__(self, uow, event_handlers, command_handlers):
        self.uow = uow
        self.event_handlers = event_handlers  
        self.command_handlers = command_handlers
    
    async def handle(self, message: Event | Command):
        # Dispatches to appropriate handlers
```

### Context-Specific Bootstrap
Each context registers its own handlers:

#### Products Catalog Bootstrap
```python
# src/contexts/products_catalog/core/bootstrap/bootstrap.py
def bootstrap(uow: UnitOfWork) -> MessageBus:
    injected_command_handlers = {
        commands.AddFoodProduct: partial(cmd_handlers.add_food_product, uow=uow),
        commands.CreateSource: partial(cmd_handlers.create_source, uow=uow),
        commands.CreateProcessType: partial(cmd_handlers.create_process_type, uow=uow),
        # ... more product commands
    }
    return MessageBus(uow=uow, event_handlers={}, command_handlers=injected_command_handlers)
```

#### Recipes Catalog Bootstrap
```python
# src/contexts/recipes_catalog/core/bootstrap/bootstrap.py  
def bootstrap(uow: UnitOfWork) -> MessageBus:
    injected_command_handlers = {
        # Recipe commands
        meal_commands.CreateRecipe: partial(meal_cmd_handlers.create_recipe_handler, uow=uow),
        meal_commands.UpdateRecipe: partial(meal_cmd_handlers.update_recipe_handler, uow=uow),
        # Meal commands  
        meal_commands.CreateMeal: partial(meal_cmd_handlers.create_meal_handler, uow=uow),
        # Client commands
        client_commands.CreateClient: partial(client_cmd_handlers.create_client_handler, uow=uow),
        # ... more recipe/meal/client commands
    }
    return MessageBus(uow=uow, event_handlers={}, command_handlers=injected_command_handlers)
```

#### IAM Context Bootstrap
```python
# src/contexts/iam/core/bootstrap/bootstrap.py
def bootstrap(uow: UnitOfWork) -> MessageBus:
    injected_command_handlers = {
        commands.CreateUser: partial(cmd_handlers.create_user, uow=uow),
        commands.AssignRoleToUser: partial(cmd_handlers.assign_role_to_user, uow=uow),
        commands.RemoveRoleFromUser: partial(cmd_handlers.remove_role_from_user, uow=uow),
    }
    return MessageBus(uow=uow, event_handlers={}, command_handlers=injected_command_handlers)
```

## Usage Patterns in Endpoints

### Container Bootstrap Pattern
All endpoints follow the same bootstrap pattern:
```python
# Common across all contexts
bus: MessageBus = Container().bootstrap()
```

### Command Handling Pattern
Write operations use the command pattern:
```python
# Example: Create Recipe
api = ApiCreateRecipe(**body)
cmd = api.to_domain()  # Convert API schema to domain command
bus: MessageBus = container.bootstrap()
await bus.handle(cmd)  # Execute command through MessageBus
```

### Query Handling Pattern
Read operations use direct UnitOfWork access:
```python
# Example: Get Recipe by ID
bus: MessageBus = container.bootstrap()
uow: UnitOfWork
async with bus.uow as uow:
    recipe = await uow.recipes.get(recipe_id)
```

### Collection Query Pattern
List/search operations use repository queries:
```python
# Example: Fetch Recipes
bus: MessageBus = Container().bootstrap()  
uow: UnitOfWork
async with bus.uow as uow:
    result = await uow.recipes.query(filter=filters)
```

## Command Pattern Analysis

### Command Creation Workflow
1. **API Schema Validation**: `ApiCreateRecipe(**body)`
2. **Domain Conversion**: `api.to_domain()` 
3. **Command Execution**: `await bus.handle(cmd)`
4. **Response Building**: Manual JSON response construction

### Command Examples by Context

#### Products Catalog Commands
- `AddFoodProduct` - Create products (bulk operation)
- `CreateSource` - Create classification sources
- `CreateProcessType` - Create process types

#### Recipes Catalog Commands  
- **Recipe Commands**: CreateRecipe, UpdateRecipe, DeleteRecipe, CopyRecipe
- **Meal Commands**: CreateMeal, UpdateMeal, DeleteMeal, CopyMeal
- **Client Commands**: CreateClient, UpdateClient, DeleteClient
- **Menu Commands**: CreateMenu, UpdateMenu, DeleteMenu

#### IAM Commands
- `CreateUser` - User creation (Cognito trigger)
- `AssignRoleToUser` - Role assignment
- `RemoveRoleFromUser` - Role removal

### Command Handler Registration
All contexts use partial function injection:
```python
commands.CreateRecipe: partial(cmd_handlers.create_recipe_handler, uow=uow)
```

## Query Pattern Analysis

### Direct Repository Access
Most queries bypass command pattern:
```python
# Get single entity
entity = await uow.entities.get(entity_id)

# Query with filters  
results = await uow.entities.query(filter=filters)

# Custom repository methods
results = await uow.products.list_top_similar_names(name)
```

### UnitOfWork Usage Patterns

#### Explicit UoW Management (Recipes/Products)
```python
bus: MessageBus = container.bootstrap()
uow: UnitOfWork
async with bus.uow as uow:
    # Repository operations
```

#### Command-Only UoW (IAM)
```python
# IAM endpoints often skip explicit UoW for queries
bus: MessageBus = Container().bootstrap()
await bus.handle(cmd)  # UoW managed inside command handler
```

### Query Response Patterns

#### Pydantic Model Serialization
```python
api = ApiRecipe.from_domain(recipe)
return {"statusCode": 200, "body": api.model_dump_json()}
```

#### Manual JSON Serialization
```python
return {
    "statusCode": 200,
    "body": json.dumps([ApiProduct.from_domain(i).model_dump() for i in result])
}
```

#### Custom Serialization
```python
return {
    "statusCode": 200, 
    "body": json.dumps(results, default=custom_serializer)
}
```

## Container and Dependency Injection

### Container Pattern Variations

#### Module-Level Container (Some endpoints)
```python
container = Container()  # Module level

@lambda_exception_handler
async def async_handler(event, context):
    bus: MessageBus = container.bootstrap()
```

#### Inline Container (Most endpoints)
```python
@lambda_exception_handler  
async def async_handler(event, context):
    bus: MessageBus = Container().bootstrap()
```

### Dependency Injection Consistency
- **UnitOfWork**: Injected via partial functions in all command handlers
- **Container**: Provides UoW factory and bootstrap method
- **MessageBus**: Created fresh per request (no singleton pattern)

## Event Handling Patterns

### Event Handler Registration
Most contexts have minimal event handling:
```python
# IAM has one event handler
injected_event_handlers = {
    events.UserCreated: [partial(evt_handlers.publish_send_admin_new_user_notification)]
}

# Other contexts typically have empty event handlers
injected_event_handlers = {}
```

### Event Processing
- **Async Task Groups**: Events processed concurrently
- **Exception Handling**: Failed events logged but don't fail command
- **Timeout Management**: Configurable timeout for event processing

## Performance and Error Handling

### Command Execution Flow
1. **Validation**: API schema validation before command creation
2. **Timeout**: Configurable timeout for command execution
3. **Exception Extraction**: Custom exception handling for FastAPI compatibility
4. **Event Publishing**: Post-command event processing
5. **UoW Management**: Automatic transaction management

### Error Patterns
```python
# Standard exception handling in MessageBus
try:
    async with anyio.create_task_group() as tg:
        tg.start_soon(self._completed, handler, command)
except* Exception as exc:
    self._extract_exception_that_has_fastapi_custom_handler(exc)
```

## Identified Inconsistencies

### Query vs Command Approach
- **Write Operations**: Consistently use command pattern
- **Read Operations**: Mix of direct repository access and potential query objects
- **Complex Queries**: No standardized query object pattern

### Container Usage
- **Initialization**: Mix of module-level vs inline container creation
- **Bootstrap Calls**: Repeated `Container().bootstrap()` without reuse
- **Dependency Management**: No request-scoped container pattern

### Response Handling
- **Serialization**: Multiple approaches (Pydantic, manual JSON, custom serializers)
- **Status Codes**: Inconsistent success codes (200 vs 201)
- **Error Responses**: No standardized command error handling

### UnitOfWork Patterns
- **Explicit Management**: Recipes/Products use explicit `async with bus.uow`
- **Implicit Management**: IAM relies on command handler UoW management
- **Query Optimization**: No evidence of read-only UoW optimizations

## Standardization Opportunities

### Unified Query Pattern
```python
# Proposed: Query objects for complex reads
class GetRecipeQuery:
    recipe_id: str

class FetchRecipesQuery:
    filters: dict
    limit: int
    sort: str
```

### Request-Scoped Container
```python
# Proposed: Container per request lifecycle
@endpoint_decorator
async def handler(event, context, container: Container):
    bus = container.message_bus  # Pre-configured
```

### Response Standardization
```python
# Proposed: Consistent response builders  
return success_response(data=api.model_dump_json(), status_code=200)
return error_response(message="Not found", status_code=404)
```

## Migration Strategy

### Phase 1: Container Standardization
- Implement request-scoped container pattern
- Reduce bootstrap boilerplate
- Add container-based dependency injection

### Phase 2: Query Object Pattern
- Introduce query objects for complex reads
- Maintain backward compatibility with direct repository access
- Add query validation and logging

### Phase 3: Response Standardization  
- Implement unified response builders
- Standardize serialization approach
- Add consistent error handling

## Success Metrics
- **Boilerplate Reduction**: Eliminate 100+ lines of repeated bootstrap code
- **Query Consistency**: Unified approach for read operations
- **Response Standardization**: Consistent JSON serialization across contexts
- **Error Handling**: Centralized command/query error management 