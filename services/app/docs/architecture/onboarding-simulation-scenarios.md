# Onboarding Simulation Scenarios

## Overview
This document contains structured scenarios to test the effectiveness of our AI agent onboarding documentation. Each scenario simulates a realistic situation an AI agent might encounter when first working with the menu planning backend codebase.

## Success Criteria
- **Time to First Success**: Complete basic task within 30 minutes using docs only
- **Self-Service Rate**: 90% of questions answered through documentation
- **Code Quality**: Generated code follows established patterns
- **Domain Understanding**: Demonstrates grasp of DDD concepts and business rules

---

## Scenario 1: "Fresh Start" - Complete Beginner Agent

### Context
- New AI agent with no prior knowledge of the codebase
- Has access to all documentation but no human guidance
- First interaction with domain-driven design patterns

### Tasks
1. **Environment Setup** (Target: 5 minutes)
   - Use quick-start guide to understand project structure
   - Validate environment setup
   - Run first test command successfully

2. **Simple Feature Request** (Target: 15 minutes)
   - "Add a 'favorite' flag to meals"
   - Use workflow guide to analyze the request
   - Identify which aggregate needs modification
   - Locate relevant files

3. **Pattern Implementation** (Target: 10 minutes)
   - Use pattern library to implement the change
   - Follow domain event patterns if needed
   - Ensure proper testing approach

### Expected Documentation Usage
- `docs/architecture/quick-start-guide.md` - Environment and commands
- `docs/architecture/ai-agent-workflows.md` - Feature analysis workflow
- `docs/architecture/decision-trees.md` - "Which Aggregate to Modify?"
- `docs/architecture/pattern-library.md` - Implementation patterns

### Success Metrics
- [ ] Completes environment validation within 5 minutes
- [ ] Correctly identifies Meal aggregate needs modification
- [ ] Follows established patterns for domain property addition
- [ ] Includes appropriate tests in implementation plan

---

## Scenario 2: "Performance Concern" - Optimization Task

### Context
- AI agent needs to investigate and optimize a slow query
- Must understand caching strategies and performance patterns
- Should demonstrate proper benchmarking approach

### Tasks
1. **Problem Analysis** (Target: 10 minutes)
   - Given: "Recipe search is slow with large datasets"
   - Use troubleshooting guide to investigate
   - Identify potential performance bottlenecks

2. **Solution Selection** (Target: 10 minutes)
   - Use decision trees to evaluate caching options
   - Consider repository vs direct query patterns
   - Plan performance measurement approach

3. **Implementation Planning** (Target: 10 minutes)
   - Use pattern library for caching implementation
   - Include proper benchmarking setup
   - Plan validation strategy

### Expected Documentation Usage
- `docs/architecture/troubleshooting-guide.md` - Performance investigation
- `docs/architecture/decision-trees.md` - "Should I Cache This?" flowchart
- `docs/architecture/pattern-library.md` - Cached property patterns
- `docs/architecture/technical-specifications.md` - Performance profiling examples

### Success Metrics
- [ ] Correctly identifies query performance as repository-level issue
- [ ] Selects appropriate caching strategy using decision tree
- [ ] Plans proper benchmarking with BenchmarkTimer
- [ ] Considers cache invalidation strategies

---

## Scenario 3: "Cross-Aggregate Coordination" - Complex Feature

### Context
- AI agent must implement a feature that spans multiple aggregates
- Requires understanding of domain events and coordination patterns
- Tests grasp of DDD principles and async patterns

### Tasks
1. **Feature Analysis** (Target: 15 minutes)
   - Request: "When a recipe is deleted, remove it from all meal plans"
   - Use workflow guide for feature analysis
   - Identify cross-aggregate coordination needs

2. **Architecture Decision** (Target: 10 minutes)
   - Use decision trees for event vs direct call
   - Plan proper aggregate boundaries
   - Consider consistency requirements

3. **Implementation Strategy** (Target: 15 minutes)
   - Use pattern library for domain events
   - Plan proper error handling
   - Include integration testing approach

### Expected Documentation Usage
- `docs/architecture/ai-agent-workflows.md` - Feature analysis workflow
- `docs/architecture/decision-trees.md` - "Event vs Direct Call" tree
- `docs/architecture/pattern-library.md` - Domain event patterns
- `docs/architecture/technical-specifications.md` - Event handling examples

### Success Metrics
- [ ] Correctly identifies this as cross-aggregate operation
- [ ] Chooses domain events over direct aggregate calls
- [ ] Plans proper event handlers and error scenarios
- [ ] Includes integration test strategy

---

## Scenario 4: "Lambda Handler Creation" - API Development

### Context
- AI agent needs to create new API endpoint
- Must understand Lambda patterns and authorization
- Should demonstrate proper error handling and validation

### Tasks
1. **API Design** (Target: 10 minutes)
   - Request: "Create endpoint to get user's favorite meals"
   - Use technical specifications for API patterns
   - Plan proper request/response structure

2. **Implementation** (Target: 15 minutes)
   - Use pattern library for Lambda handler
   - Include proper authorization checks
   - Plan validation and error handling

3. **Testing Strategy** (Target: 5 minutes)
   - Use decision trees for test strategy selection
   - Plan unit and integration tests
   - Consider performance testing needs

### Expected Documentation Usage
- `docs/architecture/technical-specifications.md` - Lambda handler examples
- `docs/architecture/pattern-library.md` - Lambda handler patterns
- `docs/architecture/decision-trees.md` - Test strategy selection
- `docs/architecture/troubleshooting-guide.md` - Lambda deployment issues

### Success Metrics
- [ ] Follows established Lambda handler patterns
- [ ] Includes proper authorization and validation
- [ ] Plans comprehensive error handling
- [ ] Includes appropriate test coverage

---

## Scenario 5: "Debugging Session" - Troubleshooting

### Context
- AI agent encounters common development issues
- Must use troubleshooting guide effectively
- Should demonstrate systematic problem-solving

### Tasks
1. **Import Error Resolution** (Target: 5 minutes)
   - Given: `ModuleNotFoundError: No module named 'src.contexts.recipes_catalog.core.domain.meal'`
   - Use troubleshooting guide to diagnose and fix
   
2. **Test Failure Investigation** (Target: 10 minutes)
   - Given: Test fails with database session issues
   - Use troubleshooting guide for systematic debugging
   - Identify proper fixture usage

3. **Cache Inconsistency** (Target: 15 minutes)
   - Given: Cached properties showing stale data
   - Use troubleshooting guide to identify cache invalidation issue
   - Plan proper fix using established patterns

### Expected Documentation Usage
- `docs/architecture/troubleshooting-guide.md` - All sections
- `docs/architecture/technical-specifications.md` - Database and cache examples
- `docs/architecture/pattern-library.md` - Cached property patterns

### Success Metrics
- [ ] Quickly identifies and fixes import path issues
- [ ] Correctly diagnoses database session management problems
- [ ] Understands cache invalidation patterns and solutions
- [ ] Uses systematic debugging approach from guide

---

## Scenario 6: "Code Review Preparation" - Quality Assurance

### Context
- AI agent has implemented a feature and needs to prepare for review
- Must demonstrate understanding of quality standards
- Should use code review workflow effectively

### Tasks
1. **Self-Review Process** (Target: 10 minutes)
   - Use workflow guide for code review preparation
   - Check implementation against established patterns
   - Validate test coverage and documentation

2. **Performance Validation** (Target: 10 minutes)
   - Use performance profiling examples
   - Run benchmarks and validate against targets
   - Check for potential optimization opportunities

3. **Integration Validation** (Target: 10 minutes)
   - Validate cross-aggregate interactions
   - Check event handling and error scenarios
   - Ensure proper logging and monitoring

### Expected Documentation Usage
- `docs/architecture/ai-agent-workflows.md` - Code review preparation workflow
- `docs/architecture/technical-specifications.md` - Performance profiling
- `docs/architecture/decision-trees.md` - Performance optimization priorities

### Success Metrics
- [ ] Follows systematic code review checklist
- [ ] Validates performance against established benchmarks
- [ ] Checks integration points and error handling
- [ ] Demonstrates quality mindset and attention to detail

---

## Evaluation Framework

### Time-to-Productivity Measurement
```
Scenario Completion Times:
- Scenario 1 (Beginner): _____ minutes (Target: 30 minutes)
- Scenario 2 (Performance): _____ minutes (Target: 30 minutes)
- Scenario 3 (Cross-Aggregate): _____ minutes (Target: 40 minutes)
- Scenario 4 (Lambda Handler): _____ minutes (Target: 30 minutes)
- Scenario 5 (Debugging): _____ minutes (Target: 30 minutes)
- Scenario 6 (Code Review): _____ minutes (Target: 30 minutes)

Average Time to Complete Basic Tasks: _____ minutes
Success Rate (Completed Successfully): _____%
```

### Documentation Usage Tracking
```
Documentation Section Usage:
- Quick Start Guide: Used? Y/N | Effective? Y/N | Issues: _____
- Technical Specifications: Used? Y/N | Effective? Y/N | Issues: _____
- AI Agent Workflows: Used? Y/N | Effective? Y/N | Issues: _____
- Decision Trees: Used? Y/N | Effective? Y/N | Issues: _____
- Pattern Library: Used? Y/N | Effective? Y/N | Issues: _____
- Troubleshooting Guide: Used? Y/N | Effective? Y/N | Issues: _____
```

### Knowledge Transfer Assessment
```
Domain Understanding Demonstrated:
- [ ] Correctly identifies aggregate boundaries
- [ ] Understands domain events vs direct calls
- [ ] Applies caching strategies appropriately
- [ ] Follows established code patterns
- [ ] Implements proper error handling
- [ ] Includes appropriate test coverage
- [ ] Considers performance implications
- [ ] Demonstrates systematic problem-solving
```

### Common Issues Tracking
```
Frequent Questions/Confusion Points:
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________

Documentation Gaps Identified:
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________

Suggested Improvements:
1. _________________________________
2. _________________________________
3. _________________________________
4. _________________________________
5. _________________________________
```

## Simulation Execution Instructions

### For Each Scenario:
1. **Setup**: Start with clean slate, documentation only
2. **Record**: Track time spent on each task
3. **Document**: Note which documentation sections are used
4. **Evaluate**: Assess quality of approach and final result
5. **Feedback**: Record any confusion points or gaps

### Success Criteria Validation:
- **30-minute productivity**: Basic scenarios completed within time limit
- **90% self-service**: Questions answered through documentation
- **Pattern compliance**: Generated code follows established patterns
- **Quality standards**: Includes tests, error handling, performance considerations

### Iteration Process:
1. Run all scenarios and collect data
2. Identify common issues and documentation gaps  
3. Update documentation based on findings
4. Re-run failed scenarios to validate improvements
5. Document lessons learned and update processes

This simulation framework provides comprehensive testing of our AI agent onboarding documentation effectiveness across realistic scenarios that cover the full development lifecycle. 