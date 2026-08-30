"""Local security review tools for PR/diff analysis."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Literal

MAX_DIFF_CHARS = 80_000
MAX_SCAN_OUTPUT_CHARS = 40_000
DEFAULT_TIMEOUT_SECONDS = 120


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n... [truncated at {limit} chars]"


def _resolve_repo_path(repo_path: str) -> Path:
    path = Path(repo_path).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    return path


def _git_toplevel(repo_path: Path) -> Path:
    result = subprocess.run(
        ['git', '-C', str(repo_path), 'rev-parse', '--show-toplevel'],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            f"Not a git repository: {repo_path}. "
            f"Error: {result.stderr.strip() or 'unknown'}"
        )
    return Path(result.stdout.strip())


def get_git_diff(
    repo_path: str,
    diff_mode: Literal[
        'uncommitted', 'staged', 'unstaged', 'branch'
    ] = 'uncommitted',
    base_branch: str = 'main',
) -> dict:
    """Return a git diff from a local repository for security review.

    Args:
        repo_path: Absolute or relative path to a git repository.
        diff_mode: Which changes to include.
            uncommitted — staged + unstaged vs HEAD (default, pre-push review)
            staged — index vs HEAD
            unstaged — working tree vs index
            branch — commits on current branch vs base_branch (MR-style)
        base_branch: Base branch for diff_mode=branch (e.g. main, develop).

    Returns:
        Dict with status, diff text, mode, and repo metadata.
    """
    path = _resolve_repo_path(repo_path)
    toplevel = _git_toplevel(path)

    if diff_mode == 'uncommitted':
        cmd = ['git', '-C', str(toplevel), 'diff', 'HEAD']
    elif diff_mode == 'staged':
        cmd = ['git', '-C', str(toplevel), 'diff', '--cached']
    elif diff_mode == 'unstaged':
        cmd = ['git', '-C', str(toplevel), 'diff']
    elif diff_mode == 'branch':
        for ref in (f'origin/{base_branch}', base_branch):
            check = subprocess.run(
                ['git', '-C', str(toplevel), 'rev-parse', '--verify', ref],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if check.returncode == 0:
                cmd = ['git', '-C', str(toplevel), 'diff', f'{ref}...HEAD']
                break
        else:
            raise ValueError(
                f"Base branch not found: tried origin/{base_branch} and {base_branch}"
            )
    else:
        raise ValueError(f"Unsupported diff_mode: {diff_mode}")

    branch_result = subprocess.run(
        ['git', '-C', str(toplevel), 'branch', '--show-current'],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    current_branch = branch_result.stdout.strip() or '(detached)'

    diff_result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        check=False,
    )
    if diff_result.returncode not in (0, 1):
        raise RuntimeError(
            f"git diff failed: {diff_result.stderr.strip() or 'unknown error'}"
        )

    diff_text = diff_result.stdout
    if not diff_text.strip():
        return {
            'status': 'empty',
            'repo_path': str(toplevel),
            'branch': current_branch,
            'diff_mode': diff_mode,
            'message': 'No changes found for the selected diff mode.',
            'diff': '',
        }

    return {
        'status': 'ok',
        'repo_path': str(toplevel),
        'branch': current_branch,
        'diff_mode': diff_mode,
        'diff': _truncate(diff_text, MAX_DIFF_CHARS),
        'truncated': len(diff_text) > MAX_DIFF_CHARS,
    }


def scan_secrets_with_gitleaks(
    repo_path: str,
    scan_mode: Literal['working_tree', 'git_history'] = 'working_tree',
    log_opts: str = 'HEAD~1..HEAD',
) -> dict:
    """Scan a repository for hardcoded secrets using gitleaks.

    Args:
        repo_path: Path to the repository or directory to scan.
        scan_mode: working_tree — current files; git_history — recent commits.
        log_opts: Git log range when scan_mode=git_history (default last commit).

    Returns:
        Parsed gitleaks JSON report or error details.
    """
    if shutil.which('gitleaks') is None:
        return {
            'status': 'error',
            'tool': 'gitleaks',
            'message': 'gitleaks not found. Install: brew install gitleaks',
        }

    path = _resolve_repo_path(repo_path)
    cmd = [
        'gitleaks', 'detect',
        '--source', str(path),
        '--report-format', 'json',
        '--report-path', '-',
        '--no-banner',
        '--exit-code', '0',
    ]
    if scan_mode == 'working_tree':
        cmd.append('--no-git')
    else:
        cmd.extend(['--log-opts', log_opts])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        check=False,
    )

    output = (result.stdout or result.stderr).strip()
    if not output:
        return {
            'status': 'ok',
            'tool': 'gitleaks',
            'findings_count': 0,
            'findings': [],
            'message': 'No secrets detected.',
        }

    try:
        findings = json.loads(output)
    except json.JSONDecodeError:
        return {
            'status': 'error',
            'tool': 'gitleaks',
            'message': _truncate(output, MAX_SCAN_OUTPUT_CHARS),
        }

    if not isinstance(findings, list):
        findings = [findings]

    return {
        'status': 'ok',
        'tool': 'gitleaks',
        'findings_count': len(findings),
        'findings': findings[:50],
        'truncated': len(findings) > 50,
    }


def scan_code_with_semgrep(
    repo_path: str,
    config: Literal['auto', 'p/security-audit', 'p/ci'] = 'p/security-audit',
) -> dict:
    """Run semgrep security rules on a repository.

    Args:
        repo_path: Path to scan.
        config: Semgrep ruleset — auto, p/security-audit, or p/ci.

    Returns:
        Semgrep JSON results or install instructions if missing.
    """
    if shutil.which('semgrep') is None:
        return {
            'status': 'error',
            'tool': 'semgrep',
            'message': (
                'semgrep not found. Install: brew install semgrep '
                '(or pip install semgrep). Then re-run the scan.'
            ),
        }

    path = _resolve_repo_path(path=repo_path)
    cmd = [
        'semgrep',
        '--config', config,
        '--json',
        '--quiet',
        str(path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        check=False,
    )

    if not result.stdout.strip():
        err = result.stderr.strip() or 'semgrep produced no output'
        return {'status': 'error', 'tool': 'semgrep', 'message': err}

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            'status': 'error',
            'tool': 'semgrep',
            'message': _truncate(result.stdout, MAX_SCAN_OUTPUT_CHARS),
        }

    results = report.get('results', [])
    return {
        'status': 'ok',
        'tool': 'semgrep',
        'config': config,
        'findings_count': len(results),
        'findings': results[:30],
        'truncated': len(results) > 30,
        'errors': report.get('errors', []),
    }
