---
description: Review a UI for visual polish, accessibility, responsiveness, and UX
argument-hint: <url-or-image> [--focus <perspectives>]
context: fork
allowed-tools: ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep
---

# /kimi:review-ui

Review a web page or design image for visual quality, accessibility, responsiveness, and UX heuristics.

## Usage

```
/kimi:review-ui <url-or-image-path> [--focus <perspectives>]
```

## Arguments

- `url-or-image-path`: Either a localhost URL (e.g., `http://localhost:3000`) or a path to an image file
- `--focus`: Optional comma-separated list of perspectives to focus on (default: all)
  - `visual` — Visual polish (alignment, spacing, typography)
  - `a11y` — Accessibility (contrast, alt text, keyboard nav)
  - `responsive` — Responsiveness (layout at different viewports)
  - `ux` — UX heuristics (navigation, feedback, consistency)

## Examples

```
/kimi:review-ui http://localhost:3000
/kimi:review-ui ./designs/mockup.png --focus visual,a11y
/kimi:review-ui http://localhost:5173 --focus responsive
```

## How it works

1. If a URL is provided, captures screenshots at mobile (375px), tablet (768px), and desktop (1440px) viewports
2. Dispatches 4 parallel subagents, each analyzing from a different perspective
3. Each reviewer uses MoonViT vision to analyze the visual elements
4. Consolidates findings and ranks by severity
5. Returns structured results with screenshot references

## Output

Returns a JSON object with:
- `verdict`: "approved", "approved-with-suggestions", or "changes-requested"
- `summary`: Executive summary of the review
- `findings`: Array of issues found with severity and recommendations
- `screenshots`: Paths to captured screenshots (if URL was provided)
- `next_steps`: Actionable items for the developer

## Notes

- URLs must be localhost only (security constraint)
- Images are analyzed directly without screenshot capture
- Uses K2.5 MoonViT for visual analysis
