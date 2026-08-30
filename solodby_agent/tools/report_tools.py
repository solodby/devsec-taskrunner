"""Persist security review reports (local + optional GCS)."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-").lower()
    return slug[:80] or "report"


def save_security_report(
    report_markdown: str,
    subject: str = "security-review",
    verdict: str = "UNKNOWN",
) -> dict:
    """Save a completed security review as a durable artifact.

    Writes a Markdown report under solodby_agent/reports/. When
    REPORTS_GCS_BUCKET is set, also uploads the same file to Google Cloud
    Storage (requires Application Default Credentials / Cloud Run SA).

    Args:
        report_markdown: Full review in Markdown (Summary, Findings table, Next steps).
        subject: Short label for the target (repo name, PR id, or file).
        verdict: PASS, PASS WITH NOTES, or CHANGES REQUESTED.

    Returns:
        Paths and upload status so the agent can confirm the action completed.
    """
    if not report_markdown or not report_markdown.strip():
        return {"status": "error", "message": "report_markdown is empty"}

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{stamp}-{_safe_slug(subject)}-{_safe_slug(verdict)}.md"
    local_path = REPORTS_DIR / filename

    header = (
        f"# Security Review Report\n\n"
        f"- Generated (UTC): {stamp}\n"
        f"- Subject: {subject}\n"
        f"- Verdict: {verdict}\n\n"
        f"---\n\n"
    )
    local_path.write_text(header + report_markdown.strip() + "\n", encoding="utf-8")

    result: dict = {
        "status": "ok",
        "action": "report_saved",
        "local_path": str(local_path),
        "verdict": verdict,
        "subject": subject,
        "bytes": local_path.stat().st_size,
        "gcs_uri": None,
    }

    bucket_name = os.environ.get("REPORTS_GCS_BUCKET", "").strip()
    if not bucket_name:
        result["gcs"] = "skipped"
        result["message"] = (
            "Report saved locally. Set REPORTS_GCS_BUCKET to also upload to GCS."
        )
        return result

    try:
        from google.cloud import storage  # type: ignore
    except ImportError:
        result["gcs"] = "error"
        result["message"] = (
            "google-cloud-storage not installed; local report only. "
            "pip install google-cloud-storage"
        )
        return result

    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob_name = f"security-reports/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path), content_type="text/markdown")
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        result["gcs"] = "uploaded"
        result["gcs_uri"] = gcs_uri
        result["message"] = f"Report saved locally and uploaded to {gcs_uri}"
    except Exception as exc:  # noqa: BLE001 — surface to agent as tool result
        result["gcs"] = "error"
        result["message"] = (
            f"Local report saved, GCS upload failed: {type(exc).__name__}: {exc}"
        )

    return result
