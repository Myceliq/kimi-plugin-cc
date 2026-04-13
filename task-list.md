# Task List — Kimi Plugin for Claude Code

## Notes for Evaluators

**Key research findings that affect implementation:**
- `kimi_cli.tools.multiagent:CreateSubagent` does **not exist** in Kimi CLI v1.31.0. All subagent launching uses `kimi_cli.tools.agent:Agent` with the `subagent_type` parameter. Agent YAMLs should use the `subagents` block for pre-defined subagents.
- The `--work-dir` flag does not exist in Kimi CLI print mode. Working directory must be set via subprocess `cwd` argument.
- Established plugin convention: user-facing slash commands go in `commands/*.md`, internal non-user-invocable skills go in `skills/*/SKILL.md`. The spec puts everything under `skills/` but implementation should follow the Codex/Gemini convention.
- Subagent YAML format should follow the working harness examples (`name`, `type`, `agent_file`) rather than the raw Pydantic model (`path`, `description`).
- The companion script is Python (per spec), unlike the Node.js companions in Codex and Gemini plugins.
- Enterprise multi-session audit (v2) is explicitly deferred — single-session 100-agent audit only.

---

### TASK-001: Plugin metadata, internal skills, and project scaffolding
- status: complete
- depends_on: []
- checkpoint: false
- files: [.claude-plugin/plugin.json, .claude-plugin/marketplace.json, skills/kimi-cli-runtime/SKILL.md, skills/kimi-result-handling/SKILL.md, .gitignore]
- acceptance:
  - `.claude-plugin/plugin.json` exists with `name: "kimi"`, version, description, author fields matching the Codex/Gemini plugin metadata format
  - `.claude-plugin/marketplace.json` exists with correct marketplace structure (name, owner, plugins array with source pointing to `./`)
  - `skills/kimi-cli-runtime/SKILL.md` exists with frontmatter `user-invocable: false` and documents the companion script contract: invocation path (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kimi-companion.py" <command>`), environment variables (`KIMI_PLUGIN_ROOT` as alias for `CLAUDE_PLUGIN_ROOT`, `KIMI_COMPANION_SESSION_ID`), exit code conventions, and argument parsing patterns
  - `skills/kimi-result-handling/SKILL.md` exists with frontmatter `user-invocable: false` and documents output presentation rules: verdict/summary/findings severity ordering, no auto-apply of fixes, visual result handling (screenshot paths), audit result display (executive summary first), error/uncertainty handling
  - `.gitignore` includes `.kimi-jobs/`, `.env`, and appropriate Python artifacts (`__pycache__/`, `*.pyc`)
  - All directory structure matches the target layout from the spec (adjusted for commands/ vs skills/ convention)
- docs_reference: research-brief.md#plugin-metadata-format-pluginjson, research-brief.md#marketplace-metadata-format-marketplacejson, research-brief.md#skill-definition-format-skillmd

### TASK-002: Companion script entry point and state management library
- status: complete
- depends_on: [TASK-001]
- checkpoint: false
- files: [scripts/kimi-companion.py, scripts/lib/__init__.py, scripts/lib/state.py]
- acceptance:
  - `scripts/kimi-companion.py` is a valid Python 3 script with a subcommand dispatcher that routes to `status`, `result`, `cancel` (and stubs for agent subcommands that error with "not yet implemented")
  - `scripts/lib/state.py` implements: job state directory resolution (using `CLAUDE_PLUGIN_DATA` env var with a fallback), job ID generation (prefix + timestamp + random), read/write/list/delete operations on per-job JSON files, job state schema matching spec (job_id, agent, status, started_at, pid, args, completed_at, output)
  - `status` subcommand: no args lists active/recent jobs; with job-id shows details; `--wait` blocks until job completes; `--timeout-ms` limits wait time; `--all` includes completed/cancelled jobs. Output is valid JSON to stdout.
  - `result` subcommand: no args returns most recently completed job's output; with job-id returns that job's output. Output is the stored job output JSON to stdout.
  - `cancel` subcommand: no args cancels most recently started job; with job-id cancels that job. Sends SIGTERM, waits up to 30s, then SIGKILL. Updates job status to `cancelled`. Returns confirmation JSON to stdout.
  - All companion script errors write to stderr and exit with code 1
  - No external Python dependencies required — stdlib only
- docs_reference: research-brief.md#codex-state-management-more-sophisticated, research-brief.md#codex-job-tracking-pattern, research-brief.md#environment-variables

### TASK-002B: Job management command definitions
- status: complete
- depends_on: [TASK-002]
- checkpoint: false
- files: [commands/status.md, commands/result.md, commands/cancel.md]
- acceptance:
  - `commands/status.md` has frontmatter with `disable-model-invocation: true`, `allowed-tools: Bash(python3:*)`, correct `argument-hint`, and passthrough invocation of the companion
  - `commands/result.md` has same passthrough pattern as status
  - `commands/cancel.md` has same passthrough pattern as status
- docs_reference: research-brief.md#command-definition-format-commandsmd

### TASK-003: Companion script — Kimi CLI invocation, JSONL parsing, and background job support
- status: complete
- depends_on: [TASK-002B]
- checkpoint: false
- files: [scripts/lib/kimi_cli.py, scripts/kimi-companion.py, scripts/lib/state.py]
- acceptance:
  - `scripts/lib/kimi_cli.py` implements: spawning the `kimi` CLI process in print mode with `--print`, `--agent-file`, `--output-format stream-json`, and `-p` flags; working directory set via subprocess `cwd` (not `--work-dir`)
  - Foreground mode (`--wait`): blocks, streams JSONL output, parses the final assistant message, returns structured result
  - Background mode: spawns a detached subprocess, returns job ID immediately, stores PID in job state for later cancellation
  - JSONL stream parsing: reads line-by-line, extracts the final assistant message content as the structured result
  - Exit code handling: 0 = success, 1 = non-retryable failure, 75 = retryable failure (surfaced differently to user)
  - The companion main script gains a generic `run_agent` handler that: resolves agent YAML path relative to plugin root, constructs prompt from subcommand args, selects foreground/background mode, invokes kimi_cli, and stores result via state module
  - Agent subcommand stubs from TASK-002 are wired to use the generic handler (but still error until agent YAMLs exist)
  - No external Python dependencies — uses subprocess, json, and pathlib from stdlib
- docs_reference: research-brief.md#kimi-cli-print-mode, research-brief.md#codex-background-task-pattern, research-brief.md#no---work-dir-flag-in-current-kimi-cli

### TASK-004: Session lifecycle hooks
- status: pending
- depends_on: [TASK-002B]
- checkpoint: false
- files: [hooks/hooks.json, scripts/kimi-companion.py, scripts/lib/state.py]
- acceptance:
  - `hooks/hooks.json` exists with valid structure matching the Codex hooks format: `SessionStart` and `SessionEnd` events, each invoking the companion script with the appropriate lifecycle subcommand
  - SessionStart handler: reads session context from stdin JSON (session_id, cwd, hook_event_name), sets `KIMI_COMPANION_SESSION_ID` via `CLAUDE_ENV_FILE` append pattern, initializes session state
  - SessionEnd handler: reads session context from stdin JSON, terminates any running Kimi jobs associated with the session (via stored PIDs), cleans up stale job files, exits cleanly
  - Hook timeout is set to 5 seconds (matching Codex convention)
  - `kimi-companion.py` gains `session-start` and `session-end` subcommands that implement the above
  - State module gains session-aware job querying (filter jobs by session ID)
- docs_reference: research-brief.md#hooks-format-hooksjson, research-brief.md#environment-variables

### TASK-005: Rescuer agent, rescue command, and companion handler — first end-to-end agent slice
- status: pending
- depends_on: [TASK-003]
- checkpoint: true
- files: [agents/rescuer.yaml, agents/rescuer-system.md, commands/rescue.md, scripts/kimi-companion.py]
- acceptance:
  - `agents/rescuer.yaml` is valid Kimi CLI agent YAML (version 1) with: `name: rescuer`, `system_prompt_path: ./rescuer-system.md`, tools list including ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep, SearchWeb, FetchURL (all using full `kimi_cli.tools.*` module paths), no subagents (single-agent)
  - `agents/rescuer-system.md` is the system prompt instructing the agent to: read AGENTS.md/CLAUDE.md if present for project conventions, work the given task (diagnose, implement, or research), and return structured JSON output matching the simple result schema (status, summary, files_changed, remaining_issues)
  - `commands/rescue.md` has frontmatter with: description, `argument-hint` showing `[--background|--wait] <task description>`, `context: fork` routing to the agent, appropriate `allowed-tools`
  - `rescue` subcommand in companion: parses task description from args, defaults to `--wait` (foreground), invokes rescuer agent YAML, passes task as prompt, stores and returns structured result
  - Running `/kimi:rescue "some task"` end-to-end: invokes companion, companion spawns kimi CLI with rescuer agent, result is stored in job state, output returned to Claude
  - Error cases handled: missing task description exits with error message; kimi CLI failure produces a failed job record
- docs_reference: research-brief.md#verified-format-from-installed-kimi-cli-source, research-brief.md#working-yaml-examples-from-kimi-swarm-harness, research-brief.md#command-definition-format-commandsmd, research-brief.md#available-tool-module-paths-verified-from-kimi-cli-v1310-source

### TASK-006: Visual builder agent and build-ui command
- status: pending
- depends_on: [TASK-003]
- checkpoint: false
- files: [agents/visual-builder.yaml, agents/visual-builder-system.md, commands/build-ui.md, scripts/kimi-companion.py]
- acceptance:
  - `agents/visual-builder.yaml` is valid Kimi CLI agent YAML with: `name: visual-builder`, tools including ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep (no Agent tool — single agent, no subagents)
  - `agents/visual-builder-system.md` instructs the agent through the 6-step visual round-trip flow: Analyze (read input image via MoonViT, identify layout/spacing/colors/typography/elements), Build (detect project stack, follow conventions, write components), Screenshot (start dev server if needed, capture at matching viewport), Compare (vision-compare screenshot to input), Iterate (up to 5 rounds fixing discrepancies), Return (structured output: files_changed, before/after screenshot paths, remaining gaps)
  - System prompt specifies constraints: only builds against existing project stack, dev server must be startable, screenshots localhost only
  - `commands/build-ui.md` has: description, `argument-hint` showing `<image> <prompt>`, `context: fork`, appropriate `allowed-tools`
  - `build-ui` subcommand in companion: parses image path and text prompt, defaults to `--wait` (foreground), validates image path exists, invokes visual-builder agent, returns structured result with simple schema (status, summary, files_changed, remaining_issues, screenshots)
- docs_reference: research-brief.md#verified-format-from-installed-kimi-cli-source, research-brief.md#available-tool-module-paths-verified-from-kimi-cli-v1310-source, research-brief.md#command-definition-format-commandsmd

### TASK-007: Swarm reviewer agent and swarm-review command
- status: pending
- depends_on: [TASK-003]
- checkpoint: false
- files: [agents/swarm-reviewer.yaml, agents/swarm-reviewer-system.md, commands/swarm-review.md, scripts/kimi-companion.py]
- acceptance:
  - `agents/swarm-reviewer.yaml` is valid Kimi CLI agent YAML with: `name: swarm-reviewer`, tools including Agent, ReadFile, Glob, Grep (root agent that launches subagents)
  - Agent YAML does NOT include `kimi_cli.tools.multiagent:CreateSubagent` (confirmed non-existent in v1.31.0); uses `kimi_cli.tools.agent:Agent` exclusively for subagent dispatch
  - `agents/swarm-reviewer-system.md` instructs the root agent to: receive a diff, dispatch 4 parallel `explore`-type subagents (Security, Performance, Correctness, Maintainability — each with its specific review criteria from the spec), collect results, deduplicate, rank by severity, and produce consolidated output matching the findings JSON schema (verdict, summary, findings with severity/category/perspective/title/body/file/line_start/line_end/confidence/recommendation, next_steps)
  - System prompt defines each perspective's focus areas as specified in the spec
  - `commands/swarm-review.md` has: description, `argument-hint` showing `[--scope auto|working-tree|branch] [--base <ref>] [--focus <perspectives>]`, `context: fork`, appropriate `allowed-tools`
  - `review` subcommand in companion: parses `--scope`, `--base`, `--focus` args; collects git diff based on scope (working-tree = `git diff`, branch = `git diff <base>...HEAD`, auto = detect); defaults to `--background`; passes diff as part of the prompt to the agent; stores structured result
- docs_reference: research-brief.md#verified-format-from-installed-kimi-cli-source, research-brief.md#agent-tool-parameters, research-brief.md#built-in-subagent-types, research-brief.md#kimi_clitools.multiagentcreatesubagent-does-not-exist, research-brief.md#codex-review-output-schema-json-schema

### TASK-008: Swarm researcher agent and swarm-research command
- status: pending
- depends_on: [TASK-003]
- checkpoint: false
- files: [agents/swarm-researcher.yaml, agents/swarm-researcher-system.md, commands/swarm-research.md, scripts/kimi-companion.py]
- acceptance:
  - `agents/swarm-researcher.yaml` is valid Kimi CLI agent YAML with: `name: swarm-researcher`, tools including Agent, ReadFile, Shell, Glob, Grep, SearchWeb, FetchURL (root agent that launches subagents)
  - Agent YAML does NOT include `kimi_cli.tools.multiagent:CreateSubagent`; uses `kimi_cli.tools.agent:Agent` for subagent dispatch
  - `agents/swarm-researcher-system.md` instructs the root agent to: analyze the research question, decompose into 3-10 independent work packages (different angles: codebase patterns, external docs, git history, similar implementations, edge cases), dispatch parallel `explore`-type subagents via `run_in_background=true`, collect results, synthesize into a single cited brief with `file:line` citations
  - `commands/swarm-research.md` has: description, `argument-hint` showing `[--wait] <research question>`, `context: fork`, appropriate `allowed-tools`
  - `research` subcommand in companion: parses research question from args, defaults to `--background`, invokes swarm-researcher agent, stores structured result with findings schema (verdict, summary, findings with citations, next_steps)
- docs_reference: research-brief.md#verified-format-from-installed-kimi-cli-source, research-brief.md#agent-tool-parameters, research-brief.md#built-in-subagent-types, research-brief.md#kimi_clitools.multiagentcreatesubagent-does-not-exist

### TASK-009: Review-UI agent and review-ui command
- status: pending
- depends_on: [TASK-003]
- checkpoint: true
- files: [agents/review-ui.yaml, agents/review-ui-system.md, commands/review-ui.md, scripts/kimi-companion.py]
- acceptance:
  - `agents/review-ui.yaml` is valid Kimi CLI agent YAML with: `name: review-ui`, tools including Agent, ReadFile, Shell, Glob (root agent that launches visual reviewer subagents)
  - `agents/review-ui-system.md` instructs the root agent to: accept a URL or image path; if URL, screenshot at multiple viewport widths (mobile 375px, tablet 768px, desktop 1440px) using Shell; if image, use directly; dispatch 4 parallel `explore`-type subagents (Visual polish, Accessibility, Responsiveness, UX heuristics — each with specific criteria from the spec); each reviewer analyzes screenshots via K2.5 MoonViT vision; root consolidates findings with severity and screenshot references
  - System prompt defines each visual perspective's criteria as specified in the spec
  - `commands/review-ui.md` has: description, `argument-hint` showing `<url-or-image> [--focus <perspectives>]`, `context: fork`, appropriate `allowed-tools`
  - `review-ui` subcommand in companion: parses URL or image path from args, parses `--focus` flag, validates localhost-only for URLs, defaults to `--background`, invokes review-ui agent, stores structured result with findings schema including screenshots array
- docs_reference: research-brief.md#verified-format-from-installed-kimi-cli-source, research-brief.md#agent-tool-parameters, research-brief.md#built-in-subagent-types

### TASK-010: Audit coordinator agent and audit command
- status: pending
- depends_on: [TASK-003]
- checkpoint: true
- files: [agents/audit-coordinator.yaml, agents/audit-coordinator-system.md, commands/audit.md, scripts/kimi-companion.py]
- acceptance:
  - `agents/audit-coordinator.yaml` is valid Kimi CLI agent YAML with: `name: audit-coordinator`, tools including Agent, ReadFile, Glob, Grep (root agent that launches up to 100 subagents)
  - Agent YAML does NOT include `kimi_cli.tools.multiagent:CreateSubagent`; uses `kimi_cli.tools.agent:Agent` for subagent dispatch
  - `agents/audit-coordinator-system.md` instructs the root agent through the 4-phase audit flow: Catalog (glob all source files, exclude node_modules/.git/build artifacts/vendored deps, group by domain/module), Partition (divide into work packages by module cohesion following the scaling table from the spec — ~5 files/agent for small codebases up to ~200 files/agent for 10K+ codebases), Dispatch (`explore`-type subagents that fully read every file in their package and evaluate against configured focus areas), Synthesize (deduplicate, rank by severity, group by category, produce executive summary + detailed findings)
  - System prompt defines the 7 default focus areas from the spec: security vulnerabilities, dead code/unused exports, naming/pattern inconsistencies, missing error handling, test coverage gaps, dependency issues, documentation staleness
  - Output matches the audit JSON schema from the spec: summary, stats (files_analyzed, agents_used, findings_total), findings array, by_category breakdown
  - `commands/audit.md` has: description, `argument-hint` showing `[--focus <categories>]`, `context: fork`, appropriate `allowed-tools`
  - `audit` subcommand in companion: parses `--focus` args, always defaults to `--background`, invokes audit-coordinator agent, stores structured result
  - Enterprise multi-session audit (v2 `--enterprise` flag) is NOT implemented — this is explicitly deferred per spec
- docs_reference: research-brief.md#verified-format-from-installed-kimi-cli-source, research-brief.md#agent-tool-parameters, research-brief.md#built-in-subagent-types, research-brief.md#kimi_clitools.multiagentcreatesubagent-does-not-exist
