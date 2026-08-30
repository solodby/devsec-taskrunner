# DevSec Taskrunner — voiceover script (English)

Source video: `Documents/Screen Recording 2026-08-30 at 22.22.16.mov`  
Muxed output: `Documents/DevSec-Taskrunner-demo-with-VO.mov`  
Voice: macOS Samantha (en_US)

---

## Slide 1 — 0:00–0:16

DevSec Taskrunner. A security review that ends as a saved report — not another chat. Built with Gemini 3.5 Flash, Google ADK, and Cloud Run, for the Taskmaster track.

## Slide 2 — 0:17–0:32

Before merge, reviews still burn time. Secrets hide in diffs. Scanners dump noise. Chat advice disappears. Nothing attaches to the change request.

## Slide 3 — 0:33–0:47

One chore. Four steps. Gather the diff. Scan with git, gitleaks, and semgrep. Decide severity. Persist a Markdown report you can attach.

## Slide 4 — 0:48–1:05

In the live demo, paste a risky change. Get a ranked findings table — file, severity, fix. Then the agent saves the report. The task is finished.

## Slide 5 — 1:06–1:22

It runs on Google Cloud. Cloud Run hosts the agent. Optional Cloud Storage keeps the reports. Same workflow — deployed, not just local.

## Slide 6 — 1:23–1:38

Stack: ADK, Gemini 3.5 Flash, Cloud Run, scanners. DevSec Taskrunner finishes the review as a file — ready for the MR. Thanks for watching.
