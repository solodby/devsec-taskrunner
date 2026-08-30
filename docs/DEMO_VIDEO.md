# Demo video checklist (~3–4 min) — All Things Agentic Hackathon / Taskmaster
#
# Record: screen + voice. Show Cloud Run Console URL clearly.

## Script

1. Problem (20s)
   - Manual PR security review is slow; secrets/SQL issues slip through.

2. Value (20s)
   - Agent runs a workflow: gather → analyze → save durable report (action).

3. Live demo local OR Cloud Run UI (90–120s)
   - Paste SQL injection diff → Findings table → report path shown.
   - Optional: gitleaks on a sample folder (no real secrets on camera).

4. Proof of Google Cloud (30–40s) — REQUIRED
   - Cloud Console → Cloud Run → service `pr-security-reviewer` Running.
   - Open service URL (.run.app) in browser.
   - Optional: GCS bucket object for a saved report.

5. Close (15s)
   - Stack: Gemini 3.5 Flash + ADK + Cloud Run (+ GCS).
   - Repo + README for spin-up.

## Before recording

- [ ] Cloud Run deploy succeeded
- [ ] Sample prompt ready (no real production secrets)
- [ ] Architecture diagram open from docs/architecture.md
- [ ] Video public (YouTube unlisted OK only if rules allow; prefer public)
