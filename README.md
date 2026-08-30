# PR Security Reviewer (ADK Taskmaster agent)

Autonomous DevSecOps workflow: review a PR/diff or local repo, then **save a durable security report** (local filesystem and optionally Google Cloud Storage).

Built for the [All Things Agentic Hackathon](https://allthingsagentichackathon.devpost.com/) — track: **Taskmaster**.

## Stack

| Layer | Tech |
| --- | --- |
| Model | Gemini 3.5 Flash |
| Agent framework | Google ADK (`google-adk`) |
| Tools | git diff, gitleaks, semgrep, `save_security_report` |
| Cloud | Cloud Run (API), optional GCS bucket for reports |

## Features

- Pasted unified-diff / snippet review with fixed Findings table
- Local repo scan: `get_git_diff` → gitleaks → semgrep
- **Action step**: `save_security_report` writes Markdown under `solodby_agent/reports/`
- Optional upload to `gs://$REPORTS_GCS_BUCKET/security-reports/`

## Local setup

```bash
cd /path/to/adk-workspace
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# API key (Gemini Developer API)
cp solodby_agent/.env.example solodby_agent/.env
# edit GOOGLE_API_KEY=

# Optional scanners
brew install gitleaks          # required for secret scan tool
brew install semgrep           # optional SAST

adk web
# or: adk run solodby_agent "Review this diff: ..."
# or: adk api_server --auto_create_session .
```

## Demo prompts

```text
Review this diff and save a report:

+ query = f"SELECT * FROM users WHERE id = {user_id}"
```

```text
Full workflow for /path/to/repo:
1) uncommitted git diff
2) gitleaks working tree
3) save security report with verdict
```

## Deploy to Cloud Run

Prerequisites: `gcloud` authenticated, billing-enabled project, APIs enabled.

```bash
# once
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com storage.googleapis.com

# optional reports bucket
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-security-reports
export REPORTS_GCS_BUCKET=YOUR_PROJECT_ID-security-reports

# deploy (ADK packs the agent for Cloud Run)
source .venv/bin/activate
adk deploy cloud_run \
  --project="$GOOGLE_CLOUD_PROJECT" \
  --region=us-central1 \
  --service_name=pr-security-reviewer \
  --with_ui \
  ./solodby_agent
```

Set Cloud Run env vars (Console or `--set-env-vars`):

- `GOOGLE_API_KEY` (or use Vertex / ADC instead)
- `GOOGLE_GENAI_USE_ENTERPRISE=0` for Gemini API key mode
- `REPORTS_GCS_BUCKET=...` (grant Cloud Run SA `roles/storage.objectCreator`)

After deploy, open the Cloud Run URL and capture Console + service URL for the demo video.

Helper script: `./scripts/deploy_cloud_run.sh`.

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Project layout

```text
adk-workspace/
├── requirements.txt
├── scripts/deploy_cloud_run.sh
├── docs/architecture.md
└── solodby_agent/
    ├── agent.py
    ├── .env.example
    ├── reports/
    └── tools/
        ├── review_tools.py
        └── report_tools.py
```

## Notes

- Cloud Run containers do not share your Mac filesystem; prefer pasted diffs or GCS-backed workflows in production.
- Local tools (`git`, `gitleaks`, `semgrep`) are for Mac/CI runners with those binaries installed.
