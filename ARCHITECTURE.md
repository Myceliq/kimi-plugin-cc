# Architecture -- Kimi Plugin for Claude Code

## Overview

A Claude Code plugin that delegates swarm-parallel and visual tasks to Kimi K2.5 via the Kimi CLI. The companion script (`kimi-companion.py`) is the single runtime entry point.

## Directory Structure

```
kimi-plugin-cc/
  .claude-plugin/
    plugin.json              # Plugin metadata (name: "kimi", v1.0.0)
    marketplace.json         # Marketplace listing
  skills/
    kimi-cli-runtime/SKILL.md    # Internal: companion script contract
    kimi-result-handling/SKILL.md # Internal: output presentation rules
  agents/
    rescuer.yaml             # Kimi CLI agent YAML: single-agent task delegation
    rescuer-system.md        # System prompt: diagnose/fix/research
  commands/
    status.md                # /kimi:status -- passthrough to companion
    result.md                # /kimi:result -- passthrough to companion
    cancel.md                # /kimi:cancel -- passthrough to companion
    rescue.md                # /kimi:rescue -- delegates to rescuer agent
  scripts/
    kimi-companion.py        # Main entry point -- subcommand dispatcher
    lib/
      __init__.py
      state.py               # Job state management (CRUD, directory resolution, ID generation)
      kimi_cli.py            # Kimi CLI invocation, JSONL parsing, background jobs
  hooks/
    hooks.json               # SessionStart/SessionEnd lifecycle hooks
  tests/
    test_task001_scaffolding.py  # Plugin metadata and directory structure
    test_task002_companion_core.py # Entry point, state, status/result/cancel
    test_task003_kimi_cli.py     # Kimi CLI module, JSONL parsing, agent configs
    test_task004_hooks.py        # Session lifecycle hooks
    test_task005_rescuer.py      # Rescuer agent, command, and integration
```

## Companion Script (`scripts/kimi-companion.py`)

Entry point for all Kimi plugin operations. Routes subcommands:

- **`status [job-id] [--wait] [--timeout-ms] [--all]`** -- List or query jobs. Returns JSON to stdout.
- **`result [job-id]`** -- Fetch output of completed job. Returns stored output JSON.
- **`cancel [job-id]`** -- Terminate running job (SIGTERM, waits up to 30s, then SIGKILL). Updates state to cancelled.
- **`rescue <task>`** -- Delegate task to rescuer agent via Kimi CLI.
- **`session-start`** -- Hook handler: sets KIMI_COMPANION_SESSION_ID via CLAUDE_ENV_FILE.
- **`session-end`** -- Hook handler: terminates running jobs for the session.
- **Agent stubs** (`research`, `review`, `review-ui`, `build-ui`, `audit`) -- Wired to generic handler; error until agent YAMLs are created.

Error convention: stderr for errors, stdout for structured JSON, exit code 1 for failures.

## Kimi CLI Module (`scripts/lib/kimi_cli.py`)

- **`build_kimi_command()`** -- Constructs CLI args: `kimi --print --agent-file <yaml> --output-format stream-json -p <prompt>`. No `--work-dir` flag (not supported).
- **`parse_jsonl_stream()`** -- Parses JSONL output, extracts last assistant message content.
- **`run_foreground()`** -- Blocks until completion, returns exit_code + parsed output.
- **`run_background()`** -- Spawns detached process, returns PID immediately.
- **`resolve_agent_file()`** -- Maps command name to agent YAML path under `agents/`.
- **`AGENT_CONFIGS`** -- Maps command names to agent YAML files and default modes.

## State Management (`scripts/lib/state.py`)

- **Directory resolution:** Uses `CLAUDE_PLUGIN_DATA/state/` when available, falls back to `$TMPDIR/kimi-companion/state/`.
- **Job ID format:** `<prefix>-<hex_timestamp>-<random6>` (e.g., `rescue-195a3b2c400-k8m2nq`).
- **Per-job files:** Each job is a separate JSON file (`<job_id>.json`) in the state directory.
- **Operations:** `write_job`, `read_job`, `list_jobs` (with active/all/session filtering), `delete_job`.

## Session Lifecycle (`hooks/hooks.json`)

- **SessionStart:** Invokes `kimi-companion.py session-start`, reads session context from stdin, sets `KIMI_COMPANION_SESSION_ID` env var.
- **SessionEnd:** Invokes `kimi-companion.py session-end`, terminates running jobs for the session, marks them as cancelled.
- Timeout: 5 seconds per hook.

## Agents

### Rescuer (`agents/rescuer.yaml`)

Single-agent task delegation. No subagents, no Agent tool. Tools: ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep, SearchWeb, FetchURL. Output: `{status, summary, files_changed, remaining_issues}`.

## Commands (User-Facing)

- **status/result/cancel** -- `disable-model-invocation: true`, direct passthrough via `Bash(python3:*)`.
- **rescue** -- `context: fork`, routes to rescuer agent.

## Key Decisions

1. **Python stdlib only** -- No external dependencies. Uses `subprocess`, `json`, `pathlib`, `signal`, `os`, `time`, `random`, `string`.
2. **Commands vs Skills convention** -- User-facing slash commands in `commands/`, internal skills in `skills/`. Follows Codex/Gemini plugin pattern.
3. **No `--work-dir` flag** -- Working directory set via subprocess `cwd` (Kimi CLI does not support `--work-dir`).
4. **No `CreateSubagent`** -- All subagent launching uses `kimi_cli.tools.agent:Agent` (v1.31.0 compatible).
5. **Agent configs centralized** -- `AGENT_CONFIGS` dict in `kimi_cli.py` maps command names to YAML files and default modes.
6. **Session lifecycle hooks** -- SessionStart/End hooks manage session ID and job cleanup.
