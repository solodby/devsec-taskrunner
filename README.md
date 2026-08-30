# DevSec Taskrunner

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

## Reproducible Testing instructions

These steps reproduce a full review → save-report run on a clean machine.

### Prerequisites

- Python 3.11+ (3.12/3.14 also works)
- macOS/Linux recommended
- Gemini API key **or** Vertex AI credentials in a supported region
- Optional: [gitleaks](https://github.com/gitleaks/gitleaks), [semgrep](https://semgrep.dev/)

### 1. Clone and install

```bash
git clone https://github.com/solodby/devsec-taskrunner.git
cd devsec-taskrunner
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp solodby_agent/.env.example solodby_agent/.env
# Edit solodby_agent/.env:
#   GOOGLE_GENAI_USE_ENTERPRISE=0
#   GOOGLE_API_KEY=<your-key>
```

Do not commit `.env`.

### 3. Optional scanners

```bash
brew install gitleaks    # secret scan tool
brew install semgrep     # optional SAST; agent continues if missing
```

### 4. Smoke test (CLI, ~30s)

```bash
source .venv/bin/activate
adk run solodby_agent 'Review this diff and save a report:

+ query = f"SELECT * FROM users WHERE id = {user_id}"'
```

**Expected:**

- Verdict includes SQL injection / CWE-89 style finding
- Agent calls `save_security_report`
- New file appears under `solodby_agent/reports/*.md`

```bash
ls solodby_agent/reports/
```

### 5. Interactive UI

```bash
adk web
```

Open http://127.0.0.1:8000 → select `solodby_agent` → paste a demo prompt below.

### 6. API server (optional)

```bash
adk api_server --auto_create_session .
# POST http://127.0.0.1:8000/run with app_name=solodby_agent
```

### Demo prompts

```text
Review this diff and save a report:

+ query = f"SELECT * FROM users WHERE id = {user_id}"
```

```text
Full workflow for /absolute/path/to/a/git/repo:
1) uncommitted git diff
2) gitleaks working tree
3) save security report with verdict
```

### Pass / fail checklist

| Check | Pass if |
| --- | --- |
| Agent loads | `adk run` / `adk web` starts without import errors |
| Diff review | Findings table with severity + recommendation |
| Action | `reports/*.md` created after review |
| Tool degrade | Without semgrep, review still completes |

### Hosted test (Cloud Run)

If a Cloud Run URL is listed on the Devpost project page, open it and run the same pasted-diff prompt. Cloud Run cannot read your laptop filesystem — use **pasted diffs** for hosted testing.

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
