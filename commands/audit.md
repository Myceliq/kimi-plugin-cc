---
description: Run a comprehensive codebase audit for issues across multiple categories
argument-hint: '[--focus <categories>]'
context: fork
allowed-tools: ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep
---

# /kimi:audit

Run a comprehensive audit of the entire codebase to identify issues across security, dead code, naming, error handling, test coverage, dependencies, and documentation.

## Usage

```
/kimi:audit [--focus <categories>]
```

## Arguments

- `--focus`: Optional comma-separated list of categories to focus on (default: all)
  - `security` — Security vulnerabilities
  - `dead-code` — Dead code and unused exports
  - `naming` — Naming and pattern inconsistencies
  - `error-handling` — Missing error handling
  - `test-coverage` — Test coverage gaps
  - `dependencies` — Dependency issues
  - `documentation` — Documentation staleness

## Examples

```
/kimi:audit
/kimi:audit --focus security
/kimi:audit --focus security,error-handling,dead-code
```

## How it works

1. **Catalog**: Scans the codebase and creates an inventory of all source files (excludes node_modules/, .git/, build/)
2. **Partition**: Divides files into work packages based on module cohesion and codebase size
3. **Dispatch**: Launches parallel subagents (up to 100) to analyze work packages
4. **Synthesize**: Deduplicates, ranks by severity, groups by category, and produces executive summary

## Output

Returns a JSON object with:
- `summary`: Executive summary of codebase health
- `stats`: Files analyzed, agents used, total findings
- `findings`: Array of issues with severity, category, file/line info, and recommendations
- `by_category`: Breakdown of findings by category
- `next_steps`: Prioritized actionable items

## Scaling

| Codebase Size | Files per Agent | Max Agents |
|--------------|-----------------|------------|
| < 50 files   | ~5 files        | 10         |
| 50-200 files | ~10 files       | 20         |
| 200-1000 files| ~25 files      | 40         |
| 1000-5000 files| ~100 files    | 50         |
| 5000-10000 files| ~150 files   | 67         |
| 10000+ files | ~200 files      | 100 (max)  |

## Notes

- Always runs in `--background` mode due to potentially long execution time
- Enterprise multi-session audit (v2) is not implemented
- Excludes: node_modules/, .git/, build/, dist/, vendored code
