[← Index](./README.md) | [Quick Start](./quick-start-guide.md) | [Workflows](./ai-agent-workflows.md) | [Patterns](./pattern-library.md) | [Troubleshooting](./troubleshooting-guide.md)

---

# 🤖 Using Cursor AI with Menu Planning Backend

*Maximize your productivity with AI-powered development in the menu planning backend*

## 🎯 Quick Start

**Ready to use Cursor AI effectively?** Jump to:
- [5 Ready-to-Use Prompts](#5-ready-to-use-prompts) - Try these immediately
- [Template Library](#template-library) - Copy and customize for your tasks
- [Common Workflows](#common-ai-development-workflows) - Step-by-step guidance

## ⚙️ Optimal Cursor Setup

### Indexing Configuration

#### Files to Always Index
```
# Core documentation (reference often)
docs/architecture/
README.md
pyproject.toml
.markdownlint.yaml
.typos.toml

# Domain models (critical for understanding)
src/contexts/*/core/domain/
src/contexts/seedwork/shared/domain/

# Application services (common modification target)
src/contexts/*/core/services/
src/contexts/*/core/adapters/

# Test patterns (for generating tests)
tests/contexts/*/unit/
tests/contexts/*/integration/
```

#### Files to Exclude from Indexing
```
# Generated/cached files
__pycache__/
.mypy_cache/
.ruff_cache/
.pytest_cache/
.coverage
htmlcov/
.benchmarks/

# Dependencies
.poetry/
poetry.lock
node_modules/

# Large data files
*.csv
event.json
csv

# Migration files (unless working on migrations)
migrations/
alembic/
```

#### Recommended `.cursorignore`
```
__pycache__/
.mypy_cache/
.ruff_cache/
.pytest_cache/
.poetry/
poetry.lock
.coverage
htmlcov/
.benchmarks/
*.csv
event.json
csv
migrations/
debug-env-templates/
.github/
.vscode/
.claude/
```

### Workspace Settings

#### Enable These Features
- ✅ **Code completion** - Essential for domain-driven patterns
- ✅ **Inline suggestions** - Helps with boilerplate reduction  
- ✅ **Documentation reference** - Use `@docs/architecture/` syntax
- ✅ **Multi-file context** - Critical for understanding aggregates
- ✅ **Test generation** - Leverages existing test patterns

#### Cursor Configuration Tips
```json
// In .cursor/settings.json
{
  "cursor.aiModelSelection": "claude-3.5-sonnet", // Best for complex reasoning
  "cursor.chat.includeDocumentation": true,
  "cursor.autocomplete.maxContextLines": 1000,
  "cursor.chat.maxContextLines": 10000
}
```

## 🎨 Effective Prompting Patterns

### Domain-Driven Development Patterns

#### Pattern 1: Aggregate Understanding
```
Analyze the @src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py aggregate. Explain:
1. What business invariants it maintains
2. Which methods modify state vs calculate values
3. How it uses the base Entity caching system
4. What domain events it could raise

Include specific code examples from the file.
```

#### Pattern 2: Command Handler Implementation
```
I need to create a new command handler for [SPECIFIC_COMMAND]. Looking at the existing pattern in @src/contexts/recipes_catalog/core/services/meal/command_handlers/, create a handler that:

1. Follows the established dependency injection pattern
2. Uses the repository and unit of work correctly
3. Handles the domain logic in the aggregate
4. Includes proper error handling

Base it on the existing AddRecipeToMealHandler pattern but for [YOUR_SPECIFIC_USE_CASE].
```

#### Pattern 3: Repository Pattern Extensions
```
Looking at @src/contexts/recipes_catalog/core/adapters/repositories/, I want to add a new method to find meals by [CRITERIA]. 

Create the method following the established patterns:
- Add to the abstract repository interface
- Implement in the concrete repository
- Use proper caching if applicable
- Include type hints matching the existing style

Show both the interface addition and implementation.
```

### Testing Patterns

#### Pattern 4: Test Generation
```
Generate comprehensive tests for @src/contexts/[CONTEXT]/core/domain/[ENTITY]/[entity].py following the patterns in @tests/contexts/[CONTEXT]/unit/.

Include:
1. Creation and validation tests
2. Business rule violation tests  
3. Caching behavior tests (if applicable)
4. Edge cases based on domain rules

Use the same testing style and naming conventions as existing tests.
```

#### Pattern 5: Performance Test Creation
```
Create performance tests for @src/contexts/[CONTEXT] following the pattern in @tests/performance_*.py.

Focus on:
1. Caching effectiveness
2. Repository query efficiency  
3. Memory usage patterns
4. Aggregate loading performance

Include benchmarks and thresholds based on existing performance tests.
```

## 🚀 5 Ready-to-Use Prompts

Copy these prompts and customize the bracketed sections for immediate productivity:

### 1. Add New Property to Aggregate
```
I want to add a new property "[PROPERTY_NAME]" of type "[TYPE]" to the @src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py aggregate.

Looking at existing patterns in the file:
1. Add the property to the dataclass with proper typing
2. Update the create_meal factory method to accept it
3. Add validation if needed (following existing validation patterns)
4. Add a cached_property if it's calculated
5. Update the __post_init__ method if necessary

Show the complete modified class with proper type hints and validation.
```

### 2. Create Repository Query Method
```
Looking at @src/contexts/recipes_catalog/core/adapters/repositories/, add a new method "find_[ENTITY]_by_[CRITERIA]" that:

1. Follows the abstract repository interface pattern
2. Implements caching using the established caching strategy
3. Uses proper SQLAlchemy querying (based on existing patterns)
4. Returns the correct domain objects
5. Handles not-found cases appropriately

Show both the interface definition and concrete implementation.
```

### 3. Generate Test Suite for New Feature
```
Generate comprehensive tests for the new [FEATURE_NAME] functionality in @src/contexts/[CONTEXT]/core/domain/[ENTITY]/.

Following the test patterns in @tests/contexts/[CONTEXT]/unit/:
1. Test creation and validation
2. Test business rule enforcement
3. Test edge cases and error conditions
4. Test caching behavior (if applicable)
5. Test integration with other aggregates

Use the same pytest fixtures and assertion patterns as existing tests.
```

### 4. Create Command Handler
```
Create a new command handler for "[COMMAND_NAME]" in @src/contexts/[CONTEXT]/core/services/[ENTITY]/command_handlers/.

Following the established pattern in existing handlers:
1. Create the command dataclass in domain/commands/
2. Implement the handler with proper dependency injection
3. Use repository and unit of work patterns correctly
4. Handle domain logic through the aggregate
5. Include proper error handling and logging

Show the complete implementation with proper typing and error handling.
```

### 5. Explain Domain Rules Implementation
```
Analyze @src/contexts/[CONTEXT]/core/domain/rules.py and @docs/architecture/domain-rules-reference.md to explain how [SPECIFIC_BUSINESS_RULE] is implemented.

Show:
1. Where the rule is defined and enforced
2. Which aggregates are involved
3. How validation errors are handled
4. Test cases that verify the rule
5. Any performance considerations

Include specific code examples and references to the documentation.
```

## 📋 Template Library

### Domain Model Template
```
Create a new [ENTITY_NAME] aggregate in @src/contexts/[CONTEXT]/core/domain/[entity]/ following the meal aggregate pattern:

Structure needed:
- root_aggregate/[entity].py - Main aggregate
- value_objects/[relevant_vos].py - Any value objects
- commands/[entity]_commands.py - Command definitions
- events/[entity]_events.py - Domain events (if any)

Follow these patterns from @src/contexts/recipes_catalog/core/domain/meal/:
1. Inherit from Entity base class
2. Use dataclass with frozen=True
3. Implement factory methods for creation
4. Add business invariant validation
5. Use cached_property for calculated values
6. Proper typing throughout
```

### Test Template
```
Generate tests for [COMPONENT] following the structure in @tests/contexts/[CONTEXT]/:

Required test files:
- unit/test_[component].py - Domain logic tests
- integration/test_[component]_repository.py - Repository tests
- e2e/test_[component]_handlers.py - End-to-end tests

Use these fixtures and patterns from existing tests:
1. pytest fixtures for object creation
2. Parametrized tests for multiple scenarios
3. Mock external dependencies appropriately
4. Test both success and failure cases
5. Verify caching behavior where applicable
```

### Command Handler Template
```
Implement [COMMAND_NAME] handler in @src/contexts/[CONTEXT]/core/services/[entity]/command_handlers/:

Components needed:
1. Command definition in domain/commands/
2. Handler implementation with dependency injection  
3. Repository interface method (if new query needed)
4. Unit of work integration
5. Error handling and validation

Follow the pattern established in existing handlers, particularly error handling and logging.
```

## 🔄 Common AI Development Workflows

### Workflow 1: Understanding Existing Code
```
1. Ask: "Analyze @[FILE_PATH] and explain its purpose, key patterns, and dependencies"
2. Follow up: "Show me how this integrates with @[RELATED_FILE]"
3. Deep dive: "Explain the business logic in [SPECIFIC_METHOD] and why it's implemented this way"
4. Context: "How does this relate to the overall architecture in @docs/architecture/technical-specifications.md?"
```

### Workflow 2: Implementing New Features
```
1. Planning: "Based on @docs/architecture/domain-rules-reference.md, how should I implement [FEATURE]?"
2. Design: "Create the aggregate design for [FEATURE] following patterns in @src/contexts/recipes_catalog/core/domain/"
3. Implementation: "Implement the [COMPONENT] following the established pattern in @[SIMILAR_COMPONENT]"
4. Testing: "Generate tests following @tests/contexts/[CONTEXT]/unit/ patterns"
5. Integration: "Show how to wire this into the existing dependency injection in @src/contexts/[CONTEXT]/core/bootstrap/"
```

### Workflow 3: Debugging and Optimization
```
1. Analysis: "Analyze the performance issue in @[FILE] - what could be causing slowness?"
2. Profiling: "Based on @tests/performance_*.py patterns, create performance tests for [COMPONENT]"
3. Optimization: "Suggest optimizations for [METHOD] while maintaining the existing caching patterns"
4. Validation: "Create tests to verify the optimization doesn't break existing functionality"
```

### Workflow 4: Refactoring
```
1. Assessment: "Analyze @[COMPONENT] for potential improvements while maintaining existing behavior"
2. Planning: "Create a refactoring plan that follows the patterns in @docs/architecture/pattern-library.md"
3. Implementation: "Refactor [METHOD] to improve [ASPECT] while maintaining backward compatibility"
4. Verification: "Update tests in @tests/contexts/[CONTEXT]/ to verify refactoring correctness"
```

## 🎓 Advanced Techniques

### Multi-File Context Prompts
```
Looking at these related files:
- @src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py
- @src/contexts/recipes_catalog/core/services/meal/command_handlers/add_recipe_to_meal_handler.py  
- @tests/contexts/recipes_catalog/unit/test_meal.py

Explain how adding a recipe to a meal works from command to aggregate to test verification. Include the complete flow with error handling.
```

### Documentation-Driven Development
```
Based on the specifications in @docs/architecture/technical-specifications.md section [X], implement the [FEATURE] with:

1. Domain model changes needed
2. Command/query definitions  
3. Handler implementations
4. Repository interface updates
5. Complete test coverage

Ensure the implementation matches the documented API contract exactly.
```

### Pattern-Based Generation
```
Using the pattern established in @src/contexts/recipes_catalog/core/domain/meal/ as a template, create a complete [NEW_ENTITY] aggregate for the [CONTEXT] context.

Include all components:
- Aggregate root with business logic
- Value objects used by the aggregate  
- Commands for state changes
- Repository interface
- Basic test suite

Follow the exact same structural patterns and naming conventions.
```

## 🔧 Integration with Development Tools

### Pre-commit Integration
```
# Use Cursor to fix pre-commit issues
When pre-commit fails, paste the error and ask:

"The pre-commit hook failed with this error: [ERROR_MESSAGE]. Looking at @.pre-commit-config.yaml and the affected files, fix the issues while maintaining code quality."
```

### Testing Integration
```
# Generate test commands
"Based on @pyproject.toml and the testing patterns in @tests/, what's the correct command to run [SPECIFIC_TEST_TYPE] for the changes I made to @[FILE]?"

# Debug test failures  
"This test is failing: [TEST_NAME]. Looking at @tests/[TEST_FILE] and @src/[SOURCE_FILE], explain why and provide a fix."
```

### Database Integration
```
# Migration assistance
"Looking at @alembic.ini and existing migrations in @migrations/, help me create a migration for [DATABASE_CHANGE] following the established patterns."

# Repository debugging
"The repository query in @src/contexts/[CONTEXT]/core/adapters/repositories/ is slow. Based on the existing caching patterns, suggest optimizations."
```

## 🚨 Troubleshooting Cursor AI Issues

### Common Problems and Solutions

#### Problem: Cursor not understanding domain patterns
```
Solution: Include more context files in your prompt:
- @src/contexts/seedwork/shared/domain/entity.py (base patterns)
- @docs/architecture/pattern-library.md (established patterns)  
- @tests/contexts/[CONTEXT]/unit/ (test examples)
```

#### Problem: Generated code doesn't follow project style
```
Solution: Reference style guides explicitly:
- @pyproject.toml (tool configurations)
- @.markdownlint.yaml (documentation style)
- Existing files in the same directory for patterns
```

#### Problem: AI suggests incorrect dependencies
```
Solution: Always reference the existing dependency injection:
- @src/contexts/[CONTEXT]/core/bootstrap/ (DI setup)
- @pyproject.toml (available packages)
- Existing similar components for patterns
```

#### Problem: Cursor generates inefficient database queries
```
Solution: Point to existing efficient patterns:
- @src/contexts/*/core/adapters/repositories/ (query patterns)
- @tests/performance_*.py (performance expectations)
- Caching strategies already implemented
```

### Getting Better Results

#### Include Specific Context
```
❌ Bad: "Create a meal entity"
✅ Good: "Create a meal entity following the aggregate pattern in @src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py"

❌ Bad: "Write tests for this"  
✅ Good: "Write tests following the pattern in @tests/contexts/recipes_catalog/unit/test_meal.py for the new functionality"

❌ Bad: "Fix the repository"
✅ Good: "Fix the repository query to follow the caching pattern in @src/contexts/recipes_catalog/core/adapters/repositories/ and match the interface in the abstract base"
```

#### Use Documentation References
```
# Always reference relevant docs
- @docs/architecture/technical-specifications.md for API contracts
- @docs/architecture/domain-rules-reference.md for business rules
- @docs/architecture/pattern-library.md for implementation patterns
- @docs/architecture/troubleshooting-guide.md for debugging approaches
```

#### Leverage Existing Patterns
```
# Point to existing implementations
- Use "@src/contexts/recipes_catalog/" for domain-driven patterns
- Use "@tests/contexts/recipes_catalog/" for testing patterns  
- Use "@src/contexts/seedwork/" for base class patterns
- Use existing command handlers for application service patterns
```

### Performance Tips

#### Optimize Context Size
- **Focus**: Include 3-5 most relevant files rather than everything
- **Prioritize**: Domain models > Tests > Documentation > Implementation details
- **Exclude**: Generated files, dependencies, unrelated contexts

#### Batch Related Changes
```
# Instead of multiple prompts, combine related changes:
"Looking at @src/contexts/[CONTEXT]/ and @tests/contexts/[CONTEXT]/, I need to:
1. Add property X to the aggregate
2. Update the repository interface  
3. Generate tests for the new functionality
4. Update the command handler to use the new property

Show all changes needed across these files."
```

## 🎯 Success Metrics

### Measure Your Cursor AI Effectiveness

#### Development Speed Indicators
- ✅ Can generate 80%+ correct code on first try
- ✅ Reduces boilerplate writing by 60%+
- ✅ Correctly follows project patterns without correction
- ✅ Generates comprehensive tests matching existing style

#### Code Quality Indicators  
- ✅ Generated code passes all pre-commit hooks
- ✅ Tests have proper coverage and edge cases
- ✅ Follows domain-driven design principles correctly
- ✅ Maintains performance characteristics of existing code

#### Learning Curve Indicators
- ✅ Prompts become more specific and effective over time
- ✅ Less iteration needed to get desired results
- ✅ Can explain complex domain logic accurately
- ✅ Suggests architectural improvements aligned with project patterns

## 🔗 Related Resources

- **[Quick Start Guide](./quick-start-guide.md)** - Essential commands and navigation
- **[AI Agent Workflows](./ai-agent-workflows.md)** - Step-by-step development processes  
- **[Pattern Library](./pattern-library.md)** - Common implementation patterns
- **[Technical Specifications](./technical-specifications.md)** - API contracts and domain models
- **[Troubleshooting Guide](./troubleshooting-guide.md)** - Common issues and solutions

---

## 📝 Related Documents

### Core Documentation
- **[Documentation Index](./README.md)** - Overview of all documentation
- **[Quick Start Guide](./quick-start-guide.md)** - Get productive in 15 minutes
- **[AI Agent Workflows](./ai-agent-workflows.md)** - Development workflow guidance

### Development Resources  
- **[Pattern Library](./pattern-library.md)** - Implementation patterns and examples
- **[Technical Specifications](./technical-specifications.md)** - API contracts and system design
- **[Decision Trees](./decision-trees.md)** - Architectural decision guidance

### Operational Resources
- **[Troubleshooting Guide](./troubleshooting-guide.md)** - Common issues and solutions
- **[Documentation Maintenance](./documentation-maintenance-checklist.md)** - Keep docs current

---

**Last Updated**: Created during documentation enhancement phase  
**Next Review**: After Cursor AI usage feedback collection 