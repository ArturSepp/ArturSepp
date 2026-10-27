"""Persist documentation monitoring and deliver deduplicated GitHub notifications."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from monitor_documentation import atomic_json

BRANCH = "automation/documentation-monitor"
STATE_PATH = "documentation-monitor.json"
ISSUE_MARKER = "<!-- oss-documentation-monitor -->"
TITLE = "OSS documentation: confirmed link failures and monitoring alerts"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward repository credentials through an HTTP redirect."""

    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


class GitHub:
    """Fixed-host REST requests; no credential forwarding to documentation sites."""

    def __init__(self, repository, token):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("Invalid GitHub repository")
        if not token:
            raise ValueError("GH_TOKEN is required")
        self.base = "https://api.github.com/repos/" + repository + "/"
        self.token = token

    def request(self, method, path, data=None, *, object_format=False):
        if path.startswith(("/", "http")) or ".." in path.split("/"):
            raise ValueError("GitHub endpoint must stay inside this repository")
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(data).encode() if data is not None else None,
            method=method,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github.object+json"
                if object_format
                else "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "ArturSepp-documentation-monitor",
            },
        )
        # No retry on writes: ambiguous delivery is reconciled using event markers.
        try:
            with urllib.request.build_opener(NoRedirect()).open(
                request, timeout=45
            ) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            raise RuntimeError(
                f"GitHub {method} {path.split('?')[0]}: HTTP {error.code}"
            ) from None
        except urllib.error.URLError:
            raise RuntimeError(
                "GitHub API transport unavailable; state/delivery not assumed successful"
            ) from None

    def items(self, path):
        page = 1
        while True:
            separator = "&" if "?" in path else "?"
            rows = self.request("GET", f"{path}{separator}per_page=100&page={page}")
            yield from rows
            if len(rows) < 100:
                break
            page += 1


def validate_snapshot(snapshot):
    if (
        snapshot.get("schema_version") != 1
        or snapshot["state"].get("schema_version") != 1
        or not isinstance(snapshot["state"]["history"], dict)
        or not isinstance(snapshot["state"]["checks"], dict)
        or not isinstance(snapshot["delivery"], dict)
        or not isinstance(snapshot["outbox"], list)
    ):
        raise ValueError("Invalid durable monitor snapshot; refusing to reset history")


def restore(api, directory):
    path = f"contents/{STATE_PATH}?ref={urllib.parse.quote(BRANCH, safe='')}"
    metadata = api.request("GET", path, object_format=True)
    if metadata.get("encoding") == "base64":
        snapshot = json.loads(base64.b64decode(metadata["content"]))
    else:
        # Fetch the exact blob, preserving the SHA comparison even for snapshots >1 MiB.
        blob = api.request("GET", "git/blobs/" + metadata["sha"])
        snapshot = json.loads(base64.b64decode(blob["content"]))
    validate_snapshot(snapshot)
    directory.mkdir(parents=True, exist_ok=True)
    atomic_json(
        directory / "remote.json", {"sha": metadata["sha"], "snapshot": snapshot}
    )
    atomic_json(directory / "state.json", snapshot["state"])
    return snapshot


def event_from_report(report, run_url):
    delta = {
        k: report[k]
        for k in ("alerts", "recoveries", "monitor_warnings", "monitor_recoveries")
    }
    if not any(delta.values()):
        return None
    value = {
        "checked_at_utc": report["checked_at_utc"],
        "delta": delta,
        "run_url": run_url,
    }
    value["id"] = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    return value


def prepare(directory, run_url):
    remote = json.loads((directory / "remote.json").read_text())
    report = json.loads((directory / "latest.json").read_text())
    state = json.loads((directory / "state.json").read_text())
    if state["checked_at_utc"] != report["checked_at_utc"]:
        raise ValueError("State and report belong to different runs")
    event = event_from_report(report, run_url)
    snapshot = remote["snapshot"]
    snapshot["state"] = state
    if event and event["id"] not in {e["id"] for e in snapshot["outbox"]}:
        snapshot["outbox"].append(event)
    validate_snapshot(snapshot)
    atomic_json(directory / "prepared.json", remote)
    summary = (
        f"## OSS documentation monitor\n\nObserved result: **{report['state']}**.\n\n"
        f"Healthy: {report['counts']['healthy']}; candidate failures: {report['counts']['broken']}; "
        f"unverified: {report['counts']['unverified']}.\n\n"
        f"New confirmed findings: {len(report['alerts'])}; recoveries: {len(report['recoveries'])}; "
        f"monitoring warnings: {len(report['monitor_warnings'])}.\n\n"
        "Network availability is outside normal commit/PR checks. See the evidence artifact.\n"
    )
    (directory / "summary.md").write_text(summary, encoding="utf-8")


def save(api, remote):
    content = base64.b64encode(
        (json.dumps(remote["snapshot"], separators=(",", ":")) + "\n").encode()
    ).decode()
    response = api.request(
        "PUT",
        f"contents/{STATE_PATH}",
        {
            "branch": BRANCH,
            "sha": remote["sha"],
            "content": content,
            "message": "chore: record documentation monitor state [skip ci]",
        },
    )
    remote["sha"] = response["content"]["sha"]


def marker(event):
    return "<!-- oss-doc-event:" + event["id"] + " -->"


def event_body(event, recipient):
    lines = [
        marker(event),
        "@" + recipient,
        "",
        f"Documentation check: {event['checked_at_utc']}",
        "",
        f"[Run and HTTP evidence]({event['run_url']})",
        "",
    ]
    for field, label in (
        ("alerts", "New confirmed failures"),
        ("recoveries", "Verified recoveries"),
        ("monitor_warnings", "Monitoring unavailable for three runs"),
        ("monitor_recoveries", "Monitoring restored"),
    ):
        rows = event["delta"][field]
        if not rows:
            continue
        lines.extend([f"### {label} ({len(rows)})", ""])
        for row in rows[:100]:
            if isinstance(row, str):
                lines.append("- " + row)
            else:
                url = urllib.parse.quote(row["url"], safe=":/#%._-~")
                detail = row.get("detail", "").replace("`", "'").replace("\n", " ")
                lines.append(f"- {row['repository']}: <{url}> — {detail}")
        if len(rows) > 100:
            lines.append("- Additional findings are recorded in the run artifact.")
        lines.append("")
    return "\n".join(lines)[:50000]


def find_issue(api, delivery):
    number = delivery.get("issue_number")
    if number:
        issue = api.request("GET", f"issues/{number}")
        if ISSUE_MARKER not in (issue.get("body") or ""):
            raise ValueError(
                "Recorded notification issue does not belong to this monitor"
            )
        return issue
    for issue in api.items("issues?state=all"):
        if (
            "pull_request" not in issue
            and ISSUE_MARKER in (issue.get("body") or "")
            and issue.get("user", {}).get("login") == "github-actions[bot]"
        ):
            return issue
    return None


def publish(api, directory, recipient):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", recipient):
        raise ValueError("Invalid notification recipient")
    remote = json.loads((directory / "prepared.json").read_text())
    snapshot = remote["snapshot"]
    validate_snapshot(snapshot)
    # Commit the URL ledger and pending deliveries BEFORE making any notification.
    # A stale rerun is rejected by the Contents API blob SHA, never overwriting a newer run.
    save(api, remote)
    while snapshot["outbox"]:
        event = snapshot["outbox"][0]
        issue = find_issue(api, snapshot["delivery"])
        body = event_body(event, recipient)
        active = any(c["active"] for c in snapshot["state"]["checks"].values()) or any(
            a["active"] for a in snapshot["state"].get("availability", {}).values()
        )
        if issue is None:
            issue = api.request(
                "POST",
                "issues",
                {
                    "title": TITLE,
                    "body": ISSUE_MARKER + "\n\n" + body,
                    "assignees": [recipient],
                },
            )
        else:
            already_sent = marker(event) in (issue.get("body") or "") or any(
                marker(event) in (c.get("body") or "")
                for c in api.items(f"issues/{issue['number']}/comments")
            )
            if issue["state"] == "closed" and active and not already_sent:
                api.request("PATCH", f"issues/{issue['number']}", {"state": "open"})
            if not already_sent:
                api.request(
                    "POST", f"issues/{issue['number']}/comments", {"body": body}
                )
        snapshot["delivery"]["issue_number"] = issue["number"]
        if not active:
            api.request(
                "PATCH",
                f"issues/{issue['number']}",
                {"state": "closed", "state_reason": "completed"},
            )
        snapshot["outbox"].pop(0)
        save(api, remote)
    atomic_json(
        directory / "published.json",
        {
            "sha": remote["sha"],
            "outbox": 0,
            "issue_number": snapshot["delivery"].get("issue_number"),
        },
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("restore", "prepare", "publish"))
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", "ArturSepp/ArturSepp"),
    )
    parser.add_argument("--recipient", default="ArturSepp")
    parser.add_argument("--run-url", default="")
    args = parser.parse_args(argv)
    try:
        if args.operation == "prepare":
            if not args.run_url.startswith(
                f"https://github.com/{args.repository}/actions/runs/"
            ):
                raise ValueError("Expected the monitor's own GitHub Actions run URL")
            prepare(args.state_dir, args.run_url)
        else:
            api = GitHub(args.repository, os.environ.get("GH_TOKEN", ""))
            if args.operation == "restore":
                restore(api, args.state_dir)
            else:
                publish(api, args.state_dir, args.recipient)
        print(json.dumps({"operation": args.operation, "state": "completed"}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(
            json.dumps({"state": "monitor_infrastructure_error", "error": str(error)})
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
