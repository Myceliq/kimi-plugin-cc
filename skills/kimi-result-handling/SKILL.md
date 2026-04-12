---
name: kimi-result-handling
description: Internal guidance for presenting Kimi helper output back to the user
user-invocable: false
---

# Kimi Result Handling

When the helper returns Kimi output, follow these presentation rules.

## Verdict and Summary

- Preserve the helper's verdict, summary, findings, and next steps structure.
- Always show the verdict (`approve` or `needs-attention`) prominently.
- Present the summary paragraph before detailed findings.

## Findings Presentation

- Order findings by severity: critical first, then high, medium, low.
- Group by category when multiple categories are present.
- Include file:line citations exactly as returned — do not truncate.
- Show the perspective label (e.g., "Security", "Performance") when available.
- Include confidence scores when present.

## Fix Recommendations

- Present recommendations as suggestions, never auto-apply fixes.
- Do not modify files based on findings without explicit user approval.
- When the user asks to apply a fix, confirm which specific finding before proceeding.

## Visual Results

- For screenshot paths, display the path so the user can open the file.
- Describe key visual findings in text alongside screenshot references.
- For before/after comparisons, show both paths clearly labeled.

## Audit Results

- Show the executive summary and stats (files_analyzed, agents_used, findings_total) first.
- Present the by_category breakdown as an overview before detailed findings.
- Detailed audit findings should be shown on request or for critical/high severity.
- For large audits, summarize by category and offer to drill into specifics.

## Error and Uncertainty Handling

- If the helper returns an error status, surface the error message clearly.
- If findings have low confidence (< 0.5), note this when presenting.
- Do not suppress or hide uncertain findings — present them with appropriate caveats.
- For retryable errors (exit code 75), suggest the user retry.
