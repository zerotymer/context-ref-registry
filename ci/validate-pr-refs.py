#!/usr/bin/env python3
"""
validate-pr-refs.py — Extract UUID/alias references from a PR diff and validate them.

Usage:
    python ci/validate-pr-refs.py <diff_file>          # from file
    git diff main...HEAD | python ci/validate-pr-refs.py -  # from stdin

Environment variables:
    REGISTRY_URL       Base URL of the registry API (default: http://localhost:8000)
    REGISTRY_API_KEY   API key for authentication (optional)
    GITHUB_TOKEN       GitHub token for posting PR comments
    PR_NUMBER          Pull request number
    REPO               Repository in "owner/repo" format
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

UUID_RE = re.compile(
    r'\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b',
    re.IGNORECASE,
)
REF_ANNOTATION_RE = re.compile(r'@(?:ref|entity):([a-zA-Z0-9_][a-zA-Z0-9_.-]*)')

REGISTRY_URL = os.environ.get("REGISTRY_URL", "http://localhost:8000")
REGISTRY_API_KEY = os.environ.get("REGISTRY_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
PR_NUMBER = os.environ.get("PR_NUMBER", "")
REPO = os.environ.get("REPO", "")


def extract_references(diff_text: str) -> list[str]:
    """Extract UUIDs and @ref/@entity annotations from diff added lines."""
    refs: set[str] = set()
    for line in diff_text.splitlines():
        if not line.startswith("+"):
            continue
        refs.update(UUID_RE.findall(line))
        refs.update(REF_ANNOTATION_RE.findall(line))
    return sorted(refs)


def call_validate_api(references: list[str]) -> dict:
    payload = json.dumps({"references": references}).encode()
    headers = {"Content-Type": "application/json"}
    if REGISTRY_API_KEY:
        headers["X-API-Key"] = REGISTRY_API_KEY

    req = Request(
        f"{REGISTRY_URL.rstrip('/')}/validate-references",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"[ERROR] Registry API returned {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"[ERROR] Cannot reach registry at {REGISTRY_URL}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def format_report(result: dict, refs: list[str]) -> str:
    data = result.get("data", result)
    valid = data["valid"]
    resolved = data["resolved"]
    ambiguous = data["ambiguous"]
    missing = data["missing"]

    lines = ["## Registry Reference Validation", ""]

    if not refs:
        lines += ["> No registry references found in this PR.", ""]
        return "\n".join(lines)

    status = "✅ All references valid" if valid else "❌ Invalid references detected"
    lines += [f"**{status}**", ""]
    lines += [f"Scanned **{len(refs)}** reference(s): {len(resolved)} resolved, {len(ambiguous)} ambiguous, {len(missing)} missing.", ""]

    if resolved:
        lines += ["### ✅ Resolved", ""]
        lines += ["| Input | Entity ID | Name | Status |", "| --- | --- | --- | --- |"]
        for r in resolved:
            lines.append(f"| `{r['input']}` | `{r['id']}` | {r.get('canonical_name', '')} | {r.get('entity_status', '')} |")
        lines.append("")

    if ambiguous:
        lines += ["### ⚠️ Ambiguous", ""]
        lines += ["| Input | Candidate IDs |", "| --- | --- |"]
        for a in ambiguous:
            candidates = ", ".join(f"`{c}`" for c in a["candidates"])
            lines.append(f"| `{a['input']}` | {candidates} |")
        lines.append("")

    if missing:
        lines += ["### ❌ Missing", ""]
        lines += ["| Input |", "| --- |"]
        for m in missing:
            lines.append(f"| `{m}` |")
        lines.append("")

    return "\n".join(lines)


def post_github_comment(body: str) -> None:
    if not GITHUB_TOKEN or not PR_NUMBER or not REPO:
        print("[INFO] GitHub comment skipped — GITHUB_TOKEN, PR_NUMBER, REPO not set.", file=sys.stderr)
        return

    payload = json.dumps({"body": body}).encode()
    req = Request(
        f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            comment = json.loads(resp.read())
            print(f"[INFO] Posted GitHub comment: {comment['html_url']}", file=sys.stderr)
    except (HTTPError, URLError) as e:
        print(f"[WARN] Failed to post GitHub comment: {e}", file=sys.stderr)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    path = sys.argv[1]
    if path == "-":
        diff_text = sys.stdin.read()
    else:
        with open(path) as f:
            diff_text = f.read()

    refs = extract_references(diff_text)
    print(f"[INFO] Found {len(refs)} reference(s): {refs}", file=sys.stderr)

    if not refs:
        report = format_report({"data": {"valid": True, "resolved": [], "ambiguous": [], "missing": []}}, [])
        print(report)
        post_github_comment(report)
        sys.exit(0)

    result = call_validate_api(refs)
    report = format_report(result, refs)
    print(report)
    post_github_comment(report)

    data = result.get("data", result)
    sys.exit(0 if data["valid"] else 1)


if __name__ == "__main__":
    main()
