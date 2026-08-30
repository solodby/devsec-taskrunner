# Architecture — PR Security Reviewer

## Overview

Taskmaster-style agent: multi-step security review that ends in a persisted report artifact, not only chat text.

```text
┌──────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│ Operator     │────▶│ ADK API / Web UI    │────▶│ Gemini 3.5 Flash │
│ (diff / path)│     │ (local or Cloud Run)│     │ (reasoning)      │
└──────────────┘     └─────────┬───────────┘     └────────┬─────────┘
                               │ tool calls               │
                               ▼                          │
                    ┌──────────────────────┐              │
                    │ Tools                │◀─────────────┘
                    │ • get_git_diff       │
                    │ • gitleaks           │
                    │ • semgrep            │
                    │ • save_security_     │
                    │   report             │
                    └──────────┬───────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     ┌──────────────────┐           ┌────────────────────┐
     │ Local reports/   │           │ GCS bucket         │
     │ *.md artifacts   │           │ (optional)         │
     └──────────────────┘           └────────────────────┘
```

## Runtime options

| Mode | Command | GCP service |
| --- | --- | --- |
| Local UI | `adk web` | none (dev) |
| Local API | `adk api_server` | none (dev) |
| Production | `adk deploy cloud_run` | **Cloud Run** (+ optional GCS) |

## Data flow (happy path)

1. User sends pasted diff or repo path.
2. Agent optionally runs scanners.
3. Agent produces Findings table + verdict.
4. Agent calls `save_security_report` → Markdown file (+ GCS upload when configured).
5. User receives chat summary and artifact path / `gs://` URI.

## Security boundaries

- No exploit payloads in instruction.
- Secrets stay in `.env` / Cloud Run env / Secret Manager (not in git).
- Report files may contain finding descriptions; do not commit real production secrets into `reports/`.
