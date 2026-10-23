"""Publish public Pepy dashboard totals as daily profile badge snapshots.

Read the visible dashboard summary and retain exact counts in counts.json.
Display total downloads rounded to thousands (K), keeping counts below 1,000 exact.
Fail before writing any output if a source is unavailable or its format changes.
The workflow publishes only profile-downloads/ on automation/reports; main and
the generated conformance reports are never changed by this collector.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from build_stats import REPOS


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def parse_counts(html: str, slug: str) -> dict:
    parser = VisibleText()
    parser.feed(html)
    text = " ".join(" ".join(parser.parts).split())
    integer = r"(\d{1,3}(?:,\d{3})+|\d+)"
    matches = re.findall(
        rf"(?<![\w-]){re.escape(slug)}\s+has been downloaded\s+{integer}"
        rf"\s+times in total on PyPI\s*,?\s*including\s+{integer}"
        r"\s+in the last 30 days", text, flags=re.IGNORECASE,
    )
    if len(matches) != 1:
        raise ValueError(f"{slug}: expected one Pepy download summary, found {len(matches)}")
    total, month = (int(value.replace(",", "")) for value in matches[0])
    if month > total:
        raise ValueError(f"{slug}: last-30-days downloads exceed total downloads")
    return {"month": month, "total": total}


def fetch_counts(slug: str) -> dict:
    source = f"https://pepy.tech/projects/{slug}"
    request = Request(source, headers={"User-Agent": "ArturSepp-profile-downloads/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                counts = parse_counts(response.read().decode("utf-8"), slug)
            return {"source": source, **counts}
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def badge(value: str, title: str, color: str = "#4c1") -> str:
    width = 16 + 7 * len(value)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" '
        f'role="img" aria-label="{escape(title, quote=True)}">\n'
        f'<title>{escape(title)}</title>\n'
        f'<rect width="{width}" height="20" rx="3" fill="{color}"/>\n'
        f'<text x="{width / 2:g}" y="14" fill="#fff" text-anchor="middle" '
        f'font-family="DejaVu Sans Mono,monospace" font-size="11">{escape(value)}</text>\n'
        '</svg>\n'
    )


def refresh(output: Path) -> dict:
    slugs = list(REPOS.values())
    with ThreadPoolExecutor(max_workers=4) as pool:
        packages = dict(zip(slugs, pool.map(fetch_counts, slugs)))
    observed = datetime.now(timezone.utc)
    stamp = observed.strftime("%Y-%m-%d %H:%M UTC")
    snapshot = {"observed_at": observed.isoformat(), "packages": packages}
    # Prepare every file before touching the previous successful snapshot.
    files = {"counts.json": json.dumps(snapshot, indent=2) + "\n",
             "updated.svg": badge(observed.strftime("%Y-%m-%d"), f"Downloads checked {stamp}")}
    for slug, counts in packages.items():
        total = counts["total"]
        value = str(total) if total < 1000 else f"{(total + 500) // 1000}K"
        files[f"{slug}-total.svg"] = badge(
            value, f"{slug}: {total:,} downloads (all time); {stamp}", color="#007ec6")
    output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (output / name).write_text(content, encoding="utf-8", newline="\n")
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = refresh(args.output)
    print(f"Verified {len(snapshot['packages'])} Pepy pages at {snapshot['observed_at']}")


if __name__ == "__main__":
    main()
