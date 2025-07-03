# Documentation Versioning Strategy

## 🎯 Purpose
This strategy ensures consistent, trackable versioning of AI agent onboarding documentation that aligns with code releases and maintains backward compatibility when needed.

## 📋 Versioning Principles

### 1. Documentation Follows Code
- Documentation versions align with application releases
- Major documentation changes accompany major code releases
- Documentation patches can be released independently for urgent fixes

### 2. Semantic Versioning for Documentation
We use a modified semantic versioning approach:
- **MAJOR.MINOR.PATCH** (e.g., `v2.1.3`)
- **MAJOR**: Significant architectural changes, new workflows, breaking changes in documented patterns
- **MINOR**: New sections, enhanced examples, additional workflows, new patterns
- **PATCH**: Bug fixes, typo corrections, link updates, example fixes

### 3. Release Alignment Strategy
- **Code Release**: Documentation MAJOR/MINOR version
- **Documentation Enhancement**: Documentation MINOR version
- **Bug Fixes/Updates**: Documentation PATCH version
- **Emergency Fixes**: Documentation PATCH with hotfix suffix

## 📊 Version Numbering System

### Version Format: `vMAJOR.MINOR.PATCH[-SUFFIX]`

#### MAJOR Version (X.0.0)
Increment when:
- [ ] New domain aggregates require significant workflow changes
- [ ] Architecture patterns fundamentally change
- [ ] Development workflow significantly changes
- [ ] Multiple documentation files require major restructuring
- [ ] Breaking changes in documented APIs/patterns

**Examples:**
- `v1.0.0` → `v2.0.0`: Migration from DDD to event sourcing architecture
- `v2.0.0` → `v3.0.0`: New microservices architecture with different onboarding workflow

#### MINOR Version (X.Y.0) 
Increment when:
- [ ] New workflow sections added to existing files
- [ ] Additional decision trees or pattern examples
- [ ] New troubleshooting scenarios
- [ ] Enhanced performance optimization guides
- [ ] New Lambda deployment patterns
- [ ] Additional testing strategies

**Examples:**
- `v1.1.0`: Added "GraphQL API" workflow to ai-agent-workflows.md
- `v1.2.0`: New "Microservices Communication" patterns in pattern-library.md
- `v1.3.0`: Enhanced troubleshooting guide with Kubernetes deployment issues

#### PATCH Version (X.Y.Z)
Increment when:
- [ ] Fix broken code examples
- [ ] Update file paths or imports
- [ ] Correct typos or formatting issues
- [ ] Update performance metrics/benchmarks
- [ ] Fix broken internal/external links
- [ ] Update command examples for new tool versions

**Examples:**
- `v1.1.1`: Fixed import paths in quick-start-guide.md
- `v1.1.2`: Updated pytest command examples
- `v1.1.3`: Corrected performance benchmarks in technical-specifications.md

#### Suffixes
- **-alpha**: Pre-release version for testing
- **-beta**: Release candidate for team review
- **-hotfix**: Emergency patch for critical issues
- **-rc**: Release candidate

**Examples:**
- `v1.2.0-alpha`: New patterns being tested
- `v1.1.4-hotfix`: Critical security update in Lambda examples

## 🏷️ Tagging Strategy

### Git Tag Format
```bash
# Standard release
git tag -a "docs-v1.2.0" -m "Enhanced AI workflows with GraphQL patterns"

# Pre-release
git tag -a "docs-v1.2.0-alpha" -m "Alpha version with new GraphQL workflows"

# Hotfix
git tag -a "docs-v1.1.4-hotfix" -m "Critical fix for security vulnerability in Lambda examples"
```

### Tag Naming Convention
- **Prefix**: `docs-` to distinguish from code releases
- **Version**: Standard semantic version
- **Message**: Brief description of main changes

### Tagging Commands
```bash
# List all documentation tags
git tag -l "docs-*"

# Show specific tag details
git show docs-v1.2.0

# Create and push tag
git tag -a "docs-v1.2.0" -m "Documentation release notes"
git push origin docs-v1.2.0

# Delete tag (if needed)
git tag -d docs-v1.2.0
git push origin --delete docs-v1.2.0
```

## 📅 Release Schedule

### Regular Release Cycle
- **Monthly**: Patch releases for accumulated fixes
- **Quarterly**: Minor releases for new content/enhancements  
- **Annually**: Major version consideration (typically aligns with major code architecture changes)
- **As-needed**: Hotfix releases for critical issues

### Release Triggers

#### Automatic Minor Release Triggers
- [ ] New aggregates added to domain model
- [ ] New API endpoints require documentation
- [ ] New deployment/infrastructure patterns introduced
- [ ] New testing frameworks or patterns adopted
- [ ] Performance optimization strategies discovered

#### Automatic Patch Release Triggers
- [ ] Code examples break due to dependency updates
- [ ] File paths change due to restructuring
- [ ] Tool command syntax changes (pytest, mypy, etc.)
- [ ] Performance benchmarks become outdated
- [ ] New troubleshooting scenarios discovered

#### Manual Major Release Consideration
- [ ] Architecture paradigm changes (DDD → Event Sourcing → CQRS)
- [ ] Platform changes (Lambda → Kubernetes → Serverless)
- [ ] Development methodology changes (TDD → BDD → DDD)
- [ ] Multiple breaking changes accumulate

## 📝 Version Documentation

### Release Notes Format
Each version should include:

```markdown
# Documentation Release v1.2.0 - YYYY-MM-DD

## 🎯 Overview
Brief description of the release focus and main improvements.

## 📊 Changes Summary
- Files modified: [number]
- New sections: [number] 
- Examples updated: [number]
- Issues resolved: [number]

## ✨ New Features
- [List new sections, workflows, patterns]

## 🔧 Improvements  
- [List enhanced examples, updated metrics, improved clarity]

## 🐛 Bug Fixes
- [List corrected examples, fixed links, resolved issues]

## 💔 Breaking Changes
- [List any changes that affect existing workflows - rare for docs]

## 📋 File Changes
### Modified Files
- `docs/architecture/quick-start-guide.md` - [brief description]
- `docs/architecture/technical-specifications.md` - [brief description]

### New Files
- `docs/architecture/new-workflow-guide.md` - [description]

## 🔍 Validation Results
- [ ] All code examples tested
- [ ] All links verified
- [ ] Cross-references validated
- [ ] Performance benchmarks updated

## ⬆️ Upgrade Instructions
[Any special steps needed when updating to this version]

## 🔗 Links
- [Previous Version](../releases/docs-v1.1.3.md)
- [Full Changelog](../CHANGELOG.md)
```

### Changelog Maintenance
Maintain `docs/CHANGELOG.md` with:
- All releases in reverse chronological order
- Links to detailed release notes
- Migration guides for major versions
- Deprecation notices

## 🔄 Branching Strategy

### Branch Naming Convention
```bash
# Feature branches for new documentation
docs/feature/new-workflow-patterns    # Minor version
docs/feature/enhanced-troubleshooting # Minor version

# Bug fix branches
docs/fix/broken-examples              # Patch version
docs/fix/outdated-imports            # Patch version

# Hotfix branches  
docs/hotfix/security-vulnerability    # Patch version with hotfix suffix

# Release preparation branches
docs/release/v1.2.0                  # For preparing releases
```

### Development Workflow
```bash
# 1. Create feature branch
git checkout -b docs/feature/new-patterns

# 2. Make changes and commit
git add docs/architecture/
git commit -m "feat: add new async patterns to workflows guide"

# 3. Create PR with version impact in description
# PR Title: "[MINOR] Add async patterns to workflow guide"

# 4. After review and merge, tag release
git checkout main
git pull origin main
git tag -a "docs-v1.2.0" -m "Add async patterns and enhanced examples"
git push origin docs-v1.2.0
```

## 📊 Version Tracking

### Metadata in Documentation Files
Each major documentation file should include version metadata:

```markdown
---
version: "1.2.0"
last_updated: "2024-01-15"
next_review: "2024-04-15"
maintainer: "team@example.com"
---
```

### Version Compatibility Matrix
Track compatibility between documentation and code versions:

| Documentation Version | Compatible Code Versions | Notes |
|----------------------|---------------------------|-------|
| docs-v1.0.0         | app-v1.0.0 - app-v1.2.x | Initial release |
| docs-v1.1.0         | app-v1.1.0 - app-v1.3.x | Added GraphQL workflows |
| docs-v1.2.0         | app-v1.2.0 - app-v1.4.x | Enhanced async patterns |

### Deprecation Policy
- **Notice Period**: 2 minor versions before removal
- **Support Period**: Continue supporting previous major version for 6 months
- **Migration Guide**: Always provide upgrade path for breaking changes

Example:
```markdown
> ⚠️ **DEPRECATED**: The workflow described in section X.Y is deprecated as of docs-v1.2.0 
> and will be removed in docs-v2.0.0. Use the new workflow in section Z.A instead.
> See [Migration Guide](../migrations/v1-to-v2.md) for details.
```

## 🔍 Version Validation

### Pre-Release Checklist
Before tagging any version:

- [ ] Run all validation commands from maintenance checklist
- [ ] Test examples in clean environment
- [ ] Verify all internal links work
- [ ] Check external references are current
- [ ] Validate version number follows semantic versioning rules
- [ ] Confirm release notes are complete and accurate
- [ ] Verify compatibility matrix is updated

### Automated Validation
```bash
# Script: scripts/validate-docs-version.sh
#!/bin/bash

echo "🔍 Validating documentation for release..."

# Check version consistency across files
echo "Checking version metadata..."
grep -r "version:" docs/architecture/ | grep -v ".git"

# Validate all links
echo "Validating internal links..."
find docs/ -name "*.md" -exec grep -l "\[.*\](.*\.md)" {} \; | xargs -I {} bash -c 'echo "Checking: {}"; markdown-link-check {}'

# Test code examples  
echo "Testing code examples..."
poetry run python scripts/test-doc-examples.py

# Check for TODO/FIXME markers
echo "Checking for incomplete sections..."
grep -r "TODO\|FIXME\|XXX" docs/architecture/ || echo "✅ No incomplete markers found"

echo "✅ Documentation validation complete"
```

## 📈 Metrics and Analytics

### Version Metrics to Track
- [ ] Release frequency (monthly/quarterly averages)
- [ ] Time between code release and documentation update
- [ ] Number of hotfixes per quarter (target: <2)
- [ ] Documentation coverage of new features (target: 100%)
- [ ] User feedback correlation with version quality

### Success Metrics
- **Currency**: Documentation never more than 1 release cycle behind code
- **Stability**: <1 hotfix per quarter on average
- **Completeness**: All new features documented within 1 week of code release
- **Quality**: >95% of examples work without modification
- **Usability**: User feedback score >4.5/5 for documentation quality

## 🚀 Release Automation

### GitHub Actions Workflow
```yaml
# .github/workflows/docs-release.yml
name: Documentation Release

on:
  push:
    tags:
      - 'docs-v*'

jobs:
  release-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate Documentation
        run: |
          bash scripts/validate-docs-version.sh
          
      - name: Generate Release Notes
        run: |
          bash scripts/generate-release-notes.sh ${{ github.ref_name }}
          
      - name: Create GitHub Release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.ref }}
          release_name: Documentation ${{ github.ref }}
          body_path: release-notes.md
```

### Release Scripts
```bash
# scripts/release-docs.sh
#!/bin/bash
VERSION=$1
TYPE=$2  # major, minor, patch

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [type]"
    echo "Example: $0 1.2.0 minor"
    exit 1
fi

echo "🚀 Preparing documentation release v$VERSION..."

# Validate current state
bash scripts/validate-docs-version.sh

# Update version metadata in files
bash scripts/update-version-metadata.sh $VERSION

# Generate changelog entry
bash scripts/generate-changelog-entry.sh $VERSION $TYPE

# Create release notes
bash scripts/generate-release-notes.sh $VERSION

echo "📋 Manual steps remaining:"
echo "1. Review generated release notes"
echo "2. Create and push tag: git tag -a docs-v$VERSION -m 'Documentation release v$VERSION'"
echo "3. Create GitHub release with generated notes"
```

## 📚 Version History

### Version 1.x Series (Current)
- **v1.0.0** (2024-01-01): Initial comprehensive documentation release
- **v1.1.0** (2024-02-01): Added GraphQL workflows and enhanced patterns
- **v1.2.0** (2024-03-01): Async patterns and performance optimization guides

### Planned Version 2.x Series  
- **v2.0.0** (TBD): Major architecture changes (when/if application moves to microservices)

---

## 🎯 Implementation Checklist

To implement this versioning strategy:

- [ ] Add version metadata to all existing documentation files
- [ ] Create initial changelog and release notes templates
- [ ] Set up automated validation scripts
- [ ] Create release automation workflow
- [ ] Train team on versioning workflow
- [ ] Establish monitoring for version metrics
- [ ] Create first official release tag for current documentation state

This versioning strategy ensures our AI agent onboarding documentation remains well-organized, traceable, and aligned with the development workflow while providing clear upgrade paths and maintaining high quality standards. 