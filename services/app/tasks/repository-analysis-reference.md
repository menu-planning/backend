# Repository Pattern Refactoring - Technical Analysis Reference

**Document Purpose**: This document contains comprehensive technical analysis of the existing repository implementation, serving as a reference for refactoring efforts and future development.

**Created**: Phase 0 of repository refactoring tasks  
**Status**: Complete analysis of all model relationships, filter operators, and join scenarios

---

## Table of Contents
- [Model Relationship Analysis](#model-relationship-analysis)
- [FilterColumnMapper Configurations](#filtercolumnmapper-configurations)
- [Filter Operators and Postfix Logic](#filter-operators-and-postfix-logic)
- [Join Scenarios and Paths](#join-scenarios-and-paths)
- [Association Tables Structure](#association-tables-structure)
- [Visual Relationship Diagrams](#visual-relationship-diagrams)
- [Mock Model Requirements](#mock-model-requirements)

---

## Model Relationship Analysis

### MealSaModel Relationships
**Table**: `recipes_catalog.meals`

**Direct Columns** (20+ fields):
- `id` (PK), `name`, `preprocessed_name`, `description`
- `author_id` (indexed), `menu_id` (FK to menus), `notes`, `total_time` (indexed)
- `weight_in_grams` (indexed), `like` (indexed)
- Nutrition percentages: `calorie_density`, `carbo_percentage`, `protein_percentage`, `total_fat_percentage`
- Timestamps: `created_at` (indexed), `updated_at`
- Versioning: `discarded`, `version`

**Complex Relationships**:
1. **recipes**: One-to-many with `RecipeSaModel`
   - Relationship: `MealSaModel.recipes`
   - Lazy loading: `selectin`
   - Cascade: `save-update, merge`

2. **tags**: Many-to-many with `TagSaModel`
   - Via: `meals_tags_association` table
   - Lazy loading: `selectin`
   - Cascade: `save-update, merge`

3. **nutri_facts**: Composite field with `NutriFactsSaModel`
   - 72+ individual nutrition columns
   - 8 key nutrients indexed: calories, protein, carbohydrate, total_fat, saturated_fat, trans_fat, sugar, salt

4. **menu_id**: Foreign key to `MenuSaModel`
   - Many-to-one relationship
   - Optional (nullable)

### RecipeSaModel Relationships
**Table**: `recipes_catalog.recipes`

**Direct Columns** (25+ fields):
- `id` (PK), `name`, `preprocessed_name`, `description`, `instructions`
- `author_id` (indexed), `meal_id` (FK to meals), `utensils`, `total_time` (indexed)
- `notes`, `privacy`, `weight_in_grams` (indexed)
- Nutrition percentages: `calorie_density`, `carbo_percentage`, `protein_percentage`, `total_fat_percentage`
- `image_url`, `average_taste_rating` (indexed), `average_convenience_rating` (indexed)
- Timestamps: `created_at` (indexed), `updated_at`
- Versioning: `discarded`, `version`

**Complex Relationships**:
1. **ingredients**: One-to-many with `IngredientSaModel`
   - Relationship: `RecipeSaModel.ingredients`
   - Lazy loading: `selectin`
   - Ordering: `IngredientSaModel.position`
   - Cascade: `all, delete-orphan`

2. **tags**: Many-to-many with `TagSaModel`
   - Via: `recipes_tags_association` table
   - Lazy loading: `selectin`
   - Cascade: `save-update, merge`

3. **ratings**: One-to-many with `RatingSaModel`
   - Relationship: `RecipeSaModel.ratings`
   - Lazy loading: `selectin`
   - Ordering: `RatingSaModel.created_at`
   - Cascade: `all, delete-orphan`

4. **nutri_facts**: Composite field with `NutriFactsSaModel`
   - Same 72+ nutrition columns as MealSaModel
   - Same indexing on 8 key nutrients

5. **meal_id**: Foreign key to `MealSaModel`
   - Many-to-one relationship
   - Required (not nullable)

### Supporting Model Relationships

#### IngredientSaModel
**Table**: `recipes_catalog.ingredients`
- **Primary Key**: Composite (`name`, `recipe_id`)
- **Foreign Key**: `recipe_id` → `recipes.id`
- **Columns**: `name`, `preprocessed_name`, `quantity`, `unit`, `position`, `full_text`, `product_id`, `created_at`
- **Indexes**: GIN trigram on `preprocessed_name`, `product_id`

#### RatingSaModel
**Table**: `recipes_catalog.ratings`
- **Primary Key**: Composite (`user_id`, `recipe_id`)
- **Foreign Key**: `recipe_id` → `recipes.id`
- **Columns**: `user_id`, `recipe_id`, `taste`, `convenience`, `comment`, `created_at`
- **Indexes**: `taste`, `convenience`, `created_at`

#### TagSaModel
**Table**: `shared_kernel.tags`
- **Primary Key**: `id` (auto-increment)
- **Columns**: `id`, `key`, `value`, `author_id`, `type`
- **Unique Constraint**: `(key, value, author_id, type)`
- **Indexes**: 
  - `(key, value, author_id, type)` - unique
  - `(author_id, type)` - for filtering

#### NutriFactsSaModel (Composite)
**72+ Nutrition Fields** (all nullable float):
- **Core**: calories, protein, carbohydrate, total_fat, saturated_fat, trans_fat, dietary_fiber, sodium, sugar
- **Fatty Acids**: arachidonic_acid, dha, epa, linolenic_acid, linoleic_acid, oleic_acid, omega_7, omega_9
- **Vitamins**: vitamin_a through vitamin_k, vitamin_b1-b12, folic_acid, biotin, choline
- **Minerals**: calcium, iron, magnesium, phosphorus, potassium, zinc, selenium, copper, chrome, etc.
- **Carbohydrates**: starch, fructose, glucose, galactose, lactose, maltose, sucrose
- **Others**: caffeine, cholesterol, taurine, l_carnitine, guarana, inositol, etc.

---

## FilterColumnMapper Configurations

### MealRepo Filter Mappers
```python
filter_to_column_mappers = [
    # Level 0: Direct MealSaModel columns
    FilterColumnMapper(
        sa_model_type=MealSaModel,
        filter_key_to_column_name={
            "id": "id", "name": "name", "menu_id": "menu_id", "author_id": "author_id",
            "total_time": "total_time", "weight_in_grams": "weight_in_grams",
            "created_at": "created_at", "updated_at": "updated_at", "like": "like",
            # Nutrition fields (from composite nutri_facts)
            "calories": "calories", "protein": "protein", "carbohydrate": "carbohydrate",
            "total_fat": "total_fat", "saturated_fat": "saturated_fat", "trans_fat": "trans_fat",
            "sugar": "sugar", "sodium": "sodium",
            # Calculated percentages
            "calorie_density": "calorie_density", "carbo_percentage": "carbo_percentage",
            "protein_percentage": "protein_percentage", "total_fat_percentage": "total_fat_percentage",
        },
    ),
    # Level 1: Join to RecipeSaModel
    FilterColumnMapper(
        sa_model_type=RecipeSaModel,
        filter_key_to_column_name={
            "recipe_id": "id",
            "recipe_name": "name",
        },
        join_target_and_on_clause=[(RecipeSaModel, MealSaModel.recipes)],
    ),
    # Level 2: Join through Recipe to IngredientSaModel
    FilterColumnMapper(
        sa_model_type=IngredientSaModel,
        filter_key_to_column_name={"products": "product_id"},
        join_target_and_on_clause=[
            (RecipeSaModel, MealSaModel.recipes),
            (IngredientSaModel, RecipeSaModel.ingredients),
        ],
    ),
]
```

### RecipeRepo Filter Mappers
```python
filter_to_column_mappers = [
    # Level 0: Direct RecipeSaModel columns
    FilterColumnMapper(
        sa_model_type=RecipeSaModel,
        filter_key_to_column_name={
            "id": "id", "name": "name", "meal_id": "meal_id", "author_id": "author_id",
            "total_time": "total_time", "weight_in_grams": "weight_in_grams", "privacy": "privacy",
            "created_at": "created_at", "average_taste_rating": "average_taste_rating",
            "average_convenience_rating": "average_convenience_rating",
            # Nutrition fields (from composite nutri_facts)
            "calories": "calories", "protein": "protein", "carbohydrate": "carbohydrate",
            "total_fat": "total_fat", "saturated_fat": "saturated_fat", "trans_fat": "trans_fat",
            "sugar": "sugar", "sodium": "sodium",
            # Calculated percentages
            "calorie_density": "calorie_density", "carbo_percentage": "carbo_percentage",
            "protein_percentage": "protein_percentage", "total_fat_percentage": "total_fat_percentage",
        },
    ),
    # Level 1: Join to IngredientSaModel
    FilterColumnMapper(
        sa_model_type=IngredientSaModel,
        filter_key_to_column_name={"products": "product_id"},
        join_target_and_on_clause=[(IngredientSaModel, RecipeSaModel.ingredients)],
    ),
]
```

### Critical Configuration Points
1. **Order Matters**: Mappers are processed in exact order provided
2. **Join Chains**: Multi-level joins must specify complete path
3. **Column Mapping**: Filter keys map to actual SA model column names
4. **Composite Field Access**: Nutrition fields access individual columns from composite

---

## Filter Operators and Postfix Logic

### ALLOWED_POSTFIX (Exact Processing Order)
```python
ALLOWED_POSTFIX = ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]
```

### Operator Selection Algorithm
```python
def _filter_operator_selection(filter_name, filter_value, sa_model_type):
    # 1. Check postfix in exact order
    if "_gte" in filter_name:
        return operators.ge
    if "_lte" in filter_name:
        return operators.le
    if "_ne" in filter_name:
        return operators.ne
    if "_not_in" in filter_name:
        return lambda c, v: (c == None) | (~c.in_(v))  # NULL-inclusive NOT IN
    if "_is_not" in filter_name:
        return operators.is_not
    
    # 2. Check value type
    if isinstance(filter_value, (list, set)):
        return lambda c, v: c.in_(v)
    
    # 3. Check column type
    if column_type == bool:
        return lambda c, v: c.is_(v)
    if column_type == list:
        return lambda c, v: c.contains(v)
    
    # 4. Default fallback
    return operators.eq
```

### Operator Behaviors

#### Comparison Operators
- **`_gte`**: `WHERE column >= value` (Greater than or equal)
- **`_lte`**: `WHERE column <= value` (Less than or equal)
- **`_ne`**: `WHERE column != value` (Not equal)

#### Complex Operators
- **`_not_in`**: `WHERE (column IS NULL OR column NOT IN (values))`
  - **Critical**: Includes NULL values in results
  - **Handles empty lists**: No filtering applied
- **`_is_not`**: `WHERE column IS NOT value`
  - **Primary use**: `IS NOT NULL` checks

#### Value-Based Operators
- **List values**: `WHERE column IN (value1, value2, ...)`
- **Boolean values**: `WHERE column IS value`
- **String values**: `WHERE column = value`

#### Special Cases
- **`_not_exists`**: Currently falls back to default behavior
- **Empty lists**: `_not_in` with empty list returns all rows
- **NULL values**: Special handling in `_not_in` and `_is_not`

### Postfix Removal Logic
```python
def remove_postfix(filter_name):
    for postfix in ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]:
        if filter_name.endswith(postfix):
            return filter_name[:-len(postfix)]
    return filter_name
```

**Critical Behavior**: Only removes the **first matching** postfix, not all occurrences.

---

## Join Scenarios and Paths

### Direct Relationships (No Joins)
- **MealSaModel**: All direct columns (20+ fields)
- **RecipeSaModel**: All direct columns (25+ fields)

### Single-Level Joins
1. **Meal → Recipe**: `MealSaModel.recipes` relationship
2. **Recipe → Ingredient**: `RecipeSaModel.ingredients` relationship
3. **Recipe → Rating**: `RecipeSaModel.ratings` relationship
4. **Meal → Tag**: Via `meals_tags_association` table
5. **Recipe → Tag**: Via `recipes_tags_association` table

### Multi-Level Join Chains
1. **Meal → Recipe → Ingredient**: For filtering meals by ingredient properties
   - **Path**: `MealSaModel.recipes → RecipeSaModel.ingredients`
   - **Use Case**: Find meals containing specific products
   - **Filter Key**: `products` (maps to `IngredientSaModel.product_id`)

2. **Meal → Recipe → Rating**: For filtering meals by recipe ratings
   - **Path**: `MealSaModel.recipes → RecipeSaModel.ratings`
   - **Use Case**: Find meals with highly-rated recipes

3. **Meal → Recipe → Tag**: For filtering meals by recipe tags
   - **Path**: `MealSaModel.recipes → recipes_tags_association`
   - **Use Case**: Find meals containing recipes with specific tags

### Join Dependency Rules
1. **Order Matters**: Recipe must be joined before Ingredient in MealRepo
2. **Duplicate Detection**: `already_joined` set tracks completed joins
3. **Relationship Mapping**: Joins use SQLAlchemy relationship attributes
4. **Performance**: Minimizes unnecessary joins through tracking

---

## Association Tables Structure

### meals_tags_association
```sql
CREATE TABLE recipes_catalog.meals_tags_association (
    meal_id VARCHAR REFERENCES recipes_catalog.meals(id),
    tag_id INTEGER REFERENCES shared_kernel.tags(id),
    PRIMARY KEY (meal_id, tag_id)
);
```

### recipes_tags_association
```sql
CREATE TABLE recipes_catalog.recipes_tags_association (
    recipe_id VARCHAR REFERENCES recipes_catalog.recipes(id),
    tag_id INTEGER REFERENCES shared_kernel.tags(id),
    PRIMARY KEY (recipe_id, tag_id)
);
```

### Association Table Characteristics
- **Composite Primary Keys**: Prevent duplicate associations
- **Cross-Schema References**: Link recipes_catalog to shared_kernel
- **No Additional Columns**: Pure many-to-many associations
- **Cascade Behavior**: Defined in relationship, not table level

---

## Visual Relationship Diagrams

### Core Entity Relationship Diagram
```
┌─────────────────┐    1:N    ┌─────────────────┐    1:N    ┌─────────────────┐
│   MealSaModel   │──────────▶│  RecipeSaModel  │──────────▶│ IngredientSaModel│
│                 │           │                 │           │                 │
│ • id (PK)       │           │ • id (PK)       │           │ • name (PK)     │
│ • name          │           │ • meal_id (FK)  │           │ • recipe_id (FK)│
│ • author_id     │           │ • author_id     │           │ • product_id    │
│ • menu_id (FK)  │           │ • nutri_facts   │           │ • quantity      │
│ • nutri_facts   │           │ • privacy       │           │ • unit          │
│ • total_time    │           │ • total_time    │           │ • position      │
│ • like          │           │ • discarded     │           └─────────────────┘
│ • discarded     │           │ • discarded     │
└─────────────────┘           └─────────────────┘
         │                             │
         │ M:N                         │ M:N                   ┌─────────────────┐
         │                             │                       │  RatingSaModel  │
         ▼                             ▼                       │                 │
┌─────────────────┐           ┌─────────────────┐     1:N     │ • user_id (PK)  │
│ meals_tags_     │           │recipes_tags_    │◀────────────│ • recipe_id (FK)│
│ association     │           │association      │             │ • taste         │
│                 │           │                 │             │ • convenience   │
│ • meal_id (FK)  │           │ • recipe_id(FK) │             │ • comment       │
│ • tag_id (FK)   │           │ • tag_id (FK)   │             │ • created_at    │
└─────────────────┘           └─────────────────┘             └─────────────────┘
         │                             │
         │ M:N                         │ M:N
         ▼                             ▼
┌─────────────────────────────────────────────────────┐
│                TagSaModel                           │
│                                                     │
│ • id (PK - auto increment)                          │
│ • key (e.g., "cuisine", "diet")                     │
│ • value (e.g., "italian", "vegetarian")            │
│ • author_id (scoped to user)                        │
│ • type ("meal" or "recipe")                         │
│                                                     │
│ UNIQUE(key, value, author_id, type)                 │
└─────────────────────────────────────────────────────┘
```

### Composite Field Breakdown (nutri_facts)
```
┌─────────────────────────────────────────────────────────────┐
│                 NutriFactsSaModel (Composite)               │
│                                                             │
│ Core Nutrients:          Vitamins:              Minerals:   │
│ • calories              • vitamin_a            • calcium    │
│ • protein               • vitamin_c            • iron       │
│ • carbohydrate          • vitamin_d            • sodium     │
│ • total_fat             • vitamin_e            • potassium  │
│ • saturated_fat         • vitamin_k            • magnesium  │
│ • trans_fat             • vitamin_b1-b12       • zinc       │
│ • dietary_fiber         • folic_acid           • selenium   │
│ • sugar                 • biotin               • copper     │
│                                                             │
│ 72+ individual float columns created automatically          │
│ 8 key nutrients are indexed for performance                 │
└─────────────────────────────────────────────────────────────┘
```

### FilterColumnMapper Join Paths
```
MealRepo Filter Paths:
│
├─ Level 0 (Direct): MealSaModel.*
│  └─ All meal columns (name, author_id, nutrition, etc.)
│
├─ Level 1 (1 Join): MealSaModel → RecipeSaModel
│  └─ recipe_id, recipe_name
│
└─ Level 2 (2 Joins): MealSaModel → RecipeSaModel → IngredientSaModel
   └─ products (via product_id)

RecipeRepo Filter Paths:
│
├─ Level 0 (Direct): RecipeSaModel.*
│  └─ All recipe columns (name, meal_id, nutrition, ratings, etc.)
│
└─ Level 1 (1 Join): RecipeSaModel → IngredientSaModel
   └─ products (via product_id)
```

---

## Mock Model Requirements

### Essential Mock Components
1. **MockMealSaModel**: Replicate all relationships and 20+ columns
2. **MockRecipeSaModel**: Replicate all relationships and 25+ columns
3. **MockIngredientSaModel**: Composite PK and position ordering
4. **MockRatingSaModel**: Composite PK and rating logic
5. **MockTagSaModel**: Unique constraint and type discrimination
6. **MockNutriFactsSaModel**: 72+ individual columns as composite
7. **Mock Association Tables**: SQLAlchemy Table objects

### Critical Mock Requirements
- **Relationship Complexity**: Same lazy loading, cascades, ordering
- **Composite Fields**: Individual columns for nutri_facts composite
- **Association Tables**: Proper many-to-many through tables
- **Foreign Keys**: Maintain referential integrity
- **Indexes**: Mock key indexes for realistic testing 
- **Column Types**: Match data types (str, int, float, bool, datetime)

### Mock Validation Criteria
- **No Database Dependencies**: Use in-memory or mock database
- **Identical Behavior**: Same query results as real models
- **Complete Coverage**: Support all FilterColumnMapper scenarios
- **Edge Case Handling**: NULL values, empty relationships, etc.
- **Performance Testing**: Support large dataset scenarios

---

## Key Insights for Refactoring

### Complexity Hotspots
1. **Tag Filtering**: Complex groupby logic with AND/OR combinations
2. **Multi-level Joins**: 3+ table joins with dependency chains
3. **Composite Fields**: 72+ individual columns from single field
4. **NULL Handling**: Special logic for `_not_in` operations
5. **Postfix Logic**: Order-dependent operator selection

### Backward Compatibility Requirements
- **Exact Method Signatures**: No changes to existing interfaces
- **Identical Query Results**: Same SQL generation behavior
- **Preserved Edge Cases**: All current workarounds must continue
- **Performance Maintenance**: No degradation in query performance
- **Error Handling**: Same exception types and messages

### Refactoring Risks
- **Join Order Changes**: Could alter query performance
- **Operator Precedence**: Changing postfix order breaks existing behavior
- **NULL Logic**: `_not_in` behavior is non-standard but required
- **Composite Field Access**: Individual column access must be preserved
- **Association Handling**: Many-to-many logic is complex and fragile

---

**Document Status**: Complete Phase 0 Analysis  
**Last Updated**: Repository Refactoring Phase 0  
**Next Phase**: Begin Phase 3 Refactoring with comprehensive test coverage 