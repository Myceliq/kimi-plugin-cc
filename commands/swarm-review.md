---
description: Run a multi-perspective code review on the current changes
argument-hint: '[--scope auto|working-tree|branch] [--base <ref>] [--focus <perspectives>]'
context: fork
allowed-tools: Bash(python3:*), Bash(*:git), ReadFile, WriteFile, StrReplaceFile, Shell
---

Route this request to the `kimi:swarm-review` subagent.
