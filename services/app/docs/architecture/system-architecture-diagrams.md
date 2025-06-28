# System Architecture Diagrams

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web App]
        MOBILE[Mobile App]
        API_CLIENT[API Clients]
    end
    
    subgraph "AWS Cloud"
        subgraph "API Gateway"
            APIGW[AWS API Gateway]
        end
        
        subgraph "Compute Layer - Lambda Functions"
            subgraph "Recipes Catalog"
                MEAL_LAMBDA[Meal Handlers]
                RECIPE_LAMBDA[Recipe Handlers]
                MENU_LAMBDA[Menu Handlers]
                CLIENT_LAMBDA[Client Handlers]
            end
            
            subgraph "Products Catalog"
                PRODUCT_LAMBDA[Product Handlers]
                CLASS_LAMBDA[Classification Handlers]
            end
            
            subgraph "IAM"
                USER_LAMBDA[User Handlers]
                AUTH_LAMBDA[Auth Handlers]
            end
        end
        
        subgraph "Data Layer"
            RDS[(RDS PostgreSQL)]
            S3[S3 Bucket - Images]
        end
        
        subgraph "Auth"
            COGNITO[AWS Cognito]
        end
    end
    
    WEB --> APIGW
    MOBILE --> APIGW
    API_CLIENT --> APIGW
    
    APIGW --> COGNITO
    
    APIGW --> MEAL_LAMBDA
    APIGW --> RECIPE_LAMBDA
    APIGW --> MENU_LAMBDA
    APIGW --> CLIENT_LAMBDA
    APIGW --> PRODUCT_LAMBDA
    APIGW --> CLASS_LAMBDA
    APIGW --> USER_LAMBDA
    APIGW --> AUTH_LAMBDA
    
    MEAL_LAMBDA --> RDS
    RECIPE_LAMBDA --> RDS
    MENU_LAMBDA --> RDS
    CLIENT_LAMBDA --> RDS
    PRODUCT_LAMBDA --> RDS
    CLASS_LAMBDA --> RDS
    USER_LAMBDA --> RDS
    
    MEAL_LAMBDA --> S3
    RECIPE_LAMBDA --> S3
```

## Domain Model - Bounded Contexts

```mermaid
graph TB
    subgraph "Recipes Catalog Context"
        MEAL[Meal Aggregate]
        RECIPE[Recipe Entity]
        MENU[Menu Aggregate]
        CLIENT[Client Aggregate]
        
        MEAL -->|contains| RECIPE
        CLIENT -->|has many| MENU
        MENU -->|references| MEAL
    end
    
    subgraph "Products Catalog Context"
        PRODUCT[Product Aggregate]
        BRAND[Brand Entity]
        CATEGORY[Category Entity]
        SOURCE[Source Entity]
        
        PRODUCT -->|classified by| BRAND
        PRODUCT -->|classified by| CATEGORY
        PRODUCT -->|from| SOURCE
    end
    
    subgraph "IAM Context"
        USER[User Aggregate]
        ROLE[Role Value Object]
        
        USER -->|has| ROLE
    end
    
    subgraph "Shared Kernel"
        NUTRI[NutriFacts VO]
        TAG[Tag VO]
        ADDR[Address VO]
        
        MEAL -.->|uses| NUTRI
        RECIPE -.->|uses| NUTRI
        PRODUCT -.->|uses| NUTRI
        MEAL -.->|uses| TAG
        RECIPE -.->|uses| TAG
        MENU -.->|uses| TAG
    end
    
    RECIPE -.->|references| PRODUCT
    MEAL -.->|authored by| USER
    MENU -.->|authored by| USER
```

## Aggregate Boundaries - Meal and Recipe

```mermaid
graph TB
    subgraph "Meal Aggregate Root"
        MEAL_ROOT[Meal<br/>- id: UUID<br/>- name: str<br/>- author_id: UUID<br/>- menu_id: UUID<br/>- version: int]
        
        subgraph "Public API"
            CREATE_RECIPE[create_recipe()]
            UPDATE_RECIPES[update_recipes()]
            DELETE_RECIPE[delete_recipe()]
            COPY_RECIPE[copy_recipe()]
        end
        
        subgraph "Cached Properties"
            NUTRI_FACTS[nutri_facts<br/>@cached_property]
            MACRO_DIV[macro_division<br/>@cached_property]
            TOTAL_WEIGHT[total_weight<br/>@cached_property]
        end
    end
    
    subgraph "Recipe Entity"
        RECIPE_ENTITY[Recipe<br/>- id: UUID<br/>- meal_id: UUID<br/>- name: str<br/>- instructions: str<br/>- nutri_facts: NutriFacts]
        
        subgraph "Protected Setters"
            SET_NAME[_set_name()]
            SET_INSTRUCT[_set_instructions()]
            SET_NUTRI[_set_nutri_facts()]
        end
        
        subgraph "Direct Actions"
            RATE[rate()]
            DELETE_RATE[delete_rate()]
        end
    end
    
    MEAL_ROOT --> CREATE_RECIPE
    MEAL_ROOT --> UPDATE_RECIPES
    MEAL_ROOT --> DELETE_RECIPE
    MEAL_ROOT --> COPY_RECIPE
    
    CREATE_RECIPE -->|creates| RECIPE_ENTITY
    UPDATE_RECIPES -->|calls| SET_NAME
    UPDATE_RECIPES -->|calls| SET_INSTRUCT
    UPDATE_RECIPES -->|calls| SET_NUTRI
    
    UPDATE_RECIPES -->|invalidates| NUTRI_FACTS
    UPDATE_RECIPES -->|invalidates| MACRO_DIV
    UPDATE_RECIPES -->|invalidates| TOTAL_WEIGHT
```

## Layered Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        LAMBDA[AWS Lambda Handlers]
        API[API Gateway]
    end
    
    subgraph "Application Layer"
        CMD_HANDLER[Command Handlers]
        EVT_HANDLER[Event Handlers]
        QUERY_HANDLER[Query Handlers]
        MSGBUS[Message Bus]
    end
    
    subgraph "Domain Layer"
        AGG[Aggregates]
        ENTITY[Entities]
        VO[Value Objects]
        DOMAIN_SVC[Domain Services]
        DOMAIN_EVT[Domain Events]
    end
    
    subgraph "Infrastructure Layer"
        REPO[Repositories]
        UOW[Unit of Work]
        ORM[SQLAlchemy ORM]
        DB[Database]
    end
    
    API --> LAMBDA
    LAMBDA --> CMD_HANDLER
    LAMBDA --> QUERY_HANDLER
    
    CMD_HANDLER --> MSGBUS
    MSGBUS --> AGG
    MSGBUS --> EVT_HANDLER
    
    AGG --> ENTITY
    AGG --> VO
    AGG --> DOMAIN_EVT
    
    CMD_HANDLER --> UOW
    UOW --> REPO
    REPO --> ORM
    ORM --> DB
    
    EVT_HANDLER --> UOW
    QUERY_HANDLER --> REPO
```

## Command Flow - Create Meal Example

```mermaid
sequenceDiagram
    participant Client
    participant Lambda
    participant CommandHandler
    participant UoW
    participant Meal
    participant Repository
    participant EventBus
    participant Database
    
    Client->>Lambda: POST /meals
    Lambda->>Lambda: Validate JWT
    Lambda->>Lambda: Parse request body
    Lambda->>CommandHandler: handle(CreateMeal)
    
    CommandHandler->>UoW: async with uow
    activate UoW
    
    CommandHandler->>Meal: Meal.create_meal()
    activate Meal
    Meal->>Meal: Validate business rules
    Meal->>Meal: Create Recipe entities
    Meal->>Meal: Calculate nutri_facts
    Meal-->>CommandHandler: Return Meal instance
    deactivate Meal
    
    CommandHandler->>Repository: uow.meals.add(meal)
    Repository->>Database: INSERT meal, recipes
    
    CommandHandler->>UoW: await uow.commit()
    UoW->>EventBus: Publish domain events
    UoW->>Database: COMMIT transaction
    deactivate UoW
    
    CommandHandler-->>Lambda: Return meal_id
    Lambda-->>Client: 201 Created
```

## Event-Driven Architecture

```mermaid
graph LR
    subgraph "Meal Context"
        MEAL_AGG[Meal Aggregate]
        MEAL_EVENTS[MealCreated<br/>RecipeUpdated<br/>MealDeleted]
    end
    
    subgraph "Menu Context"
        MENU_AGG[Menu Aggregate]
        MENU_HANDLER[Menu Event Handler]
    end
    
    subgraph "Event Bus"
        EVENT_QUEUE[Domain Event Queue]
    end
    
    subgraph "Projections"
        NUTRITION_PROJ[Nutrition Summary]
        MENU_PROJ[Menu Calendar]
    end
    
    MEAL_AGG -->|emits| MEAL_EVENTS
    MEAL_EVENTS --> EVENT_QUEUE
    
    EVENT_QUEUE --> MENU_HANDLER
    MENU_HANDLER -->|updates| MENU_AGG
    
    EVENT_QUEUE --> NUTRITION_PROJ
    EVENT_QUEUE --> MENU_PROJ
```

## Caching Strategy

```mermaid
graph TB
    subgraph "Entity Instance"
        ENTITY[Entity Base Class]
        CACHED_ATTRS[_cached_attrs: set]
        
        subgraph "Cached Properties"
            PROP1[@cached_property<br/>nutri_facts]
            PROP2[@cached_property<br/>macro_division]
            PROP3[@cached_property<br/>average_rating]
        end
        
        subgraph "Cache Management"
            INVALIDATE[_invalidate_caches()]
            CHECK_CACHE[Check if cached]
            COMPUTE[Compute value]
            STORE[Store in cache]
        end
    end
    
    subgraph "Mutation Flow"
        MUTATE[Mutation method]
        UPDATE_STATE[Update state]
        INCREMENT_VER[_increment_version()]
        CLEAR_CACHE[Clear affected caches]
    end
    
    ENTITY --> CACHED_ATTRS
    ENTITY --> PROP1
    ENTITY --> PROP2
    ENTITY --> PROP3
    
    PROP1 --> CHECK_CACHE
    CHECK_CACHE -->|miss| COMPUTE
    COMPUTE --> STORE
    CHECK_CACHE -->|hit| RETURN[Return cached value]
    
    MUTATE --> UPDATE_STATE
    UPDATE_STATE --> INCREMENT_VER
    INCREMENT_VER --> CLEAR_CACHE
    CLEAR_CACHE --> INVALIDATE
```

## Repository Pattern with Async/Await

```mermaid
sequenceDiagram
    participant Handler
    participant UoW
    participant Repository
    participant Session
    participant Database
    
    Handler->>UoW: async with UnitOfWork()
    activate UoW
    UoW->>Session: Create async session
    UoW->>Repository: Initialize repositories
    
    Handler->>Repository: await repo.get(id)
    activate Repository
    Repository->>Session: await session.execute(query)
    Session->>Database: SELECT * FROM table
    Database-->>Session: Result rows
    Session-->>Repository: SQLAlchemy result
    Repository->>Repository: Map to domain model
    Repository-->>Handler: Domain entity
    deactivate Repository
    
    Handler->>Handler: Modify entity
    
    Handler->>Repository: await repo.update(entity)
    Repository->>Session: session.add(mapped_entity)
    
    Handler->>UoW: await uow.commit()
    UoW->>Session: await session.commit()
    Session->>Database: COMMIT
    UoW->>UoW: Publish events
    deactivate UoW
```

## Database Schema Overview

```mermaid
erDiagram
    MEALS {
        uuid id PK
        string name
        uuid author_id FK
        uuid menu_id FK
        text description
        text notes
        boolean discarded
        int version
        timestamp created_at
        timestamp updated_at
    }
    
    RECIPES {
        uuid id PK
        uuid meal_id FK
        string name
        text instructions
        jsonb nutri_facts
        int servings
        int prep_time_minutes
        int cook_time_minutes
        uuid author_id FK
        boolean discarded
        int version
    }
    
    INGREDIENTS {
        uuid id PK
        uuid recipe_id FK
        uuid product_id FK
        decimal amount
        string unit
        string preparation
        int position
    }
    
    MENUS {
        uuid id PK
        uuid author_id FK
        uuid client_id FK
        text description
        boolean discarded
        int version
    }
    
    MENU_MEALS {
        uuid id PK
        uuid menu_id FK
        uuid meal_id FK
        int week
        string weekday
        string meal_type
        string meal_name
        jsonb nutri_facts
    }
    
    PRODUCTS {
        uuid id PK
        string name
        uuid brand_id FK
        uuid source_id FK
        jsonb nutri_facts_per_100g
        string barcode
        text ingredients_text
        jsonb allergens
    }
    
    MEALS ||--o{ RECIPES : contains
    RECIPES ||--o{ INGREDIENTS : has
    INGREDIENTS }o--|| PRODUCTS : uses
    MENUS ||--o{ MENU_MEALS : contains
    MENU_MEALS }o--|| MEALS : references
```

## Testing Strategy

```mermaid
graph TB
    subgraph "Test Pyramid"
        UNIT[Unit Tests<br/>Domain Logic]
        INTEGRATION[Integration Tests<br/>Repositories, Services]
        E2E[E2E Tests<br/>Lambda Handlers]
    end
    
    subgraph "Test Focus Areas"
        BEHAVIOR[Behavior Tests<br/>What it does]
        CACHE[Cache Tests<br/>Performance & Invalidation]
        BOUNDARY[Boundary Tests<br/>Edge cases]
        PERF[Performance Tests<br/>Benchmarks]
    end
    
    subgraph "Test Patterns"
        FACTORIES[Test Factories<br/>create_meal()]
        FIXTURES[Fixtures<br/>Database state]
        MOCKS[Mocks<br/>External services]
        PARAMS[Parametrized<br/>Multiple scenarios]
    end
    
    UNIT --> BEHAVIOR
    UNIT --> CACHE
    UNIT --> BOUNDARY
    
    INTEGRATION --> FIXTURES
    INTEGRATION --> FACTORIES
    
    E2E --> MOCKS
    
    BOUNDARY --> PARAMS
    PERF --> CACHE
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "CI/CD Pipeline"
        GIT[Git Push]
        CI[GitHub Actions]
        TEST[Run Tests]
        BUILD[Build Lambda]
        DEPLOY[Deploy]
    end
    
    subgraph "AWS Infrastructure"
        subgraph "Production"
            PROD_LAMBDA[Lambda Functions]
            PROD_RDS[RDS PostgreSQL]
            PROD_S3[S3 Bucket]
        end
        
        subgraph "Staging"
            STAGE_LAMBDA[Lambda Functions]
            STAGE_RDS[RDS PostgreSQL]
            STAGE_S3[S3 Bucket]
        end
    end
    
    GIT --> CI
    CI --> TEST
    TEST -->|pass| BUILD
    BUILD --> DEPLOY
    
    DEPLOY -->|staging| STAGE_LAMBDA
    DEPLOY -->|production| PROD_LAMBDA
```

## Security Architecture

```mermaid
graph TB
    subgraph "External"
        CLIENT[Client Application]
    end
    
    subgraph "AWS API Gateway"
        APIGW[API Gateway]
        AUTH[Authorizer]
    end
    
    subgraph "AWS Cognito"
        COGNITO[User Pool]
        TOKENS[JWT Tokens]
    end
    
    subgraph "Lambda Function"
        HANDLER[Handler]
        VALIDATE[Validate Claims]
        AUTHORIZE[Check Permissions]
    end
    
    subgraph "Domain Layer"
        DOMAIN[Domain Logic]
        RULES[Business Rules]
    end
    
    CLIENT -->|1. Request + Token| APIGW
    APIGW -->|2. Validate| AUTH
    AUTH -->|3. Check| COGNITO
    COGNITO -->|4. Claims| AUTH
    AUTH -->|5. Authorized| HANDLER
    
    HANDLER -->|6. Extract user_id| VALIDATE
    VALIDATE -->|7. Check role| AUTHORIZE
    AUTHORIZE -->|8. Execute| DOMAIN
    DOMAIN -->|9. Enforce| RULES
```

These diagrams provide a comprehensive visual representation of the system architecture, making it easier for AI agents to understand the structure, relationships, and flow of the application.