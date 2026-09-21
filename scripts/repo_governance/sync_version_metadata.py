"""Preview, check, or explicitly apply citation versions from pyproject.toml.

Does not bump the package version, change release dates, stage files, or commit.
"""

from __future__ import annotations

import argparse
import difflib
import re
from pathlib import Path

import tomllib


def proposed_changes(root):
    """Return original/new text pairs without altering any file."""
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = str(project["version"])
    repositories = [
        value.rstrip("/").lower()
        for value in project.get("urls", {}).values()
        if "github.com/" in value and "/issues" not in value and "/discussions" not in value
    ]
    changes = []
    citation = root / "CITATION.cff"
    if citation.exists():
        original = citation.read_text(encoding="utf-8")
        updated, count = re.subn(r"(?m)^version:.*$", f'version: "{version}"', original)
        if count != 1:
            raise ValueError("CITATION.cff needs exactly one top-level version field.")
        # Preserve existing quoting when the value already agrees.
        current = re.search(r"(?m)^version:\s*['\"]?([^'\"\n]+)", original)
        if current and current[1].strip() != version:
            changes.append((citation, original, updated))
    readme = root / "README.md"
    if readme.exists():
        original = readme.read_text(encoding="utf-8")

        def replace(block):
            text = block[0]
            if not any(repo in text.lower() for repo in repositories):
                return text
            return re.sub(
                r"(\bversion\s*=\s*[\{\"])[^}\"]+",
                lambda m: m[1] + version,
                text,
                flags=re.IGNORECASE,
            )

        updated = re.sub(
            r"@software\{.*?(?=\n\})", replace, original, flags=re.DOTALL | re.IGNORECASE
        )
        if updated != original:
            changes.append((readme, original, updated))
    return changes


def main():
    """Default to a reviewable diff; writing requires the explicit --write flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changes = proposed_changes(args.repo.resolve())
    for path, original, updated in changes:
        print(
            "".join(
                difflib.unified_diff(
                    original.splitlines(True),
                    updated.splitlines(True),
                    fromfile=str(path),
                    tofile=str(path),
                )
            ),
            end="",
        )
    if args.write:
        # Check every input before writing any output; never consume a stale working copy.
        if any(path.read_text(encoding="utf-8") != original for path, original, _ in changes):
            raise RuntimeError("Metadata changed during preparation; rerun to review the new diff.")
        for path, _, updated in changes:
            path.write_text(updated, encoding="utf-8", newline="\n")
    if not changes:
        print("Citation versions already match pyproject.toml.")
    raise SystemExit(1 if args.check and changes else 0)


if __name__ == "__main__":
    main()
