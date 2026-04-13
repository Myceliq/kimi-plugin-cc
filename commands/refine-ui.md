---
description: Refine existing UI based on feedback, a reference image, or review findings
argument-hint: <url> [<reference-image>] [--feedback <text>] [--findings <json-path>]
context: fork
allowed-tools: ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep
---

# /kimi:refine-ui

Take existing UI and make it better — fix spacing, match a design reference, address review findings, or polish based on best practices.

## Usage

```
/kimi:refine-ui <url> [reference-image] [options]
```

## Arguments

- `url`: Localhost URL of the page to refine (e.g., `http://localhost:3000/dashboard`)
- `reference-image`: Optional path to a mockup or design that the UI should match
- `--feedback "<text>"`: Specific issues to fix (e.g., "spacing is off, header should be sticky")
- `--findings <path>`: Path to a JSON file with `/kimi:review-ui` output to address

## Examples

```
/kimi:refine-ui http://localhost:3000 ./mockup.png
/kimi:refine-ui http://localhost:5173/dashboard --feedback "make the sidebar narrower, fix the table alignment"
/kimi:refine-ui http://localhost:3000 --findings /tmp/review-findings.json
/kimi:refine-ui http://localhost:3000
```

## How it works

1. Reads the codebase to understand components, styles, and framework
2. Screenshots the current state ("before")
3. If reference image: compares current vs reference via MoonViT vision
4. If feedback/findings: maps each issue to specific files
5. Implements targeted, surgical fixes (no redesign)
6. Screenshots the result ("after") and verifies visually
7. Iterates up to 3 rounds until improvements are confirmed

## Output

Returns a JSON object with:
- `status`: "complete" or "partial"
- `summary`: What was refined
- `changes`: Array of changes with file paths and reasons
- `files_changed`: List of modified files
- `screenshots`: Before/after screenshot paths + reference if provided

## Notes

- This refines existing UI, not builds from scratch (use `/kimi:build-ui` for that)
- Follows existing project conventions (Tailwind stays Tailwind, CSS modules stay CSS modules)
- Changes are minimal and surgical — no surrounding refactors
- Localhost URLs only
