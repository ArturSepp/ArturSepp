"""Regenerate explicitly selected existing stack policies from the public registry."""

import argparse
import json
from pathlib import Path

from conformance import load_registry


def render_policy(registry: dict, package: dict) -> str:
    """Render registry edges and exact development exceptions without prose reasons."""
    own = package["import"]
    core = package["core"]
    optional = sorted({name for names in package["extras"].values() for name in names})
    forbidden = sorted(
        {item["import"] for item in registry["packages"]} - {own} - set(core) - set(optional)
    )
    policy = {
        "schema_version": 1,
        "source_registry": "ArturSepp/scripts/public_registry.json",
        "import": own,
        "core": core,
        "optional": optional,
        "forbidden": forbidden,
        "optional_adapters": [
            {key: value for key, value in entry.items() if key != "reason"}
            for entry in package.get("optional_adapters", [])
        ],
        "development_imports": [
            {key: value for key, value in entry.items() if key != "reason"}
            for entry in package.get("development_imports", [])
        ],
    }
    return json.dumps(policy, indent=2) + "\n"


def main() -> None:
    """Write or check only the explicitly selected existing package policy files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--package", action="append", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    registry = load_registry()
    packages = {package["dist"]: package for package in registry["packages"]}
    selected = []
    for name in dict.fromkeys(args.package):
        if name not in packages:
            parser.error(f"Unknown distribution: {name}")
        package = packages[name]
        target = args.repos_root / package["local_dir"] / ".github/stack-policy.json"
        if not target.is_file():
            parser.error(f"Missing existing stack policy: {target}")
        selected.append((target, render_policy(registry, package)))
    failures = []
    for target, content in selected:
        if args.check:
            if target.read_text(encoding="utf-8") != content:
                failures.append(str(target))
        else:
            target.write_text(content, encoding="utf-8", newline="\n")
    if failures:
        raise SystemExit("Generated stack policies differ:\n" + "\n".join(failures))
    print("Stack policies " + ("verified" if args.check else "generated")
          + f" for {len(selected)} packages")


if __name__ == "__main__":
    main()
