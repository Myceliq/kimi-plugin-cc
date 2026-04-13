---
description: Fetch stored output for a completed Kimi job
argument-hint: '[job-id]'
disable-model-invocation: true
allowed-tools: Bash(python3:*)
---

!`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kimi-companion.py" result $ARGUMENTS`
