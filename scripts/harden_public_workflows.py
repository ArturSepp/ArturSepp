"""Apply bounded HTTP and artifact-read retries without changing validation or upload steps.

This maintainer-only producer edits workflow YAML in registered source exports/checkouts.
It never retries test commands, changes release identities, or performs publication.
"""
from __future__ import annotations

import argparse
import json
import re
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

MARKER = "artifact-read-retry-v1"
PREFIX = "artifact_read_retry_v1_"
DOWNLOAD = "actions/download-artifact@"


def dependency_policy(source: str) -> dict[str, str]:
    policy = {}
    if re.search(r"\buvx?\s|astral-sh/setup-uv@", source):
        policy.update(UV_HTTP_RETRIES="5", UV_HTTP_TIMEOUT="60")
    if re.search(r"\b(?:python\S*\s+-m\s+pip|pip\s+(?:install|download|wheel))\b", source):
        policy.update(PIP_RETRIES="5", PIP_TIMEOUT="60")
    return policy


def artifact_blocks(source: str) -> list[tuple[int, int, str]]:
    """Locate only download-action steps, preserving surrounding YAML and comments."""
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    blocks = []
    for index, line in enumerate(lines):
        match = re.match(r"^( *)(- )?uses: actions/download-artifact@", line)
        if not match:
            continue
        indent = len(match[1]) if match[2] else len(match[1]) - 2
        start = index
        while start >= 0 and not re.match(rf"^ {{{indent}}}- ", lines[start]):
            start -= 1
        if start < 0:
            raise ValueError("Cannot identify the artifact step boundary")
        end = index + 1
        while end < len(lines):
            following = lines[end]
            if following.strip() and len(following) - len(following.lstrip()) <= indent:
                break
            end += 1
        blocks.append((offsets[start], offsets[end], "".join(lines[start:end])))
    return blocks


def retry_artifact(block: str, identifier: str) -> str:
    indent = len(block) - len(block.lstrip(" "))
    lead = " " * indent
    field = lead + "  "
    step = yaml.load("\n".join(line[indent:] for line in block.splitlines()), Loader=yaml.BaseLoader)[0]
    if "id" in step or step.get("continue-on-error", "false") != "false":
        raise ValueError("Artifact steps with caller-visible IDs or advisory failures require review")
    tail = block[len(block.rstrip()):]
    body = block.rstrip() + "\n"

    def attempt(name: str, soft: bool, condition: str | None = None) -> str:
        lines = body.splitlines(keepends=True)
        lines = [line for line in lines if not re.match(rf"^{field}(?:if|continue-on-error):", line)]
        extras = [field + "# " + MARKER + "\n", field + "id: " + name + "\n"]
        if soft:
            extras.append(field + "continue-on-error: true\n")
        chosen = condition if condition is not None else step.get("if")
        if chosen:
            extras.append(field + "if: " + chosen + "\n")
        return lines[0] + "".join(extras) + "".join(lines[1:])

    second, final = identifier + "_retry", identifier + "_final"
    condition1 = f"steps.{identifier}.outcome == 'failure'"
    condition2 = f"steps.{second}.outcome == 'failure'"
    pause1 = (lead + "- name: Wait before retrying artifact download\n" + field + "if: " + condition1
              + "\n" + field + "shell: bash\n" + field + "run: sleep 10\n")
    pause2 = (lead + "- name: Wait before final artifact download attempt\n" + field + "if: " + condition2
              + "\n" + field + "shell: bash\n" + field + "run: sleep 30\n")
    return (attempt(identifier, True) + pause1 + attempt(second, True, condition1)
            + pause2 + attempt(final, False, condition2) + tail)


def validate_artifacts(document: dict[str, Any]) -> None:
    for job in document.get("jobs", {}).values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps", [])
        downloads = [step for step in steps if step.get("uses", "").startswith(DOWNLOAD)]
        primaries = [s for s in downloads if re.fullmatch(PREFIX + r"\d+", s.get("id", ""))]
        if len(downloads) != 3 * len(primaries):
            raise ValueError("Every artifact download must belong to a bounded retry group")
        for primary in primaries:
            identifier = primary["id"]
            group = [next(s for s in downloads if s.get("id") == name) for name in
                     (identifier, identifier + "_retry", identifier + "_final")]
            if [s.get("continue-on-error", "false") for s in group] != ["true", "true", "false"]:
                raise ValueError("The final artifact download failure must remain fatal")
            if any(s["uses"] != primary["uses"] or s.get("with") != primary.get("with") for s in group):
                raise ValueError("Artifact retries must keep the same immutable action and inputs")
            for previous, following in pairwise(group):
                if following.get("if") != f"steps.{previous['id']}.outcome == 'failure'":
                    raise ValueError("Retry must depend on the previous download outcome")


def harden_workflow(source: str, *, template: bool = False) -> str:
    """Make minimal anchored edits; running the producer twice is a no-op."""
    changes = []
    number = 0
    for start, end, block in artifact_blocks(source):
        if MARKER in block:
            continue
        number += 1
        identifier = PREFIX + str(number)
        while re.search(rf"\bid: {re.escape(identifier)}(?:\s|$)", source):
            number += 1
            identifier = PREFIX + str(number)
        changes.append((start, end, retry_artifact(block, identifier)))
    for start, end, replacement in reversed(changes):
        source = source[:start] + replacement + source[end:]
    missing = {key: value for key, value in dependency_policy(source).items()
               if not re.search(rf"^  {key}:", source, re.MULTILINE)}
    if missing:
        addition = "".join(f'  {key}: "{value}"\n' for key, value in missing.items())
        if re.search(r"^env:\s*$", source, re.MULTILINE):
            source = re.sub(r"^env:\s*\n", "env:\n" + addition, source, count=1, flags=re.MULTILINE)
        else:
            source, count = re.subn(r"^jobs:", "env:\n" + addition + "\njobs:", source, count=1,
                                    flags=re.MULTILINE)
            if count != 1:
                raise ValueError("Expected one workflow jobs mapping")
    if not template:
        validate_artifacts(yaml.load(source, Loader=yaml.BaseLoader))
    return source


def workflow_retry_drift(root: Path) -> list[str]:
    """Report missing safeguards so scheduled conformance catches regressions."""
    problems = []
    for path in sorted((root / ".github/workflows").glob("*.y*ml")):
        try:
            source = path.read_text(encoding="utf-8")
            if harden_workflow(source) != source:
                problems.append(f"{path.name}: missing bounded read safeguards")
        except (ValueError, TypeError, KeyError, yaml.YAMLError) as error:
            problems.append(f"{path.name}: {error}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--package")
    args = parser.parse_args()
    registry = json.loads(Path(__file__).with_name("public_registry.json").read_text(encoding="utf-8"))
    changed = []
    for package in registry["packages"]:
        if args.package and args.package not in (package["repo"], package["dist"]):
            continue
        folder = args.repos_root / package["local_dir"] / ".github/workflows"
        if not folder.is_dir():
            raise ValueError(f"Missing registered workflow directory: {folder}")
        for path in sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")]):
            source = path.read_text(encoding="utf-8")
            proposed = harden_workflow(source)
            if proposed != source:
                changed.append(str(path))
                if not args.check:
                    path.write_text(proposed, encoding="utf-8", newline="\n")
    if args.check and changed:
        raise SystemExit("Workflow retry safeguards missing:\n" + "\n".join(changed))
    print(json.dumps({"changed_workflows": len(changed), "check": args.check}))


if __name__ == "__main__":
    main()
