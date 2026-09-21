"""Read-only audit of the public stack's commit checker adoption and branch protection."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path):
    """Hash a checker independent of checkout line endings."""
    return hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()


def output(args):
    """Read Git/GitHub metadata without modifying it."""
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def consumer_targets(registry, package):
    """Derive the smallest environment for every core or optional consumer edge."""
    targets = []
    for consumer in registry["packages"]:
        extras = []
        if package["import"] in consumer.get("core", []):
            extras.append("")
        extras.extend(
            extra
            for extra, dependencies in consumer.get("extras", {}).items()
            if package["import"] in dependencies
        )
        if not extras:
            continue
        extra = min(extras, key=lambda name: (name == "all", len(name), name))
        targets.append(
            {
                "repository": f"ArturSepp/{consumer['repo']}",
                "module": consumer["import"],
                "extra": extra,
                "sdk": package["import"] == "bbg_fetch",
            }
        )
    return targets


def main():
    """Report local copies/hooks and optional live protection settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--require-hooks", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    registry = json.loads((here / "portfolio_registry.json").read_text())
    expected = digest(here / "oss_checks.py")
    public = json.loads((here.parent / "public_registry.json").read_text())
    packages = {item["local_dir"]: item for item in public["packages"]}
    rows = []
    for entry in registry["repositories"]:
        if entry["visibility"] != "public-package":
            continue
        root = args.repos_root / entry["directory"]
        checker = root / ".github/oss_checks.py"
        row = {
            "repository": entry["name"],
            "checker_matches": checker.exists() and digest(checker) == expected,
            "hook_path": output(["git", "-C", str(root), "config", "--get", "core.hooksPath"]),
            "required_workflow": (root / ".github/workflows/required.yml").is_file(),
            "reference_checker_matches": (root / ".github/check_new_references.py").exists()
            and digest(root / ".github/check_new_references.py")
            == digest(here / "check_new_references.py"),
        }
        profile_path = root / ".github/oss-checks.json"
        profile = json.loads(profile_path.read_text()) if profile_path.exists() else {}
        actual_edges = [
            {key: value for key, value in edge.items() if key != "commit"}
            for edge in profile.get("consumers", [])
        ]
        row["consumer_graph_matches"] = actual_edges == consumer_targets(
            public, packages[entry["directory"]]
        )
        if args.online:
            raw = output(["gh", "api", f"repos/ArturSepp/{entry['name']}/branches/main/protection"])
            protection = json.loads(raw) if raw else {}
            row["main_protected"] = bool(protection)
            row["admins_enforced"] = protection.get("enforce_admins", {}).get("enabled", False)
            checks = protection.get("required_status_checks") or {}
            row["required_contexts"] = checks.get("contexts", [])
            row["up_to_date_required"] = checks.get("strict", False)
            row["pull_request_required"] = (
                protection.get("required_pull_request_reviews") is not None
            )
        rows.append(row)
    report = json.dumps({"checker_version": "1.0.0", "repositories": rows}, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)
    passed = all(
        row["checker_matches"]
        and row["reference_checker_matches"]
        and row["required_workflow"]
        and row["consumer_graph_matches"]
        for row in rows
    )
    if args.require_hooks:
        passed = passed and all(row["hook_path"] == ".githooks" for row in rows)
    if args.online:
        passed = passed and all(
            row["main_protected"]
            and row["admins_enforced"]
            and row["up_to_date_required"]
            and row["pull_request_required"]
            and "Required checks" in row["required_contexts"]
            for row in rows
        )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
