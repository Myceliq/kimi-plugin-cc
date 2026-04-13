---
description: Execute a task plan with parallel generation and evaluation via Agent Swarm
argument-hint: <plan-file-or-inline> [--no-eval] [--parallel <max>]
context: fork
allowed-tools: ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep
---

# /kimi:sprint

Give Kimi a task plan — it executes every task using Agent Swarm with TDD generation and skeptical evaluation. Independent tasks run in parallel, dependent tasks respect ordering.

## Usage

```
/kimi:sprint <plan-source> [options]
```

## Arguments

- `plan-source`: One of:
  - Path to a plan file (markdown with task entries)
  - Inline task description (Kimi will parse tasks from it)
- `--no-eval`: Skip evaluator verification (generator only, faster but no quality gate)
- `--parallel <max>`: Maximum parallel generators (default: let Agent Swarm decide)

## Plan Format

The plan should contain tasks with descriptions, files, and acceptance criteria. Flexible format — Kimi parses what you give it:

```markdown
### TASK-001: Add user authentication middleware
- files: [src/middleware/auth.ts, tests/auth.test.ts]
- depends_on: []
- acceptance: JWT validation returns 401 for expired tokens, 403 for invalid roles

### TASK-002: Create user profile API endpoints  
- files: [src/routes/profile.ts, tests/profile.test.ts]
- depends_on: [TASK-001]
- acceptance: GET /profile returns user data, PATCH /profile updates fields
```

Or simpler:
```
1. Add auth middleware (src/middleware/auth.ts) — validate JWT, return 401/403
2. Profile API endpoints (src/routes/profile.ts) — GET and PATCH, depends on auth
3. Settings page (src/pages/settings.tsx) — form with save, independent of 1-2
```

## Examples

```
/kimi:sprint ./docs/sprint-plan.md
/kimi:sprint ./tasks.md --no-eval
/kimi:sprint "1. Add input validation to all API routes 2. Add rate limiting middleware 3. Add request logging"
```

## How it works

1. Parses the task plan, identifies dependencies and parallelizable batches
2. Reads codebase for conventions (AGENTS.md, testing framework, patterns)
3. For each batch of independent tasks:
   - Dispatches generator subagents in parallel (TDD: failing tests → minimal code)
   - Dispatches evaluator subagent to verify each task (6-point checklist)
   - On rejection: generator retries with feedback (up to 3 rounds)
4. Runs full test suite after each batch
5. Returns structured results with per-task status

## Output

Returns a JSON object with:
- `status`: "complete" or "partial"
- `stats`: Tasks complete/failed/skipped, agents used, evaluation rounds
- `tasks`: Per-task detail (status, files changed, evaluation verdict)
- `test_results`: Final test suite pass/fail
- `files_changed`: All modified files

## Notes

- Generator follows TDD: failing tests first, then minimal code
- Evaluator checks: black-box tests, no test-only paths, no silent errors, scope compliance, criteria coverage, tests pass
- Independent tasks parallelize via Agent Swarm
- Failed tasks don't block independent work (only block dependents)
- Use `--no-eval` for speed when you trust the plan and will review yourself
