"""Collect public sources and all tags for the read-only scheduled audit."""
import argparse
import subprocess
import tempfile
from pathlib import Path

from conformance import load_registry
from workflow_support import DELAYS, backoff, permanent_git_error


def clone_one(url: str, target: Path) -> bool:
    """Use a fresh C-local/runner-temp directory per attempt; never reuse a partial clone."""
    if target.exists():
        raise ValueError(f"Refusing to reuse an existing checkout: {target}")
    for attempt in range(len(DELAYS) + 1):
        attempt_root = Path(tempfile.mkdtemp(prefix=f".{target.name}-clone-", dir=target.parent))
        try:
            result = subprocess.run(
                ["git", "clone", "--filter=blob:none", "--branch", "main", url, str(attempt_root)],
                capture_output=True, text=True, timeout=180, check=False,
            )
        except subprocess.TimeoutExpired:
            result = None
        if result is not None and result.returncode == 0:
            attempt_root.rename(target)
            return True
        if permanent_git_error(result) or attempt == len(DELAYS):
            return False
        backoff("public source clone", attempt)
    raise AssertionError("unreachable")


def main() -> None:
    """Clone into a new task directory, leaving any existing checkout untouched."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    registry = load_registry()
    for package in registry["packages"]:
        target = args.root / package["local_dir"]
        if target.exists():
            raise SystemExit(f"Refusing to reuse an existing checkout: {target}")
        # A failed clone remains visible as an unknown source in the report.
        collected = clone_one(
            f"https://github.com/{registry['owner']}/{package['repo']}.git", target
        )
        print(f"{package['repo']}: {'collected' if collected else 'unavailable'}")



if __name__ == "__main__":
    main()
