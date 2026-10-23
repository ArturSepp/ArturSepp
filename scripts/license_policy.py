"""Check one manually reviewed runtime against its complete retained notices.

Inputs are a saved runtime-only ``pip inspect`` record, the independently reviewed
evidence record, and that installation's site-packages directory. The review owns
licence interpretation, including alternatives, compiler exceptions and vendor
terms. This assertion neither parses arbitrary SPDX expressions nor licenses a
whole environment, future resolution or different platform.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


# Exact ordinary identifiers only. A substring test would incorrectly reject a
# reviewed FTL alternative or the GCC runtime exception used by NumPy/SciPy.
ORDINARY_COPYLEFT = {
    f"{family}-{version}-{suffix}"
    for family, versions in (("GPL", ("2.0", "3.0")),
                             ("LGPL", ("2.0", "2.1", "3.0")),
                             ("AGPL", ("1.0", "3.0")))
    for version in versions for suffix in ("only", "or-later")
} | {"GPL", "GPLv2", "GPLv2+", "GPLv3", "GPLv3+", "LGPL", "AGPL"}


def normalized(name: str) -> str:
    """Normalize distribution names without interpreting requirement syntax."""
    return re.sub(r"[-_.]+", "-", name).lower()


def fingerprint(metadata: dict) -> dict:
    """Keep every licence metadata field used in the original L2 review."""
    return {
        "license_expression": metadata.get("license_expression"),
        "license": metadata.get("license"),
        "license_file": metadata.get("license_file", []),
        "license_classifiers": [value for value in metadata.get("classifier", [])
                                if value.startswith("License ::")],
    }


def verify_file(site: Path, evidence: dict, kind: str) -> None:
    """Compare full bytes, keeping every evidence path inside site-packages."""
    relative = Path(evidence["path"])
    path = (site / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(site.resolve()):
        raise ValueError(f"Invalid {kind} evidence path: {relative}")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != evidence["sha256"]:
        raise ValueError(f"Changed/missing complete {kind}: {relative}")


def check_runtime(inspect: dict, review: dict, site: Path) -> dict:
    """Fail closed unless the exact recorded runtime has complete reviewed evidence.

    L2's evidence format is accepted directly. A later bounded review can name its
    platform explicitly; omitting it retains L2's Windows/CPython 3.12 scope.
    Only pip is excluded as seeded installer tooling. Test tools must not appear
    in the saved base inventory. Empty/partial reviews and duplicate names fail.
    """
    expected_platform = review.get("platform", {
        "sys_platform": "win32", "python_version": "3.12", "platform_machine": "AMD64",
    })
    if not {"sys_platform", "python_version", "platform_machine"} <= expected_platform.keys():
        raise ValueError("Incomplete reviewed platform")
    for field in expected_platform:
        if not expected_platform.get(field) or inspect["environment"].get(field) != expected_platform[field]:
            raise ValueError(f"Unreviewed platform: {field}")
    expected = review["packages"]
    if not expected or not review.get("scope") or not review.get("qualifications"):
        raise ValueError("Incomplete reviewed scope/qualifications/packages")
    if any(name != normalized(name) for name in expected):
        raise ValueError("Review package names must be normalized")
    installed = {}
    notices = 0
    for record in inspect["installed"]:
        metadata = record["metadata"]
        name = normalized(metadata["name"])
        if name == "pip":
            continue
        if name in installed:
            raise ValueError(f"Duplicate runtime package: {name}")
        if any(metadata.get(field) in ORDINARY_COPYLEFT for field in ("license_expression", "license")):
            raise ValueError(f"Ordinary copyleft licence: {name}")
        if name not in expected:
            raise ValueError(f"Unreviewed package: {name}")
        entry = expected[name]
        if metadata["version"] != entry["version"]:
            raise ValueError(f"Unreviewed version: {name} {metadata['version']}")
        if fingerprint(metadata) != entry["metadata_licence"]:
            raise ValueError(f"Unreviewed licence metadata: {name}")
        if entry["disposition"] not in {"reviewed", "reviewed_with_compiler_exception"}:
            raise ValueError(f"Unresolved licence review: {name}")
        if not entry.get("reviewed_terms") or not entry.get("notices"):
            raise ValueError(f"Incomplete terms/notices review: {name}")
        for notice in entry["notices"]:
            verify_file(site, notice, "notice")
            notices += 1
        installed[name] = metadata["version"]
    if set(installed) != set(expected):
        raise ValueError(f"Missing reviewed packages: {sorted(set(expected) - set(installed))}")
    for binary in review["native_binaries"]:
        verify_file(site, binary, "native binary")
    return {
        "status": "passed_for_recorded_runtime_with_documented_qualifications",
        "scope": review["scope"], "platform": expected_platform,
        "runtime_packages": installed, "runtime_count": len(installed),
        "notice_count": notices, "native_binary_count": len(review["native_binaries"]),
        "installer_tooling_excluded": ["pip"],
        "ordinary_gpl_agpl_lgpl_findings": 0, "unresolved_runtime_licence_identities": 0,
        "qualifications": review["qualifications"],
    }


def check_files(inspect_path: Path, review_path: Path, site: Path) -> dict:
    """Return a receipt tied to both exact evidence inputs; propagate failures."""
    receipt = check_runtime(
        json.loads(inspect_path.read_text(encoding="utf-8-sig")),
        json.loads(review_path.read_text(encoding="utf-8-sig")), site,
    )
    for name, path in (("inspect", inspect_path), ("review", review_path)):
        receipt[f"{name}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return receipt


def main() -> int:
    """Assert a recorded base independently of the wider conformance backlog."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = check_files(args.inspect, args.review, args.site)
    except (OSError, ValueError, KeyError, TypeError) as error:
        receipt = {"status": "failed", "detail": str(error)}
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return int(receipt["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
