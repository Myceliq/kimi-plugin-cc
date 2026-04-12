---
name: kimi-cli-runtime
description: Internal helper contract for calling the kimi-companion runtime from Claude Code
user-invocable: false
---

# Kimi CLI Runtime

Use this skill only inside Kimi plugin agents and commands.

## Primary Helper

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kimi-companion.py" <command> [args]
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_PLUGIN_ROOT` | Absolute path to plugin directory (set by Claude Code) |
| `KIMI_PLUGIN_ROOT` | Alias for `CLAUDE_PLUGIN_ROOT` (set by companion for clarity) |
| `CLAUDE_PLUGIN_DATA` | Writable state directory for plugin data |
| `KIMI_COMPANION_SESSION_ID` | Session ID for job tracking and cleanup (set by SessionStart hook) |
| `CLAUDE_ENV_FILE` | File path for appending env vars during hooks |

## Subcommands

| Command | Description |
|---------|-------------|
| `research <prompt>` | Parallel multi-agent research |
| `review [--scope] [--focus]` | Multi-perspective code review |
| `review-ui <url-or-image>` | Visual/UX review via screenshots |
| `build-ui <image> <prompt>` | Visual-to-code with verification loop |
| `rescue <task>` | Delegate task to K2.5 |
| `audit [--focus]` | Full codebase audit |
| `status [job-id]` | List active/recent jobs |
| `result [job-id]` | Fetch stored output for completed job |
| `cancel [job-id]` | Terminate running job |
| `session-start` | Initialize session (called by hook) |
| `session-end` | Cleanup session (called by hook) |

## Argument Parsing

- Flags use `--flag` or `--flag value` format
- Positional arguments follow the subcommand
- `--wait` forces foreground (blocking) execution
- `--background` forces background (detached) execution

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Non-retryable failure (bad arguments, missing files, runtime errors) |
| `75` | Retryable failure (rate limits, server errors, timeouts) |

All errors are written to stderr. Structured output is written to stdout as JSON.
