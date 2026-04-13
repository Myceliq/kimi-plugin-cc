---
description: Build a UI from a reference image using iterative visual comparison
argument-hint: '[--background|--wait] <image path or description>'
context: fork
allowed-tools: Bash(python3:*), Bash(*:curl), Bash(*:npm), Bash(*:node), ReadFile, WriteFile, StrReplaceFile, Shell
---

Route this request to the `kimi:build-ui` subagent.
