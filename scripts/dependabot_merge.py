"""Merge verified Dependabot PRs and report failures without executing PR content."""

from __future__ import annotations

import argparse
import base64
import difflib
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import tomllib
from documentation_monitor_actions import GitHub, GitHubError
from monitor_documentation import atomic_json

HERE = Path(__file__).resolve().parent
BRANCH = "automation/dependabot-merge"
STATE_FILE = "dependabot-merge.json"
CALLER = ".github/workflows/dependabot-merge.yml"
ACTION_LINE = re.compile(
    r"^(\s*(?:-\s+)?uses:\s+)([\w.-]+/[\w.-]+(?:/[\w./-]+)?)@([a-f0-9]{40})(\s+#\s*)(v?[0-9][\w.+-]*)\s*$"
)
REQUIREMENT = re.compile(r"^\s*([\w.-]+)(\[[^\]]+\])?\s*([^;@]*)(;.*)?$")


class ManualReview(ValueError):
    """An update is outside the dependency-only policy."""


def read_file(api, path, ref):
    metadata = api.request(
        "GET",
        "contents/" + path + "?ref=" + urllib.parse.quote(ref, safe=""),
        object_format=True,
    )
    if metadata.get("type") != "file":
        raise ManualReview("Expected a regular repository file")
    blob = (
        metadata
        if metadata.get("encoding") == "base64"
        else api.request("GET", "git/blobs/" + metadata["sha"])
    )
    return base64.b64decode(blob["content"])


class Store:
    """Compare-and-swap notification intents on a dedicated non-source branch."""

    def __init__(self, api, repository):
        self.api, self.repository = api, repository
        self.sha, self.value = self.read()

    def read(self):
        metadata = self.api.request(
            "GET",
            f"contents/{STATE_FILE}?ref={urllib.parse.quote(BRANCH, safe='')}",
            object_format=True,
        )
        blob = (
            metadata
            if metadata.get("encoding") == "base64"
            else self.api.request("GET", "git/blobs/" + metadata["sha"])
        )
        value = json.loads(base64.b64decode(blob["content"]))
        if (
            value.get("schema_version") != 1
            or value.get("repository") != self.repository
            or not isinstance(value.get("notifications"), dict)
        ):
            raise ValueError("Invalid durable Dependabot state; refusing to reset it")
        return metadata["sha"], value

    def save(self):
        payload = {
            "branch": BRANCH,
            "sha": self.sha,
            "message": "chore: record Dependabot notification state [skip ci]",
            "content": base64.b64encode(
                (json.dumps(self.value, sort_keys=True) + "\n").encode()
            ).decode(),
        }
        try:
            response = self.api.request("PUT", "contents/" + STATE_FILE, payload)
            self.sha = response["content"]["sha"]
        except (GitHubError, KeyError, TypeError):
            current_sha, current = self.read()
            if current != self.value:
                raise RuntimeError(
                    "State write unverified or stale; refusing further mutations"
                ) from None
            self.sha = current_sha


def requirement_shape(value):
    if isinstance(value, dict):
        return value  # Dependency-group includes cannot change.
    match = REQUIREMENT.fullmatch(value)
    if not match:
        raise ManualReview("Direct URL requirements require manual review")
    name, extras, _, marker = match.groups()
    return (
        name.lower().replace("_", "-").replace(".", "-"),
        extras or "",
        marker or "",
    )


def project_shape(text):
    value = tomllib.loads(text)
    for parent, key in [
        (value.get("project", {}), "dependencies"),
        (value.get("build-system", {}), "requires"),
    ]:
        if key in parent:
            parent[key] = [requirement_shape(r) for r in parent[key]]
    for group in [
        value.get("project", {}).get("optional-dependencies", {}),
        value.get("dependency-groups", {}),
    ]:
        for name, requirements in group.items():
            group[name] = [requirement_shape(r) for r in requirements]
    return value


def verify_lock(before, after, public_json):
    old, new = tomllib.loads(before), tomllib.loads(after)
    if {k: v for k, v in old.items() if k != "package"} != {
        k: v for k, v in new.items() if k != "package"
    }:
        raise ManualReview(
            "Lock format, Python policy or top-level lock configuration changed"
        )
    old_rows = {json.dumps(p, sort_keys=True) for p in old["package"]}
    old_sources = {
        p["name"]: p["source"] for p in old["package"] if "registry" not in p["source"]
    }
    for package in new["package"]:
        if json.dumps(package, sort_keys=True) in old_rows:
            continue
        source = package["source"]
        if "registry" not in source:
            if source != old_sources.get(package["name"]):
                raise ManualReview(
                    "New editable/path/Git source requires manual review"
                )
            continue
        if source != {"registry": "https://pypi.org/simple"}:
            raise ManualReview(
                "Only the approved PyPI registry may change automatically"
            )
        name, version = package["name"], package["version"]
        url = (
            "https://pypi.org/pypi/"
            + urllib.parse.quote(name, safe="")
            + "/"
            + urllib.parse.quote(version, safe="")
            + "/json"
        )
        metadata = public_json(url)
        files = {p["url"]: p for p in metadata["urls"]}
        for artifact in [package.get("sdist"), *package.get("wheels", [])]:
            if artifact is None:
                continue
            released = files.get(artifact["url"])
            if (
                not released
                or released.get("yanked")
                or artifact["hash"] != "sha256:" + released["digests"]["sha256"]
                or artifact.get("size", released["size"]) != released["size"]
            ):
                raise ManualReview(
                    "Locked artifact differs from the non-yanked PyPI release"
                )


def public_json(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except (OSError, ValueError):
        raise GitHubError(
            "PyPI release metadata unavailable; update remains unverified"
        ) from None


def verify_diff(api, pr, upstream, fetch_json=public_json):
    files = list(api.items(f"pulls/{pr['number']}/files"))
    if not files or len(files) > 100:
        raise ManualReview("Empty or oversized update requires manual review")
    for file in files:
        path = file["filename"]
        if file["status"] != "modified" or path == CALLER:
            raise ManualReview(
                "Added, removed, renamed or automation-policy files require review"
            )
        if path == "pyproject.toml":
            a = read_file(api, path, pr["base"]["sha"]).decode("utf-8")
            b = read_file(api, path, pr["head"]["sha"]).decode("utf-8")
            if project_shape(a) != project_shape(b):
                raise ManualReview(
                    "Project identity, dependency names/markers or tool configuration changed"
                )
        elif path == "uv.lock":
            a = read_file(api, path, pr["base"]["sha"]).decode("utf-8")
            b = read_file(api, path, pr["head"]["sha"]).decode("utf-8")
            verify_lock(a, b, fetch_json)
        elif path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
            # Read the complete immutable blobs: the PR files API may truncate patches.
            before = read_file(api, path, pr["base"]["sha"]).decode("utf-8")
            after = read_file(api, path, pr["head"]["sha"]).decode("utf-8")
            diff = list(difflib.ndiff(before.splitlines(), after.splitlines()))
            removed = [line[2:] for line in diff if line.startswith("- ")]
            added = [line[2:] for line in diff if line.startswith("+ ")]
            if not removed or len(removed) != len(added):
                raise ManualReview("Workflow logic changed")
            for a, b in zip(removed, added):
                old, new = ACTION_LINE.fullmatch(a), ACTION_LINE.fullmatch(b)
                if (
                    not old
                    or not new
                    or old[1] != new[1]
                    or old[2] != new[2]
                    or old[4] != new[4]
                    or old[3] == new[3]
                ):
                    raise ManualReview(
                        "Only existing action SHA/version pins may change"
                    )
                if any(part in {".", ".."} for part in new[2].split("/")):
                    raise ManualReview("Invalid upstream action path")
                if upstream(new[2], new[5]) != new[3]:
                    raise ManualReview(
                        "Action SHA does not match the named upstream release tag"
                    )
        else:
            raise ManualReview("File outside the dependency-update allowlist: " + path)


def eligible(pr, repository, default_branch):
    return (
        pr.get("state") == "open"
        and not pr.get("draft")
        and pr["user"]["login"] == "dependabot[bot]"
        and pr["user"].get("type") == "Bot"
        and pr["base"]["ref"] == default_branch
        and pr["base"]["repo"]["full_name"].lower() == repository.lower()
        and (pr["head"].get("repo") or {}).get("full_name", "").lower()
        == repository.lower()
        and pr["head"]["ref"].startswith("dependabot/")
    )


def gate(api, pr):
    sha = pr["head"]["sha"]
    workflow = api.request("GET", "actions/workflows/required.yml")
    if (
        workflow.get("path") != ".github/workflows/required.yml"
        or workflow.get("state") != "active"
    ):
        return "blocked", ["Trusted required-checks workflow is absent or disabled"]
    runs = api.request(
        "GET",
        f"actions/workflows/{workflow['id']}/runs?event=pull_request&head_sha={sha}&per_page=100",
    )["workflow_runs"]
    runs = [
        r
        for r in runs
        if r["head_sha"] == sha
        and r["event"] == "pull_request"
        and r["workflow_id"] == workflow["id"]
    ]
    if not runs:
        return "pending", ["No trusted required run on the current head"]
    run = max(runs, key=lambda r: r["id"])
    if run["status"] != "completed":
        return "pending", ["Current required workflow is still running"]
    if run["conclusion"] != "success":
        return "failed", [f"Required checks: {run['conclusion']} ({run['html_url']})"]
    jobs = list(api.items(f"actions/runs/{run['id']}/jobs?filter=latest"))
    if not any(
        j["name"] == "Required checks" and j["conclusion"] == "success" for j in jobs
    ):
        return "blocked", ["The required rollup did not pass in the trusted run"]
    checks = list(api.items(f"commits/{sha}/check-runs?filter=latest"))
    # The checks endpoint returns an object; run() supplies an adapter for its array.
    failures = [
        c["name"] + ": " + str(c["conclusion"])
        for c in checks
        if c["status"] == "completed"
        and c["conclusion"] not in {"success", "neutral", "skipped"}
    ]
    statuses = api.request("GET", f"commits/{sha}/status")["statuses"]
    failures += [
        c["context"] + ": " + c["state"]
        for c in statuses
        if c["state"] in {"failure", "error"}
    ]
    if failures:
        return "failed", failures
    if any(c["status"] != "completed" for c in checks) or any(
        c["state"] != "success" for c in statuses
    ):
        return "pending", ["Other current-head checks are still pending"]
    latest = {}
    for review in api.items(f"pulls/{pr['number']}/reviews"):
        if review["state"] not in {"COMMENTED", "PENDING"}:
            latest[review["user"]["login"]] = review["state"]
    if "CHANGES_REQUESTED" in latest.values():
        return "blocked", ["A reviewer requested changes"]
    return "ready", []


class RepoAPI(GitHub):
    """Normalize paginated check-run and job endpoint envelopes."""

    def items(self, path):
        if path.startswith(("commits/", "actions/runs/")):
            key = "check_runs" if "/check-runs" in path else "jobs"
            page = 1
            while True:
                sep = "&" if "?" in path else "?"
                rows = self.request("GET", f"{path}{sep}per_page=100&page={page}")[key]
                yield from rows
                if len(rows) < 100:
                    return
                page += 1
        else:
            yield from super().items(path)


def notify(api, store, pr, kind, details, run_url):
    normalized = [re.sub(r"https?://[^\s)]+", "<run>", d) for d in details]
    signature = {
        "pr": pr["number"],
        "head": pr["head"]["sha"],
        "kind": kind,
        "details": sorted(normalized),
    }
    fingerprint = hashlib.sha256(
        json.dumps(signature, sort_keys=True).encode()
    ).hexdigest()
    marker = "<!-- oss-dependabot-failure:" + fingerprint + " -->"
    existing = store.value["notifications"].get(fingerprint)
    if existing and existing["phase"] == "sent":
        return "already_notified"
    for comment in api.items(f"issues/{pr['number']}/comments"):
        if (
            marker in comment.get("body", "")
            and comment["user"]["login"] == "github-actions[bot]"
        ):
            store.value["notifications"][fingerprint] = {
                **signature,
                "phase": "sent",
                "comment_id": comment["id"],
            }
            store.save()
            return "reconciled"
    if existing:
        raise RuntimeError(
            "Notification delivery pending discovery; refusing a duplicate comment"
        )
    store.value["notifications"][fingerprint] = {**signature, "phase": "posting"}
    store.save()
    body = (
        marker
        + "\n@ArturSepp\n\nDependabot automatic merge needs attention on "
        + pr["html_url"]
        + " at `"
        + pr["head"]["sha"]
        + "`.\n\n"
        + "\n".join("- " + d.replace("`", "'").replace("\n", " ") for d in details)
        + "\n\n[Automation run]("
        + run_url
        + ")\n\n"
        + "The PR remains unmerged. Existing required checks and branch protections were not bypassed."
    )
    response = api.request(
        "POST", f"issues/{pr['number']}/comments", {"body": body[:50000]}
    )
    store.value["notifications"][fingerprint].update(
        phase="sent", comment_id=response["id"]
    )
    store.save()
    return "notified"


def process(
    api,
    repository,
    default_branch,
    store,
    apply,
    run_url,
    upstream,
    fetch_json=public_json,
):
    rows, errors = [], []
    for item in api.items("pulls?state=open"):
        pr = api.request("GET", f"pulls/{item['number']}")
        if not eligible(pr, repository, default_branch):
            continue
        row = {"pr": pr["number"], "head": pr["head"]["sha"], "url": pr["html_url"]}
        rows.append(row)
        try:
            status, details = gate(api, pr)
            if status == "ready":
                try:
                    verify_diff(api, pr, upstream, fetch_json)
                except ManualReview as error:
                    status, details = "blocked", [str(error)]
            current = api.request("GET", f"pulls/{pr['number']}")
            if (
                not eligible(current, repository, default_branch)
                or current["head"]["sha"] != pr["head"]["sha"]
            ):
                row["state"] = "changed_during_check"
                continue
            row.update(state=status, details=details)
            if status == "ready" and apply:
                try:
                    result = api.request(
                        "PUT",
                        f"pulls/{pr['number']}/merge",
                        {"sha": pr["head"]["sha"], "merge_method": "squash"},
                    )
                    if not result.get("merged"):
                        raise GitHubError("GitHub declined the merge")
                    row.update(state="merged", merge_commit=result["sha"])
                except GitHubError as error:
                    current = api.request("GET", f"pulls/{pr['number']}")
                    if current.get("merged"):
                        row["state"] = "merged_reconciled"
                    elif current["head"]["sha"] != pr["head"]["sha"]:
                        row["state"] = "changed_during_merge"
                    elif error.retryable:
                        raise
                    else:
                        row.update(state="merge_failed", details=[str(error)])
                        row["notification"] = notify(
                            api, store, pr, "merge_failed", row["details"], run_url
                        )
            elif status in {"failed", "blocked"} and apply:
                row["notification"] = notify(api, store, pr, status, details, run_url)
        except (GitHubError, RuntimeError, ValueError, KeyError, TypeError) as error:
            row.update(state="unverified", error=str(error))
            errors.append({"pr": pr["number"], "error": str(error)})
    return {
        "repository": repository,
        "mode": "apply" if apply else "dry_run",
        "pull_requests": rows,
        "infrastructure_errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        registry = json.loads(
            (HERE / "public_registry.json").read_text(encoding="utf-8")
        )
        allowed = {
            registry["owner"].lower() + "/" + p["repo"].lower()
            for p in registry["packages"]
        }
        if not args.repository or args.repository.lower() not in allowed:
            raise ValueError("Repository is outside the approved OSS registry")
        if args.apply and (
            os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("GITHUB_REPOSITORY", "").lower()
            != args.repository.lower()
        ):
            raise ValueError(
                "Apply is restricted to the calling package GitHub Actions job"
            )
        token = os.environ.get("GH_TOKEN", "")
        api = RepoAPI(args.repository, token)
        metadata = api.request("GET", "")
        if args.apply and (
            os.environ.get("GITHUB_EVENT_NAME")
            not in {"workflow_run", "schedule", "workflow_dispatch"}
            or os.environ.get("GITHUB_REF")
            != "refs/heads/" + metadata["default_branch"]
        ):
            raise ValueError(
                "Apply requires a trusted default-branch maintenance event"
            )
        store = Store(api, args.repository) if args.apply else None
        cache = {}

        def upstream(action, tag):
            repo = "/".join(action.split("/")[:2])
            key = (repo, tag)
            if key not in cache:
                obj = RepoAPI(repo, token).request(
                    "GET", "git/ref/tags/" + urllib.parse.quote(tag, safe="")
                )["object"]
                for _ in range(3):
                    if obj["type"] == "commit":
                        break
                    obj = RepoAPI(repo, token).request("GET", "git/tags/" + obj["sha"])[
                        "object"
                    ]
                if obj["type"] != "commit":
                    raise ManualReview("Upstream tag does not resolve to a commit")
                cache[key] = obj["sha"]
            return cache[key]

        run_url = (
            "https://github.com/"
            + args.repository
            + "/actions/runs/"
            + os.environ.get("GITHUB_RUN_ID", "local")
        )
        report = process(
            api,
            args.repository,
            metadata["default_branch"],
            store,
            args.apply,
            run_url,
            upstream,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(args.output_dir / "report.json", report)
        summary = (
            "## Dependabot merge monitor\n\n"
            + "\n".join(
                f"- {p['url']}: **{p['state']}**" for p in report["pull_requests"]
            )
            + (
                "\nNo open eligible Dependabot PRs.\n"
                if not report["pull_requests"]
                else "\n"
            )
        )
        (args.output_dir / "summary.md").write_text(summary, encoding="utf-8")
        print(json.dumps(report))
        return 2 if report["infrastructure_errors"] else 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        report = {"state": "automation_unverified", "error": str(error)}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(args.output_dir / "report.json", report)
        (args.output_dir / "summary.md").write_text(
            "## Dependabot merge monitor\n\nAutomation could not verify the repository. "
            "No merge is assumed successful; inspect the run log and report artifact.\n",
            encoding="utf-8",
        )
        print(json.dumps(report))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
