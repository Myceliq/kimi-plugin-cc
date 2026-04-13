---
description: Show active and recent Kimi jobs for this repository
argument-hint: '[job-id] [--wait] [--timeout-ms <ms>] [--all]'
disable-model-invocation: true
allowed-tools: Bash(python3:*)
---

!`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kimi-companion.py" status $ARGUMENTS`
