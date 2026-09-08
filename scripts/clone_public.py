"""Collect public sources and all tags for the read-only scheduled audit."""
import argparse
import subprocess
from pathlib import Path

from conformance import load_registry


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
        result = subprocess.run(["git", "clone", "--filter=blob:none", "--branch", "main",
                                 f"https://github.com/{registry['owner']}/{package['repo']}.git",
                                 str(target)], capture_output=True, text=True, timeout=180)
        print(f"{package['repo']}: {'collected' if result.returncode == 0 else 'unavailable'}")


if __name__ == "__main__":
    main()
