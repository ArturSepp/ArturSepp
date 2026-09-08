"""Generate release-v1 workflow/helper copies from the public registry and templates."""
import argparse
from pathlib import Path

from conformance import load_registry, render_release_template


def main() -> None:
    """Write only the three owned release files into existing package checkouts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failures = []
    for package in load_registry()["packages"]:
        root = args.repos_root / package["local_dir"]
        if not (root / "pyproject.toml").is_file():
            raise SystemExit(f"Missing package checkout: {root}")
        for template, relative in (("release.yml", ".github/workflows/release.yml"),
                                   ("release_guard.py", ".github/scripts/release_guard.py"),
                                   ("publish_tag.py", ".github/scripts/publish_tag.py")):
            content = render_release_template(template, package)
            target = root / relative
            if args.check:
                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    failures.append(str(target))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8", newline="\n")
    if failures:
        raise SystemExit("Generated release files differ:\n" + "\n".join(failures))
    print("Release-v1 files " + ("verified" if args.check else "generated") + " for 10 packages")


if __name__ == "__main__":
    main()
