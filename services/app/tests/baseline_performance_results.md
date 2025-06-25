# Baseline Performance Results - Domain Heavy Computations

**Captured on:** Pre-refactoring (Phase 0.1.4)  
**Target Improvements:** ≥30% speed improvement + ≥95% cache hit ratio

## Performance Benchmarks (in nanoseconds)

| Test | Min (ns) | Max (ns) | Mean (ns) | Median (ns) | OPS (Kops/s) | Notes |
|------|----------|----------|-----------|-------------|--------------|-------|
| Recipe macro_division | 157.99 | 12,916.00 | 202.68 | 183.00 | 4,933.90 | Fastest computation |
| Meal nutri_facts | 164.99 | 2,089.00 | 212.64 | 182.99 | 4,702.69 | Aggregates 10 recipes |
| Meal macro_division | 166.00 | 890.99 | 200.30 | 180.99 | 4,992.48 | Depends on nutri_facts |
| Recipe average ratings | 256.99 | 19,424.00 | 442.52 | 303.99 | 2,259.80 | 50 ratings computation |
| Meal repeated access (5x each) | 23,442.00 | 26,740.99 | 24,446.41 | 24,453.50 | 40.91 | Cache effectiveness test |

## Key Observations

### Current Performance Characteristics
- **Individual computations** are relatively fast (157-442 ns mean)
- **Repeated access** shows significant overhead (24,446 ns mean for 20 property accesses)
- **Cache effectiveness** appears limited with current @lru_cache implementation

### Heavy Computation Properties Identified
1. **Meal.nutri_facts** - Aggregates nutrition from multiple recipes
2. **Meal.macro_division** - Calculates macro percentages from nutri_facts
3. **_Recipe.average_taste_rating** - Averages taste ratings (with @lru_cache)
4. **_Recipe.average_convenience_rating** - Averages convenience ratings (with @lru_cache)  
5. **_Recipe.macro_division** - Calculates recipe macro percentages (with @lru_cache)

### Performance Targets for Post-Refactoring
- **Speed improvement target**: ≥30% faster (target mean times)
  - Recipe macro_division: ≤142 ns
  - Meal nutri_facts: ≤149 ns  
  - Meal macro_division: ≤140 ns
  - Recipe average ratings: ≤310 ns
  - Meal repeated access: ≤17,112 ns

- **Cache hit ratio target**: ≥95%
- **Cache behavior**: Instance-level caching vs shared @lru_cache

## Test Environment
- **Python**: 3.12.3
- **pytest-benchmark**: 4.0.0  
- **Test data**: 10 recipes per meal, 50 ratings per recipe
- **Iterations**: Automatic (pytest-benchmark controlled)

## Current Issues to Address
1. **Shared cache bugs** with @lru_cache on properties
2. **Cache invalidation** problems when domain state changes
3. **Performance bottlenecks** in repeated property access
4. **Missing instance-level caching** leading to repeated computation

---
*This baseline will be used to validate ≥30% performance improvement and ≥95% cache hit ratio after implementing instance-level caching with @cached_property* 