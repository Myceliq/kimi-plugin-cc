---
description: Build UI components from a design image reference
argument-hint: <image> <prompt>
context: fork
allowed-tools: ReadFile, WriteFile, StrReplaceFile, Shell, Glob, Grep
---

# /kimi:build-ui

Build UI components that match a design reference image.

## Usage

```
/kimi:build-ui <image-path> <description-of-what-to-build>
```

## Arguments

- `image-path`: Path to the reference image (PNG, JPG, or other image format)
- `description`: Text description of what to build (e.g., "Build a login form matching this design")

## Example

```
/kimi:build-ui ./designs/login-mockup.png "Create a login page with email/password fields and social login buttons"
```

## How it works

1. The visual-builder agent analyzes the reference image to identify layout, colors, typography, and components
2. Detects your project stack and follows existing conventions
3. Builds matching UI components
4. Captures screenshots and compares to the reference
5. Iterates up to 5 times to improve the match
6. Returns the final result with file paths and any remaining gaps

## Output

Returns a JSON object with:
- `status`: "complete" or "partial"
- `summary`: Description of what was built
- `files_changed`: List of created/modified files
- `remaining_issues`: Any gaps that couldn't be resolved
- `screenshots`: Paths to reference and captured screenshots

## Notes

- Screenshots are captured from localhost only (security constraint)
- Your project must have a startable dev server
- The agent follows your existing project conventions and stack
