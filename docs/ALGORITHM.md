# DebtTrack Algorithm

This document explains how DebtTrack quantifies technical debt into developer hours.

## Overview

DebtTrack calculates debt using a **hotspot score** formula that considers:
- Code complexity (nesting depth, cyclomatic complexity)
- File size (lines of code)
- File age (days since last modification)

## Hotspot Score Formula

```
hotspot_score = (complexity × LOC × 0.001) + (complexity × age_factor) + (LOC × 0.001)
```

Where:
- `complexity` = nested_depth × 1.5 + cyclomatic_estimate
- `age_factor` = min(days_since_modified × 0.01, 10) — caps at 10 to avoid old files dominating
- `LOC` = lines of code (excluding comments and blanks)

## Debt Hours Calculation

```
debt_hours = hotspot_score × refactor_multiplier
```

Default `refactor_multiplier = 4` (meaning every hotspot point represents ~4 hours of refactoring work).

## Complexity Estimation

### Nested Depth
- Calculated from indentation level
- Base depth = 1 (top-level code)
- Each 4 spaces of indentation adds 1 level
- Higher nesting = more branches, more conditional logic

### Cyclomatic Complexity (rough estimate)
- Base = 1
- +0.5 for each: `if`, `elif`, `else`, `for`, `while`, `except`, `case`, `&&`, `||`

### Limitations
This is a **rough estimation**, not a true static analysis. For accurate cyclomatic complexity, use tools like:
- Radon (Python)
- ESLint complexity rule (JavaScript)
- Go's `gocyclo`
- SonarQube

## Priority Thresholds

| Priority | Debt Hours | Action |
|----------|------------|--------|
| 🔴 Critical | ≥ 50h | Refactor immediately |
| 🟡 High | 20-50h | Next sprint |
| 🟢 Medium | 5-20h | Batch later |
| ⚪ Low | < 5h | When convenient |

## Cost Calculation

```
monthly_cost = (total_debt_hours / 12) × hourly_rate
```

Assumes debt is spread evenly across 12 months for maintenance.

## File Exclusion

Excluded patterns:
- `node_modules`, `.git`, `__pycache__`, `dist`, `build`
- `*.min.js`, `*.bundle.js`
- `.venv`, `venv`, `target`, `coverage`

## Why Hours, Not Scores?

Traditional tools give you:
- SonarQube: "A, B, C maintainability rating"
- CodeClimate: "1-4 maintainability score"
- CodeScene: "CodeHealth 1-10"

**Problem:** These don't translate to business decisions.

DebtTrack gives you:
- "347 hours of debt"
- "$4,200/month maintenance cost"
- "ROI of refactoring: 6 months"

This is what managers and CFOs understand.

## Validation

CodeScene research shows:
- **60% defect risk** when AI works on unhealthy code (high debt)
- **2-5x AI error rates** in problematic code

While our metrics are estimated, the relative comparison (which modules are worse) is reliable for prioritization.