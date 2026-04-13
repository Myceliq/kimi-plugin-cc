---
description: Bulk-fix findings from audit, review, or UI review using Agent Swarm parallelism
argument-hint: <findings-json-or-job-id> [--severity <min>] [--category <list>] [--max <n>]
context: fork
allowed-tools: ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep
---

# /kimi:fix

Take findings from `/kimi:audit`, `/kimi:swarm-review`, or `/kimi:review-ui` and fix them in bulk. Parallelizes independent fixes across files using Agent Swarm.

## Usage

```
/kimi:fix <findings-source> [options]
```

## Arguments

- `findings-source`: One of:
  - Path to a findings JSON file
  - A job ID from a previous `/kimi:audit`, `/kimi:swarm-review`, or `/kimi:review-ui` run (fetches the stored result)
  - `--last` to use the most recently completed audit/review job
- `--severity <min>`: Minimum severity to fix. Default: `medium` (fixes critical, high, medium). Options: `critical`, `high`, `medium`, `low`, `info`
- `--category <list>`: Comma-separated categories to target (e.g., `security,dead-code`). Default: all categories
- `--max <n>`: Maximum number of findings to fix. Default: no limit
- `--dry-run`: Show what would be fixed without making changes

## Examples

```
/kimi:fix --last
/kimi:fix --last --severity critical
/kimi:fix /tmp/audit-results.json --category security,dead-code
/kimi:fix kimi-audit-20260413-abc123 --max 20
/kimi:fix --last --dry-run
```

## How it works

1. Parses findings and applies severity/category filters
2. Groups findings by file — same-file findings are sequential, different files parallelize
3. Dispatches Agent Swarm subagents for independent file groups
4. Each subagent: reads file, applies fixes bottom-up, runs tests
5. Verifies no regressions — reverts any fix that breaks tests
6. Returns structured results: fixed, skipped, reverted counts + details

## Output

Returns a JSON object with:
- `status`: "complete" or "partial"
- `stats`: Total findings, fixed, skipped, reverted, agents used
- `fixed`: Array of successfully applied fixes with descriptions
- `skipped`: Array of findings that couldn't be fixed (with reasons)
- `reverted`: Array of fixes that caused test regressions
- `test_results`: Final test suite pass/fail status
- `files_changed`: List of modified files

## Notes

- Fixes critical and high severity first, then medium
- Reverts any fix that causes test failures — safety over completeness
- Uses Agent Swarm for parallel fixes across independent files
- Runs tests after each file group, not just at the end
- Pairs naturally with `/kimi:audit` and `/kimi:swarm-review`
