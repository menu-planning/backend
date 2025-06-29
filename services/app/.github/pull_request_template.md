# Pull Request Template

## 📋 PR Overview
**Type of Change**: <!-- Select one -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation only changes
- [ ] ♻️ Code refactoring (no functional changes, no api changes)
- [ ] ⚡ Performance improvements
- [ ] 🧪 Tests (adding missing tests or correcting existing tests)
- [ ] 🔧 Configuration changes
- [ ] 🚀 Build/CI related changes

**Summary**: <!-- Brief description of what this PR accomplishes -->

**Related Issues**: <!-- Link any related issues, e.g., "Fixes #123" or "Related to #456" -->

## 🧪 Testing Checklist

### Code Testing
- [ ] Unit tests pass locally (`poetry run python -m pytest tests/unit/`)
- [ ] Integration tests pass locally (`poetry run python -m pytest tests/integration/`)
- [ ] All existing tests still pass
- [ ] New tests added for new functionality
- [ ] Test coverage maintained or improved
- [ ] Manual testing completed for changed functionality

### Performance Testing (if applicable)
- [ ] Performance benchmarks run and documented
- [ ] No significant performance regressions introduced
- [ ] Memory usage patterns validated
- [ ] Cache behavior verified (if cache-related changes)

## 📚 Documentation Requirements

### 🔍 Documentation Impact Assessment
**Select all that apply:**

#### Domain Model Changes
- [ ] New aggregates, entities, or value objects added
- [ ] Business rules modified or added
- [ ] Domain events introduced or changed
- [ ] Repository patterns modified

#### API Changes  
- [ ] New endpoints added
- [ ] Existing endpoints modified
- [ ] Request/response formats changed
- [ ] Authentication/authorization changes

#### Architecture Changes
- [ ] New patterns or architectural concepts introduced
- [ ] Performance optimization strategies added
- [ ] Caching strategies modified
- [ ] Integration patterns changed

#### Development Workflow Changes
- [ ] New development tools introduced
- [ ] Build/deployment process modified
- [ ] Testing strategies updated
- [ ] Environment setup changes

### 📝 Required Documentation Updates

#### For Domain Model Changes
- [ ] Update `docs/architecture/domain-rules-reference.md` if business rules changed
- [ ] Update `docs/architecture/pattern-library.md` if new patterns added
- [ ] Update `docs/architecture/technical-specifications.md` with new API examples
- [ ] Add new decision trees to `docs/architecture/decision-trees.md` if applicable

#### For API Changes
- [ ] Update API usage examples in `docs/architecture/technical-specifications.md`
- [ ] Add Lambda handler examples if new endpoints created
- [ ] Update error handling documentation with new error scenarios
- [ ] Validate all existing API examples still work

#### For Architecture Changes
- [ ] Update `docs/architecture/ai-agent-workflows.md` if workflows affected
- [ ] Update `docs/architecture/system-architecture-diagrams.md` if structure changed
- [ ] Update performance optimization guides if applicable
- [ ] Add new troubleshooting scenarios if complex changes

#### For Development Workflow Changes
- [ ] Update `docs/architecture/quick-start-guide.md` if setup process changed
- [ ] Update command examples in technical specifications
- [ ] Add new troubleshooting scenarios to `docs/architecture/troubleshooting-guide.md`
- [ ] Update validation scripts if new tools introduced

### ✅ Documentation Validation
**Required before merge:**

#### Accuracy Validation
- [ ] All code examples tested and working
  ```bash
  # Run documentation validation
  scripts/validate-docs.sh
  
  # Test specific examples if needed
  poetry run python -c "
  # Test imports from new code
  # Test any code examples added to documentation
  "
  ```
- [ ] All file paths verified to exist
- [ ] All command examples work in target environment
- [ ] Performance metrics updated if applicable

#### Content Quality Validation
- [ ] Clear explanations for new concepts
- [ ] Examples progress from simple to complex
- [ ] Prerequisites clearly stated
- [ ] Error scenarios documented
- [ ] Cross-references added to related documentation

#### AI Agent Onboarding Impact
- [ ] New functionality doesn't break 15-minute onboarding target
- [ ] Clear learning path maintained
- [ ] Common pitfalls documented
- [ ] Self-service information provided
- [ ] Integration points clearly explained

## 🔄 Development Workflow Integration

### Pre-Commit Validation
- [ ] Pre-commit hooks pass (including documentation validation)
- [ ] Code formatting applied (`poetry run python black .`)
- [ ] Linting passes (`poetry run python ruff check .`)
- [ ] Type checking passes (`poetry run python mypy src/`)

### CI/CD Pipeline Status
- [ ] All CI checks pass
- [ ] Documentation validation pipeline passes
- [ ] No breaking changes in public APIs (unless intentional)
- [ ] Deployment scripts updated if needed

## 🎯 AI Agent Onboarding Impact Assessment

### Onboarding Experience Impact
**Rate the impact on new AI agent onboarding (select one):**
- [ ] 🟢 **Positive Impact**: Makes onboarding easier or faster
- [ ] 🟡 **Neutral Impact**: No significant change to onboarding experience  
- [ ] 🟠 **Potential Confusion**: May require additional explanation or examples
- [ ] 🔴 **Breaking Change**: Requires immediate documentation updates to prevent confusion

### Knowledge Transfer Requirements
**Select if applicable:**
- [ ] New concepts introduced that need explanation
- [ ] Existing patterns modified that need documentation updates
- [ ] Performance characteristics changed that affect usage guidance
- [ ] Integration patterns changed that affect workflow documentation

### Documentation Maintenance Burden
**Estimated ongoing maintenance impact:**
- [ ] 🟢 **Low**: Minimal future maintenance required
- [ ] 🟡 **Medium**: Occasional updates may be needed
- [ ] 🔴 **High**: Will require regular maintenance as code evolves

## 📊 Review Guidelines for Reviewers

### Technical Review Focus
- [ ] **Domain Accuracy**: Business logic correctly implements domain rules
- [ ] **Architecture Alignment**: Changes follow established patterns
- [ ] **Performance Impact**: No unexpected performance regressions
- [ ] **Test Coverage**: Adequate test coverage for changes
- [ ] **Error Handling**: Proper error handling and logging

### Documentation Review Focus
- [ ] **Accuracy**: All documentation changes reflect actual implementation
- [ ] **Completeness**: All necessary documentation updated
- [ ] **Clarity**: Explanations clear for target audience (AI agents)
- [ ] **Examples**: Code examples work and demonstrate concepts effectively
- [ ] **Integration**: Changes integrate well with existing documentation

### AI Agent Onboarding Review
- [ ] **Learning Path**: Changes don't disrupt logical learning progression
- [ ] **Time to Productivity**: Maintains or improves onboarding speed
- [ ] **Self-Service**: Provides sufficient information for independent work
- [ ] **Common Pitfalls**: Documents potential confusion points

## 🚀 Deployment Considerations

### Infrastructure Impact
- [ ] Database migrations included if schema changes
- [ ] Environment variables documented if new config added
- [ ] Lambda deployment considerations documented
- [ ] Performance monitoring considerations included

### Rollback Plan
- [ ] Rollback strategy documented if needed
- [ ] Breaking changes clearly identified
- [ ] Migration path provided for major changes
- [ ] Backwards compatibility maintained where possible

## 📝 Additional Notes

### Implementation Details
<!-- Any additional context about implementation decisions, trade-offs, or considerations -->

### Review Focus Areas
<!-- Specific areas where you'd like reviewers to focus attention -->

### Breaking Changes Details
<!-- If breaking changes, provide detailed migration guide -->

### Performance Impact
<!-- Document any performance implications, positive or negative -->

---

## 📋 Pre-Merge Checklist

**Author Checklist:**
- [ ] All tests pass locally and in CI
- [ ] Documentation updated per requirements above
- [ ] Documentation validation passes (`scripts/validate-docs.sh`)
- [ ] Performance impact assessed and documented
- [ ] Breaking changes clearly identified and documented
- [ ] Self-review completed using review guidelines

**Reviewer Checklist:**
- [ ] Code review completed following review guidelines
- [ ] Documentation review completed and validated
- [ ] AI agent onboarding impact assessed
- [ ] Architecture alignment verified
- [ ] Performance impact acceptable
- [ ] Test coverage adequate

**Documentation Maintainer Checklist:**
- [ ] Documentation changes reviewed for accuracy
- [ ] Examples tested and working
- [ ] Integration with existing docs verified
- [ ] Maintenance burden assessed and acceptable
- [ ] AI agent onboarding experience impact evaluated

---

*This PR template ensures all changes properly support AI agent onboarding while maintaining code quality and documentation accuracy.* 