You are continuing work on AI Agent Onboarding Documentation Enhancement for a menu planning backend.

**CONTEXT:**
- This is a domain-driven design (DDD) system with asynchronous patterns
- Uses Poetry for dependency management, pytest for testing, PostgreSQL for data
- Architecture follows "Architecture Patterns with Python" adapted for async/Lambda

**COMPLETED WORK:**
✅ Phase 1.1: Created comprehensive quick start guide at `docs/architecture/quick-start-guide.md`
  - 15-minute onboarding checklist with working commands
  - All commands validated to use `poetry run python -m` pattern  
  - Import paths tested and corrected (NutriFacts location fixed)
  - 10 cache-related tests confirmed working

**CURRENT TASK:** Phase 1.3 - Enhance Technical Specifications
**GOAL:** Add interactive examples to `docs/architecture/technical-specifications.md`

**NEXT STEPS:**
1. Follow @process-task-list.mdc to implement tasks 1.3.1-1.3.6 from @tasks-prd-ai-agent-onboarding.md
2. Add "Common Operations" section with copy-paste code examples
3. Create API usage examples for each command/query
4. Include error handling examples with actual error messages
5. Validate all examples work in actual environment

**KEY FILES VALIDATED:**
- `src/contexts/seedwork/shared/domain/entity.py` - Base entity with caching
- `src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py` - Meal aggregate  
- `tests/contexts/seedwork/shared/domain/test_entity_cache_invalidation.py` - 10 cache tests
- `docs/architecture/technical-specifications.md` - Target for enhancement

**IMPORTANT:** PRD (`tasks/prd-ai-agent-onboarding.md`) is planning doc only - do not modify.

Use Standard Mode execution: validate examples as you add them, get approval before major phases. 