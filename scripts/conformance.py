"""Read-only public-surface checks; unavailable network data is never a clean bill of health."""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import re
import shlex
import subprocess
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

REGISTRY = Path(__file__).with_name("public_registry.json")
AGENT_MANIFEST = Path(__file__).with_name("agent_core_manifest.json")
URL_KEYS = {"Homepage", "Documentation", "Repository", "Changelog", "Issues"}


def normalized(name: str) -> str:
    """Apply the distribution-name normalization used by package indexes."""
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement: str) -> str:
    """Read only the leading package name, leaving markers and extras untouched."""
    match = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", requirement)
    if not match:
        raise ValueError(f"Invalid requirement: {requirement!r}")
    return normalized(match[0])


def load_registry(path: Path = REGISTRY) -> dict:
    """Load a unique, closed and acyclic approved dependency graph."""
    registry = json.loads(path.read_text(encoding="utf-8"))
    packages = registry["packages"]
    for field in ("repo", "dist", "import", "rtd"):
        if len({p[field].lower() for p in packages}) != len(packages):
            raise ValueError(f"Duplicate registry {field}")
    graph = {p["import"]: set(p["core"]) | {x for xs in p["extras"].values() for x in xs}
             for p in packages}
    visited, active = set(), set()

    def visit(node: str) -> None:
        if node in active:
            raise ValueError(f"Dependency cycle at {node}")
        if node not in graph:
            raise ValueError(f"Unknown stack module {node}")
        if node in visited:
            return
        active.add(node)
        for child in graph[node]:
            visit(child)
        active.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return registry


def git(root: Path, *args: str) -> str:
    """Run a bounded read-only Git query without refreshing the index."""
    command = ["git", "-c", f"safe.directory={root.resolve().as_posix()}",
               "--no-optional-locks", "-C", str(root), *args]
    return subprocess.run(command, check=True, text=True, encoding="utf-8",
                          capture_output=True, timeout=60).stdout.strip()


def fetch_json(url: str, attempts: int = 3) -> dict | list:
    """Fetch public JSON; retry transport/rate errors and surface failure explicitly."""
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ArturSepp-conformance/1",
                                                          "Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except (OSError, ValueError) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code == 404:
                raise
            if attempt == attempts - 1:
                raise
            time.sleep(1 + attempt)
    raise AssertionError("unreachable")


def finding(check: str, state: str, detail: str) -> dict:
    """Create a report cell with a stable machine-readable identifier."""
    return {"check": check, "state": state, "detail": detail}


def historical_backlog(package: dict, registry: dict) -> list[dict]:
    """Keep recorded provenance defects visible when current public data is unavailable."""
    return [finding("historical_provenance", "known-gap", f"{version}: {record['reason']} (recorded {record['recorded']}; not refreshed)")
            for version, record in registry.get("historical_release_gaps", {}).get(package["dist"], {}).items()]


def agent_block_digest(source: str) -> str:
    """Hash the generated block including its markers; a current stamp alone is insufficient."""
    blocks = re.findall(r"<!-- ===== SHARED AGENT CORE .*?<!-- ===== SHARED AGENT CORE — end ===== -->", source, re.DOTALL)
    if len(blocks) != 1:
        raise ValueError("Expected exactly one generated agent-core block")
    return hashlib.sha256(blocks[0].encode("utf-8")).hexdigest()


def render_release_template(name: str, package: dict) -> str:
    """Render reviewed registry variances identically for generation and checking."""
    content = (Path(__file__).with_name("templates") / name).read_text(encoding="utf-8")
    for key, value in (("DIST", package["dist"]), ("IMPORT", package["import"]), ("TIER", package["tier"])):
        content = content.replace("{{" + key + "}}", value)
    sdk = package.get("release_external_sdk")
    command = ""
    if sdk:
        command = "          uv pip install --python {python} --index-url=" + shlex.quote(sdk["index_url"]) + " " + shlex.quote(sdk["requirement"]) + "\n"
    return content.replace("{{PROJECT_SDK}}", command.format(python=".venv") if command else "").replace("{{WHEEL_SDK}}", command.format(python='"$RUNNER_TEMP/release-wheel-env/bin/python"') if command else "")


def generated_release_drift(root: Path, package: dict) -> list[str]:
    """Compare generated source content, including edits which preserve an old stamp."""
    errors = []
    for name, relative in (("release.yml", ".github/workflows/release.yml"),
                           ("release_guard.py", ".github/scripts/release_guard.py"),
                           ("publish_tag.py", ".github/scripts/publish_tag.py")):
        expected = render_release_template(name, package)
        target = root / relative
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            errors.append(relative)
    return errors


def offline_checks(root: Path, package: dict, registry: dict) -> list[dict]:
    """Check source metadata, approved graph, import bans and tracked hygiene."""
    result = []
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    metadata = project["project"]
    mismatches = []
    if normalized(metadata["name"]) != normalized(package["dist"]):
        mismatches.append("distribution name")
    if metadata["description"] != package["summary"]:
        mismatches.append("summary")
    if set(metadata.get("urls", {})) != URL_KEYS | set(package.get("extra_url_keys", [])):
        mismatches.append("URL key set")
    if metadata.get("urls", {}).get("Documentation", "").rstrip("/") != f"https://{package['rtd']}.readthedocs.io":
        mismatches.append("canonical Documentation URL")
    result.append(finding("source_metadata", "fail" if mismatches else "pass", ", ".join(mismatches) or "registry matches"))
    imports = {normalized(p["dist"]): p["import"] for p in registry["packages"]}
    own = package["import"]

    def edges(requirements: list[str]) -> set[str]:
        return {imports[requirement_name(req)] for req in requirements
                if requirement_name(req) in imports and imports[requirement_name(req)] != own}

    errors = []
    if edges(metadata.get("dependencies", [])) != set(package["core"]):
        errors.append("core dependency edges differ from approved registry")
    extras = metadata.get("optional-dependencies", {})
    for extra in extras.keys() | package["extras"].keys():
        if edges(extras.get(extra, [])) != set(package["extras"].get(extra, [])):
            errors.append(f"extra {extra}: dependency edges differ")
    allowed = set(package["core"]) | {x for xs in package["extras"].values() for x in xs}
    expected_bans = set(imports.values()) - allowed - {own}
    lint = project.get("tool", {}).get("ruff", {}).get("lint", {})
    actual_bans = set(lint.get("flake8-tidy-imports", {}).get("banned-api", {}))
    missing = expected_bans - actual_bans
    if missing:
        errors.append("missing import bans: " + ", ".join(sorted(missing)))
    # Independently inspect core source: a stale Ruff stamp or a broad ignore cannot hide an edge.
    for path in sorted((root / "src" / own).rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except (SyntaxError, UnicodeError) as error:
            errors.append(f"{path.relative_to(root)}: cannot inspect syntax: {error}")
            continue
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            names = ([a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import)
                     else [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module and not node.level
                     else [])
            for name in set(names) & expected_bans:
                exceptions = [entry for entry in package.get("development_imports", [])
                              if entry["path"] == path.relative_to(root).as_posix() and name in entry["modules"]]
                scopes, parent = [], parents.get(node)
                while parent is not None:
                    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        scopes.append(parent.name)
                    parent = parents.get(parent)
                if any("function" not in entry or entry["function"] in scopes for entry in exceptions):
                    continue
                errors.append(f"{path.relative_to(root)}:{node.lineno}: forbidden import {name}")
    result.append(finding("dependency_graph", "fail" if errors else "pass", "; ".join(errors) or "declared and imported stack edges allowed"))
    tracked = git(root, "ls-files").splitlines()
    hygiene = ["tracked IDE files" for x in tracked if x.startswith(".idea/")][:1]
    if not (root / ".gitattributes").exists():
        hygiene.append("missing .gitattributes")
    agent = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").exists() else ""
    if f"agent core v{registry['agent_core_version']}" not in agent:
        hygiene.append(f"agent core stamp differs from v{registry['agent_core_version']}")
    manifest = json.loads(AGENT_MANIFEST.read_text(encoding="utf-8"))
    try:
        if manifest["version"] != registry["agent_core_version"] or agent_block_digest(agent) != manifest["sha256"][package["local_dir"]]:
            hygiene.append("agent core content differs from reviewed manifest")
    except ValueError as error:
        hygiene.append(str(error))
    for name in ("AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "CITATION.cff", "CHANGELOG.md"):
        if not (root / name).exists():
            hygiene.append(f"missing {name}")
    result.append(finding("hygiene", "fail" if hygiene else "pass", "; ".join(hygiene) or "required source files present"))
    workflows = []
    for path in sorted((root / ".github/workflows").glob("*.y*ml")):
        source = path.read_text(encoding="utf-8")
        for action in re.findall(r"uses:\s*([^\s#]+)", source):
            if not action.startswith("./") and not re.fullmatch(r"[^@]+@[0-9a-f]{40}", action):
                workflows.append(f"{path.name}: mutable action {action}")
    result.append(finding("action_pins", "fail" if workflows else "pass", "; ".join(workflows) or "external actions pinned to full SHA"))
    generated = generated_release_drift(root, package)
    result.append(finding("release_templates", "fail" if generated else "pass", ", ".join(generated) or "generated release files match reviewed template content"))
    return result


def release_checks(root: Path, package: dict, pypi: dict, since: str, known_gaps: dict | None = None) -> list[dict]:
    """Check every recent PyPI release against its tag; main may intentionally be ahead."""
    result = []
    known_gaps = known_gaps or {}
    for version, files in pypi.get("releases", {}).items():
        if not files or (version not in known_gaps and max(f.get("upload_time_iso_8601", f.get("upload_time", "")) for f in files)[:10] < since):
            continue
        if version in known_gaps:
            # An existing version tag alone cannot close documented artifact-provenance gaps.
            result.append(finding("historical_provenance", "known-gap", f"{version}: {known_gaps[version]['reason']}"))
            continue
        tag = f"v{version}"
        if not re.fullmatch(r"v\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?(?:\.post\d+)?(?:\.dev\d+)?", tag):
            result.append(finding("published_tag", "unknown", f"{version}: unsupported historical version syntax"))
            continue
        try:
            tagged = tomllib.loads(git(root, "show", f"refs/tags/{tag}:pyproject.toml"))["project"]
        except (subprocess.SubprocessError, ValueError) as error:
            result.append(finding("published_tag", "fail", f"{version}: missing or unreadable {tag}"))
            continue
        if tagged["version"] != version or normalized(tagged["name"]) != normalized(package["dist"]):
            result.append(finding("published_tag", "fail", f"{tag}: metadata identifies {tagged['name']} {tagged['version']}"))
        else:
            result.append(finding("published_tag", "pass", f"{tag}: matches published version"))
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    current = project["version"]
    published = bool(pypi.get("releases", {}).get(current))
    result.append(finding("development_state", "pass", f"main/source {current}: " + ("published" if published else "prepared/unpublished; GitHub Release page optional")))
    return result


def network_checks(root: Path, package: dict, registry: dict, fetch=fetch_json) -> list[dict]:
    """Collect independent services so an unavailable API does not hide other findings."""
    result = []
    try:
        data = fetch(f"https://pypi.org/pypi/{package['dist']}/json")
        if not isinstance(data, dict) or not isinstance(data.get("releases"), dict) or not isinstance(data.get("info"), dict):
            raise ValueError("unexpected PyPI response")
        result.extend(release_checks(root, package, data, registry["history_since"],
                                     registry.get("historical_release_gaps", {}).get(package["dist"], {})))
        info = data["info"]
        urls = info.get("project_urls") or {}
        stale = (info.get("summary") != package["summary"]
                 or set(urls) != URL_KEYS | set(package.get("extra_url_keys", []))
                 or urls.get("Documentation", "").rstrip("/") != f"https://{package['rtd']}.readthedocs.io")
        result.append(finding("pypi_metadata", "fail" if stale else "pass", "latest published metadata differs; requires next release" if stale else "latest published summary and URL keys match"))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result.append(finding("pypi", "unknown", str(error)))
        result.extend(historical_backlog(package, registry))
    try:
        data = fetch(f"https://api.github.com/repos/{registry['owner']}/{package['repo']}")
        if not isinstance(data, dict) or "description" not in data or "topics" not in data:
            raise ValueError("unexpected GitHub response")
        errors = []
        if data["description"] != package["summary"]:
            errors.append("description")
        if (data.get("homepage") or "").rstrip("/") != f"https://{package['rtd']}.readthedocs.io":
            errors.append("homepage")
        if not set(package["topics"]).issubset(data["topics"]):
            errors.append("required topics")
        result.append(finding("github_about", "fail" if errors else "pass", ", ".join(errors) or "description, homepage and required topics match"))
    except (OSError, ValueError, KeyError) as error:
        result.append(finding("github", "unknown", str(error)))
    return result


def write_reports(report: dict, output: Path) -> None:
    """Write timestamped JSON plus readable Markdown without hiding unknowns."""
    output.mkdir(parents=True, exist_ok=True)
    (output / "CONFORMANCE.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Public package conformance", "", f"Observed: {report['observed_at']} · mode: {report['mode']}", "",
             "GitHub Release pages are optional. Unpublished source versions are preparation states.", "",
             "| Package | Pass | Fail | Known gap | Unknown | Findings |", "|---|---:|---:|---:|---:|---|"]
    for package in report["packages"]:
        checks = package["checks"]
        counts = [sum(c["state"] == state for c in checks) for state in ("pass", "fail", "known-gap", "unknown")]
        notes = "; ".join(f"{c['check']}: {c['detail']}" for c in checks if c["state"] != "pass") or "checked contracts pass"
        lines.append(f"| {package['dist']} | {counts[0]} | {counts[1]} | {counts[2]} | {counts[3]} | {notes.replace('|', '/').replace(chr(10), ' ')} |")
    lines += ["", "This report checks the implemented contracts only; it does not certify numerical correctness, live docs, or release artifact provenance.", ""]
    (output / "CONFORMANCE.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """Inspect existing local clones; network collection is explicit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("."))
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--fail-on-drift", action="store_true")
    args = parser.parse_args()
    registry = load_registry()
    report = {"observed_at": dt.datetime.now(dt.timezone.utc).isoformat(), "mode": "online" if args.online else "offline", "packages": []}
    for package in registry["packages"]:
        root = args.repos_root / package["local_dir"]
        try:
            checks = offline_checks(root, package, registry)
            if args.online:
                checks += network_checks(root, package, registry)
            else:
                checks.append(finding("public_state", "unknown", "network collection disabled"))
                checks.extend(historical_backlog(package, registry))
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            checks = [finding("source", "unknown", str(error))]
        report["packages"].append({"dist": package["dist"], "checks": checks})
    write_reports(report, args.output)
    failures = sum(c["state"] == "fail" for p in report["packages"] for c in p["checks"])
    unknowns = sum(c["state"] == "unknown" for p in report["packages"] for c in p["checks"])
    known = sum(c["state"] == "known-gap" for p in report["packages"] for c in p["checks"])
    print(f"{len(report['packages'])} packages checked; {failures} failed contracts; {known} known gaps; {unknowns} unknown; reports in {args.output}")
    return int(args.fail_on_drift and failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
