"""Bound transient reads and publish only verified generated-report snapshots."""
from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import os
import subprocess
import time
import urllib.error
from pathlib import Path

DELAYS = (2, 5, 10)
BRANCH = "automation/reports"
REGISTRY = json.loads(Path(__file__).with_name("public_registry.json").read_text(encoding="utf-8"))
DISTRIBUTIONS = {package["dist"] for package in REGISTRY["packages"]}
TRANSIENT_HTTP = {408, 429, 500, 502, 503, 504}


def backoff(stage, attempt, minimum=0):
    """Honor bounded server delays; a longer outage must remain visible."""
    delay = max(DELAYS[min(attempt, len(DELAYS) - 1)], minimum)
    if delay > 60:
        raise RuntimeError(f"{stage}: server requested a delay beyond this retry budget")
    print(json.dumps({"state": "workflow_retry", "stage": stage, "delay_seconds": delay}))
    time.sleep(delay)


def retry_read(operation, *, attempts=4):
    """Retry transient read failures, never permission or data-validation errors."""
    for attempt in range(attempts):
        minimum = 0
        try:
            return operation()
        except urllib.error.HTTPError as error:
            if error.code not in TRANSIENT_HTTP or attempt + 1 == attempts:
                raise
            header = (error.headers or {}).get("Retry-After")
            if header is not None:
                try:
                    minimum = max(0, int(header))
                except (TypeError, ValueError):
                    raise error from None
            elif error.code == 429:
                minimum = 60
            if minimum > 60:
                raise
            error.close()
        except (
            urllib.error.URLError, TimeoutError, ConnectionError,
            http.client.HTTPException, json.JSONDecodeError, UnicodeDecodeError,
        ):
            if attempt + 1 == attempts:
                raise
        backoff("HTTP read", attempt, minimum)
    raise ValueError("attempts must be positive")


def git(root, *arguments, check=True):
    """Run Git without a shell or exposing credential-bearing transport output."""
    result = subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=120, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(f"Git {arguments[0]} failed; repository state was not assumed successful")
    return result


def permanent_git_error(result):
    if result is None:
        return False
    detail = result.stderr.lower()
    return any(word in detail for word in (
        "permission denied", "authentication failed", "repository not found",
        "couldn't find remote ref", "does not appear to be a git repository",
        "could not read username",
    ))


def fetch_reports(root):
    """Fetch the existing report branch; a transport failure never means absent."""
    for attempt in range(len(DELAYS) + 1):
        try:
            result = git(root, "fetch", "--no-tags", "origin", f"refs/heads/{BRANCH}", check=False)
        except subprocess.TimeoutExpired:
            result = None
        if result is not None and result.returncode == 0:
            return git(root, "rev-parse", "FETCH_HEAD").stdout.strip()
        if permanent_git_error(result) or attempt == len(DELAYS):
            raise RuntimeError("Cannot fetch the existing report branch; refusing to recreate it")
        backoff("report fetch", attempt)
    raise AssertionError("unreachable")


def observed_at(value):
    stamp = dt.datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError("Report observation timestamp must include its timezone")
    return stamp


def snapshot(kind, source):
    """Validate a complete snapshot and capture its allowlisted files before Git switches."""
    if kind == "conformance":
        metadata = "CONFORMANCE.json"
        names = [metadata, "CONFORMANCE.md"]
        prefix = ""
    elif kind == "downloads":
        metadata = "counts.json"
        names = [metadata, "updated.svg", *[f"{slug}-total-blue.svg" for slug in sorted(DISTRIBUTIONS)]]
        prefix = "profile-downloads/"
    else:
        raise ValueError("Unknown generated-report kind")
    if any((source / name).is_symlink() for name in names):
        raise ValueError("Generated snapshot files must not be symlinks")
    files = {prefix + name: (source / name).read_bytes() for name in names}
    value = json.loads(files[prefix + metadata])
    packages = value["packages"]
    distributions = ({row["dist"] for row in packages} if kind == "conformance" else set(packages))
    if distributions != DISTRIBUTIONS or len(packages) != len(DISTRIBUTIONS):
        raise ValueError("Generated snapshot does not cover the approved package set")
    return files, prefix + metadata, observed_at(value["observed_at"])


def publish(kind, source, root):
    """Publish one immutable commit, reconciling failed pushes without overwriting newer work."""
    files, metadata, stamp = snapshot(kind, source)
    if git(root, "status", "--porcelain").stdout.strip():
        raise RuntimeError("Report publisher requires a clean checkout")
    base = fetch_reports(root)
    current = json.loads(git(root, "show", f"{base}:{metadata}").stdout)
    previous_stamp = observed_at(current["observed_at"])
    if stamp < previous_stamp:
        raise RuntimeError("Refusing to replace newer observations with a stale artifact")
    if stamp == previous_stamp:
        unchanged = all(
            git(root, "show", f"{base}:{name}").stdout.encode("utf-8") == content
            for name, content in files.items()
        )
        if unchanged:
            return "already_published"
        raise RuntimeError("Conflicting report content for the same observation timestamp")
    git(root, "switch", "--detach", base)
    for name, content in files.items():
        destination = root / name
        if not destination.resolve().is_relative_to(root.resolve()):
            raise ValueError("Report destination must remain inside its checkout")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    git(root, "add", "--", *files)
    git(root, "-c", "user.name=github-actions[bot]", "-c",
        "user.email=github-actions[bot]@users.noreply.github.com", "commit", "-m",
        f"chore: refresh verified {kind} report")
    commit = git(root, "rev-parse", "HEAD").stdout.strip()
    for attempt in range(len(DELAYS) + 1):
        try:
            result = git(root, "push", "origin", f"{commit}:refs/heads/{BRANCH}", check=False)
        except subprocess.TimeoutExpired:
            result = None
        if result is not None and result.returncode == 0:
            return "published"
        backoff("report push reconciliation", attempt)
        remote = fetch_reports(root)
        if git(root, "merge-base", "--is-ancestor", commit, remote, check=False).returncode == 0:
            return "already_published"
        if remote != base:
            raise RuntimeError("Report branch advanced; refusing to overwrite concurrent work")
        if permanent_git_error(result) or attempt == len(DELAYS):
            raise RuntimeError("Report push failed after reconciliation; existing reports preserved")
    raise AssertionError("unreachable")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("conformance", "downloads"))
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        parser.error("This publisher runs only inside its GitHub Actions job")
    try:
        result = publish(args.kind, args.source.resolve(), Path.cwd())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "report_publication_failed", "error": str(error)}))
        return 2
    print(json.dumps({"state": result, "kind": args.kind}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
