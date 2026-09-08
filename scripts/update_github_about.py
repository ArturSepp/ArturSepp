"""Print registry-driven About updates; apply only with an explicit --apply flag."""
import argparse
import json
import subprocess

from conformance import load_registry


def commands(registry: dict) -> list[list[str]]:
    """Add minimum topics without deleting existing topics or changing community settings."""
    result = []
    for package in registry["packages"]:
        command = ["gh", "repo", "edit", f"{registry['owner']}/{package['repo']}",
                   "--description", package["summary"], "--homepage",
                   f"https://{package['rtd']}.readthedocs.io"]
        for topic in package["topics"]:
            command += ["--add-topic", topic]
        result.append(command)
    return result


def main() -> None:
    """Render exact argument arrays before any opt-in mutations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    planned = commands(load_registry())
    print(json.dumps({"mode": "apply" if args.apply else "dry-run", "commands": planned}, indent=2))
    if args.apply:
        for command in planned:
            subprocess.run(command, check=True, timeout=60)


if __name__ == "__main__":
    main()
