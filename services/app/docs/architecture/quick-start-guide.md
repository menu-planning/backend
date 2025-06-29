[← Index](./README.md) | [Quick Start](./quick-start-guide.md) | [Workflows](./ai-agent-workflows.md) | [Patterns](./pattern-library.md) | [Troubleshooting](./troubleshooting-guide.md)

---

# Quick Start Guide - AI Agent Onboarding

## 🚀 First 15 Minutes: Get Productive Fast

Welcome! This guide gets you contributing to the menu planning backend within 15 minutes. Follow this checklist in order.

### ⚡ Immediate Setup (5 minutes)

#### 1. Environment Validation
```bash
# Verify you're in the right directory
pwd
# Should show: /home/jap/projects/menu-planning/backend/services/app

# Check Python and Poetry are available
python --version  # Should be 3.12+
poetry --version   # Should be installed

# Install dependencies if needed
poetry install
```

#### 2. Quick Health Check
```bash
# Run a fast test to verify everything works
poetry run python -c "
import sys
sys.path.append('src')
from contexts.seedwork.shared.domain.entity import Entity
print('✓ Domain layer accessible')
"

# Test database connection
poetry run python manage.py check-db

# Run a small test suite (should complete in <30 seconds)
poetry run python -m pytest tests/contexts/seedwork/shared/domain/test_entity_cache_invalidation.py::TestEntityCacheInvalidation::test_cached_property_actually_caches -v
```

### 🗺️ Project Navigation (5 minutes)

#### Core Directory Structure
```
src/contexts/                    # Domain-driven design contexts
├── recipes_catalog/             # Meals, recipes, menus
├── products_catalog/            # Food products and nutrition data
├── shared_kernel/               # Shared value objects and enums
├── iam/                         # User management
└── seedwork/                    # Base classes and patterns

tests/contexts/                  # Mirror structure of src/
├── unit/                        # Pure domain logic tests
├── integration/                 # Repository and service tests
└── e2e/                         # Lambda handler tests

docs/architecture/               # Architecture documentation
├── quick-start-guide.md         # This file
├── technical-specifications.md  # API contracts and data models
├── system-architecture-diagrams.md # Visual architecture
└── decisions/                   # Architecture Decision Records
```

#### Key Files to Know
| File | Purpose | When to Use |
|------|---------|-------------|
| `src/contexts/seedwork/shared/domain/entity.py` | Base entity with caching | Understanding entity patterns |
| `src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py` | Primary aggregate example | Learning aggregate design |
| `tests/contexts/recipes_catalog/core/domain/meal/root_aggregate/test_meal.py` | Comprehensive test example | Understanding test patterns |
| `docs/architecture/technical-specifications.md` | API contracts | Finding command/query specs |
| `src/contexts/recipes_catalog/core/services/meal/command_handlers/` | Application service layer | Command handling patterns |

### 🛠️ Essential Commands (5 minutes)

#### Development Commands
```bash
# Testing (always use poetry run python -m!)
poetry run python -m pytest                                    # Run all tests
poetry run python -m pytest tests/contexts/recipes_catalog/unit -v    # Unit tests only
poetry run python -m pytest --cov=src --cov-report=term-missing       # With coverage

# Code Quality  
poetry run python -m mypy src/                                 # Type checking
poetry run python -m ruff check .                              # Linting
poetry run python -m black . --check                           # Format checking
poetry run python -m bandit -r src/                            # Security scan

# Database
poetry run python manage.py check-db                        # Test connection
poetry run python alembic upgrade head                      # Run migrations
poetry run python alembic history                           # View migration history

# Quick Exploration
poetry run python manage.py shell                           # Interactive shell
poetry run python scripts/explore_domain.py                 # Domain model explorer
```

#### 🚨 Critical: Always Use `poetry run python -m`
**NEVER use bare commands like `pytest` or `mypy`. Always prefix with `poetry run python -m`**

✅ Correct: `poetry run python -m pytest`  
❌ Wrong: `pytest` or even `poetry run python pytest`

💡 **Quick Reference**: For instant access to commands and patterns, see the [Quick Reference Card](./quick-reference.md)

## 🎯 Quick Wins: Try These Now

### 1. Explore the Domain Model (2 minutes)
```python
# Run this in a Python shell: poetry run python manage.py shell
from contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

# Create a simple meal (this won't persist, just explore)
meal = Meal.create_meal(
    name="Test Meal",
    author_id="test-author",
    recipes=[]
)

print(f"Created meal: {meal.name}")
print(f"Meal ID: {meal.id}")
print(f"Version: {meal.version}")
print(f"Created at: {meal.created_at}")
```

### 2. Run a Focused Test (1 minute)
```bash
# Test the caching behavior (core feature)
poetry run python -m pytest tests/contexts/seedwork/shared/domain/test_entity_cache_invalidation.py::TestEntityCacheInvalidation::test_cached_property_actually_caches -v
```

### 3. Examine Architecture Patterns (2 minutes)
```bash
# Look at entity caching patterns
head -50 src/contexts/seedwork/shared/domain/entity.py

# See aggregate design
head -100 src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py

# Check test patterns
head -50 tests/contexts/recipes_catalog/core/domain/meal/root_aggregate/test_meal.py
```

## 🧭 Navigation Tips

### Finding What You Need

| I want to... | Look here | Command to explore |
|--------------|-----------|-------------------|
| **Understand a domain concept** | `src/contexts/{context}/core/domain/` | `find src/contexts -name "*.py" \| grep domain` |
| **See test examples** | `tests/contexts/{context}/unit/` | `poetry run python -m pytest tests/ --collect-only` |
| **Find API contracts** | `docs/architecture/technical-specifications.md` | `grep -n "Command\|Query" docs/architecture/technical-specifications.md` |
| **Check command handlers** | `src/contexts/{context}/core/services/` | `find src -name "*command_handlers.py"` |
| **Understand caching** | `tests/performance_*.py` | `poetry run python -m pytest tests/ -k cache` |
| **See repository patterns** | `src/contexts/{context}/core/adapters/repositories/` | `find src -name "*repository*.py"` |

### Quick File Access
```bash
# Find files by pattern
find src -name "*meal*" -type f | head -10

# Search for specific patterns in code
grep -r "cached_property" src/contexts/seedwork/

# Find test files for a specific feature
find tests -name "*test_meal*" -type f

# Look for command definitions
grep -r "@dataclass" src/contexts/*/core/domain/commands/
```

## 🎓 Learning Path

### Level 1: Domain Understanding (15 minutes)
1. Read `docs/architecture/technical-specifications.md` (sections 1-3)
2. Explore one aggregate: `meal.py`
3. Run its tests: `test_meal.py`
4. Try the domain exploration exercises below

### Level 2: Implementation Patterns (30 minutes)
1. Study the base entity caching system
2. Follow a command from handler → aggregate → repository
3. Write a simple test following existing patterns
4. Understand the repository and UoW patterns

### Level 3: Advanced Patterns (60 minutes)
1. Performance optimization with caching
2. Event-driven communication
3. Domain rule validation
4. Complex aggregate interactions

## 🔍 Domain Model Exploration Exercises

### Exercise 1: Meal Aggregate (5 minutes)
```python
# In shell: poetry run python manage.py shell

# Create meal with recipes
from contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

# Explore the aggregate
meal = Meal.create_meal(name="Breakfast", author_id="chef-1", recipes=[])

# Check properties
print(f"Aggregate root: {type(meal)}")
print(f"Has caching: {hasattr(meal, '_cached_attrs')}")  
print(f"Domain events: {meal.domain_events}")

# Add a recipe (this will fail gracefully - explore why)
try:
    # This shows aggregate boundary enforcement
    meal.recipes[0]._set_name("Direct access")  
except IndexError:
    print("✓ Cannot directly access recipes - proper aggregate boundaries")
```

### Exercise 2: Caching Behavior (5 minutes)
```python
# Create meal with recipes (use test factories if available)
# meal = create_meal_with_recipes(recipe_count=3)  # If factory exists

# First access - populates cache
# nutri_facts = meal.nutri_facts
# print(f"Cached attributes: {meal._cached_attrs}")

# Modify recipes - should invalidate cache
# meal.update_recipes(recipe_id=meal.recipes[0].id, name="Updated Recipe")
# print(f"Cache after update: {meal._cached_attrs}")
```

### Exercise 3: Test Pattern Recognition (5 minutes)
```bash
# Look at test patterns
head -20 tests/contexts/recipes_catalog/core/domain/meal/root_aggregate/test_meal.py

# See cache testing
grep -A 10 -B 5 "cache" tests/contexts/recipes_catalog/core/domain/meal/root_aggregate/test_meal_instance_caching.py

# Find domain rule tests
grep -r "BusinessRule" tests/contexts/recipes_catalog/
```

## 🤖 Using with Cursor AI

### 🚀 Immediate AI Productivity

New to Cursor AI with this codebase? **Start here for instant productivity:**

1. **Reference the comprehensive guide**: See `docs/architecture/cursor-ai-guide.md` for complete setup and advanced techniques
2. **Try these 3 prompts right now** (copy-paste ready):

#### 🎯 3 Essential Prompts to Try Immediately

**1. Understand the Meal Aggregate**
```
Analyze the @src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py aggregate. Explain:
1. What business invariants it maintains
2. How it uses the base Entity caching system from @src/contexts/seedwork/shared/domain/entity.py
3. Which methods modify state vs calculate values
4. How the nutri_facts cached_property works

Include specific code examples from the file.
```

**2. Create a Test Following Project Patterns**
```
Generate a unit test for adding a recipe to a meal, following the patterns in @tests/contexts/recipes_catalog/unit/test_meal.py.

The test should:
1. Use the same fixture and setup patterns
2. Test both success and validation failure cases
3. Verify caching behavior is maintained
4. Follow the existing assertion style and naming conventions

Show the complete test method with proper imports.
```

**3. Explain a Command Handler Flow**  
```
Looking at @src/contexts/recipes_catalog/core/services/meal/command_handlers/ and @src/contexts/recipes_catalog/core/domain/meal/, explain how command handling works in this codebase.

Trace the complete flow from:
1. Command definition → Handler → Aggregate → Repository
2. Show how dependency injection works
3. Explain error handling patterns
4. Point out caching considerations

Use a specific handler as an example.
```

### 🎨 Cursor AI Best Practices for This Codebase

#### Reference Documentation Effectively
```bash
# Always include relevant documentation in your prompts:
@docs/architecture/technical-specifications.md  # For API contracts
@docs/architecture/pattern-library.md          # For implementation patterns  
@docs/architecture/domain-rules-reference.md   # For business rules
@docs/architecture/cursor-ai-guide.md          # For AI-specific guidance
```

#### Context-Aware Prompting
```
# Instead of vague requests:
❌ "Create a repository method"

# Use specific, context-aware prompts:
✅ "Looking at @src/contexts/recipes_catalog/core/adapters/repositories/, add a new method 'find_meals_by_author' that follows the established caching pattern and returns properly typed domain objects"
```

#### Leverage Existing Patterns
```
# Point to established patterns:
"Following the pattern in @src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py, create a new aggregate for [YOUR_ENTITY] with proper caching, validation, and factory methods"

# Reference test patterns:
"Generate tests following @tests/contexts/recipes_catalog/unit/test_meal.py patterns for comprehensive coverage including edge cases and caching behavior"
```

### 🔧 Quick AI Setup for This Project

#### 1. Essential Files to Include in Context
```
# Domain understanding (always include):
src/contexts/seedwork/shared/domain/entity.py
src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py
tests/contexts/recipes_catalog/unit/test_meal.py

# For specific contexts, add:
src/contexts/[your_context]/core/domain/
tests/contexts/[your_context]/unit/
docs/architecture/technical-specifications.md
```

#### 2. Cursor Settings for This Project
```json
// Recommended .cursor/settings.json
{
  "cursor.aiModelSelection": "claude-3.5-sonnet",
  "cursor.chat.includeDocumentation": true,
  "cursor.autocomplete.maxContextLines": 1000,
  "cursor.chat.maxContextLines": 10000
}
```

#### 3. Files to Exclude (.cursorignore)
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
migrations/
```

### 📋 Common AI Development Workflows

#### Workflow: Adding a New Property to an Aggregate
```
1. "Analyze @src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py to understand the current property patterns"

2. "Add property 'dietary_restrictions' of type List[str] to the Meal aggregate, following existing patterns for:
   - Dataclass field definition
   - Factory method updates  
   - Validation (if needed)
   - Caching considerations"

3. "Generate tests for the new property following @tests/contexts/recipes_catalog/unit/test_meal.py patterns"
```

#### Workflow: Creating a Repository Query
```
1. "Looking at @src/contexts/recipes_catalog/core/adapters/repositories/, show me the interface and implementation patterns"

2. "Add a new method 'find_meals_by_dietary_restrictions' that:
   - Follows the interface pattern
   - Implements proper caching
   - Uses correct typing
   - Handles edge cases appropriately"

3. "Create tests for this repository method following existing repository test patterns"
```

#### Workflow: Understanding Business Rules
```
1. "Analyze @src/contexts/recipes_catalog/core/domain/rules.py and explain how validation works in this codebase"

2. "Show me how to add a new business rule for [YOUR_RULE] following the established patterns"

3. "Generate tests that verify this business rule is enforced correctly"
```

### 🎯 Success Indicators

You're using Cursor AI effectively with this codebase when:
- ✅ Generated code follows the established domain-driven patterns
- ✅ Tests are comprehensive and match existing test styles
- ✅ Code passes all pre-commit hooks without modification
- ✅ AI correctly references the caching and repository patterns
- ✅ Generated documentation follows project conventions

### 🔗 Advanced AI Techniques

For advanced Cursor AI techniques, comprehensive templates, and troubleshooting:
👉 **See the complete guide**: `docs/architecture/cursor-ai-guide.md`

Includes:
- 20+ ready-to-use prompt templates
- Advanced multi-file context techniques
- Performance optimization with AI
- Integration with development tools
- Troubleshooting common AI issues

## 🆘 Common Issues & Quick Fixes

### Import Errors
```bash
# If you see import errors, check Python path
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Or use the manage.py shell which sets paths correctly
poetry run python manage.py shell
```

### Test Failures
```bash
# If tests fail, check database state
poetry run python manage.py check-db

# Reset test database if needed
poetry run python cleanup_test_schema.py

# Run a specific failing test with verbose output
poetry run python -m pytest path/to/failing/test.py::test_name -v -s
```

### Performance Issues
```bash
# If commands seem slow, check if you're missing poetry run python -m
# Correct:
poetry run python -m pytest

# Wrong (will use wrong Python/packages):
pytest
```

## ✅ Readiness Checklist

After completing this guide, you should be able to:
- [ ] Navigate the codebase structure confidently
- [ ] Run tests and understand the output
- [ ] Find domain objects and understand their relationships  
- [ ] Locate relevant tests for any component
- [ ] Use the development commands correctly
- [ ] Understand the aggregate boundary patterns
- [ ] Recognize the caching system in action

## 🚀 Next Steps

1. **Read the full PRD**: `tasks/prd-ai-agent-onboarding.md`
2. **Dive deeper**: `docs/architecture/technical-specifications.md`
3. **Study patterns**: Pick one aggregate and study its complete implementation
4. **Try implementing**: Add a simple method to an existing entity (with tests!)

## 📞 When You Need Help

1. **Check the troubleshooting guide**: `docs/architecture/troubleshooting-guide.md` (coming soon)
2. **Look for similar patterns**: Use `grep` to find existing implementations
3. **Run relevant tests**: Often tests show usage examples
4. **Check ADRs**: `docs/architecture/decisions/` for design rationale

Remember: This is a complex domain-driven system. Take time to understand the domain model before making changes. The architecture is designed to guide you toward correct implementations.

---

## 📚 Related Documents

### Essential Next Reads
- **[AI Agent Workflows](./ai-agent-workflows.md)** - Step-by-step development processes for implementing features
- **[Pattern Library](./pattern-library.md)** - Implementation patterns and code examples for common scenarios
- **[Technical Specifications](./technical-specifications.md)** - Complete API contracts and data models

### For Deeper Understanding  
- **[Domain Rules Reference](./domain-rules-reference.md)** - Business logic and domain constraints
- **[Decision Trees](./decision-trees.md)** - Architectural decision frameworks
- **[Troubleshooting Guide](./troubleshooting-guide.md)** - Common issues and debugging strategies

### Development Support
- **[Documentation Index](./README.md)** - Complete navigation to all documentation
- **[System Architecture Diagrams](./system-architecture-diagrams.md)** - Visual system overview 