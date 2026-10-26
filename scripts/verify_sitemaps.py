"""Check served sitemaps with independent HTTP requests, never a browser session."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
HEADERS = {
    "date", "content-type", "cache-control", "age", "etag", "last-modified",
    "cf-cache-status", "cf-ray", "cf-mitigated", "x-cache", "via", "x-served", "x-rtd-path",
    "x-robots-tag", "location", "retry-after",
}


@dataclass
class Response:
    """One plain-URL response; credentials and cookie headers are never reported."""

    url: str
    status: int
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    error: str = ""

    def record(self) -> dict:
        return {
            "url": self.url, "http_status": self.status,
            "sha256": hashlib.sha256(self.body).hexdigest(),
            "headers": {k: v for k, v in self.headers.items() if k in HEADERS},
            "error": self.error,
        }


class CurlClient:
    """Start a fresh system curl process per GET, without curlrc or browser state."""

    def __init__(self, interval: float = 1.0, timeout: float = 30.0):
        self.executable = shutil.which("curl") or shutil.which("curl.exe")
        if not self.executable:
            raise OSError("System curl is required for independent HTTP verification")
        self.interval, self.timeout = interval, timeout
        self.last_request = 0.0

    def fetch(self, url: str) -> Response:
        delay = self.interval - (time.monotonic() - self.last_request)
        if delay > 0:
            time.sleep(delay)
        self.last_request = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="oss-sitemap-") as directory:
            body, headers = Path(directory) / "body", Path(directory) / "headers"
            command = [
                self.executable, "-q", "--silent", "--show-error",
                "--connect-timeout", str(min(10.0, self.timeout)),
                "--max-time", str(self.timeout), "--max-filesize", "10485760",
                "--dump-header", str(headers), "--output", str(body),
                "--write-out", "%{http_code}", "--url", url,
            ]
            try:
                result = subprocess.run(
                    command, capture_output=True, text=True, check=False,
                    timeout=self.timeout + 5,
                )
            except (OSError, subprocess.SubprocessError) as error:
                return Response(url, 0, error=str(error))
            parsed = {}
            for line in headers.read_text(encoding="iso-8859-1").splitlines() if headers.exists() else []:
                if line.startswith("HTTP/"):
                    parsed = {}  # Discard an earlier proxy CONNECT/interim response.
                elif ":" in line:
                    key, value = line.split(":", 1)
                    key = key.lower()
                    parsed[key] = ", ".join(filter(None, [parsed.get(key), value.strip()]))
            return Response(
                url, int(result.stdout.strip() or "0"),
                body.read_bytes() if body.exists() else b"", parsed,
                result.stderr.strip()[:500] if result.returncode else "",
            )


def site_origin(site: str) -> str:
    """Accept HTTPS origins; plain HTTP is reserved for local fixture servers."""
    parsed = urlsplit(site)
    local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
            or any(c.isspace() for c in site)
            or (parsed.scheme != "https" and not local_http)):
        raise ValueError("Use an HTTPS site origin without a path, credentials or query")
    return site.rstrip("/")


def locations(body: bytes) -> list[str]:
    """Read a page sitemap, preserving duplicates for validation."""
    root = ElementTree.fromstring(body)
    if root.tag != f"{{{NAMESPACE}}}urlset":
        raise ValueError("Expected a sitemap urlset, not an index, HTML or challenge page")
    urls = []
    for entry in root.findall(f"{{{NAMESPACE}}}url"):
        loc = entry.find(f"{{{NAMESPACE}}}loc")
        if loc is None or not loc.text or not loc.text.strip():
            raise ValueError("Sitemap entry has no location")
        urls.append(loc.text.strip())
    if not urls:
        raise ValueError("Sitemap has no page locations")
    return urls


class PageHead(HTMLParser):
    """Read canonical, robots and refresh metadata only inside the HTML head."""

    def __init__(self):
        super().__init__()
        self.in_head = False
        self.canonicals, self.robots = [], []
        self.refresh = False

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
        if not self.in_head:
            return
        a = dict(attrs)
        if tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonicals.append(a.get("href"))
        if tag == "meta" and a.get("name", "").lower() == "robots":
            self.robots.append(a.get("content", ""))
        if tag == "meta" and a.get("http-equiv", "").lower() == "refresh":
            self.refresh = True

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False


def unavailable(response: Response, row: dict) -> bool:
    if (response.error or response.status != 200
            or response.headers.get("cf-mitigated", "").lower() == "challenge"):
        row.update(state="unverified", detail="HTTP access was not verified; no stale-deployment claim")
        row["rate_limited"] = response.status == 429
        return True
    return False


def verify_site(site: str, version: str, client: CurlClient, *, check_pages: bool = False,
                max_pages: int = 1000, expected: list[str] | None = None) -> dict:
    """Compare exact plain URLs; report observed mismatches without inferring their cache layer."""
    site = site_origin(site)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise ValueError("Version must be a URL-safe Read the Docs version slug")
    base = f"{site}/en/{version}/"
    row = {"site": site, "version": version, "state": "unverified", "pages": [],
           "page_checks": "not_requested" if not check_pages else "incomplete"}
    root = client.fetch(site + "/sitemap.xml")
    row["root"] = root.record()
    if unavailable(root, row):
        return row
    version_map = client.fetch(base + "sitemap.xml")
    row["version_sitemap"] = version_map.record()
    if unavailable(version_map, row):
        return row
    try:
        root_urls, version_urls = locations(root.body), locations(version_map.body)
    except (ElementTree.ParseError, ValueError) as error:
        row["detail"] = str(error)
        return row
    row.update(root_urls=root_urls, version_urls=version_urls,
               same_inventory=set(root_urls) == set(version_urls),
               same_bytes=root.body == version_map.body,
               same_etag=root.headers.get("etag") == version_map.headers.get("etag")
               if root.headers.get("etag") and version_map.headers.get("etag") else None)
    problems = []
    for name, urls in (("root", root_urls), ("version", version_urls)):
        if len(urls) != len(set(urls)):
            problems.append(f"{name}: duplicate locations")
        if base + "index.html" in urls:
            problems.append(f"{name}: homepage index.html alias replaces/duplicates its root canonical")
        if any(not u.startswith(base) or urlsplit(u).query or urlsplit(u).fragment for u in urls):
            problems.append(f"{name}: location outside the selected channel or containing query/fragment")
    if not row["same_inventory"]:
        problems.append("Plain root and version HTTP inventories differ; inspect cache evidence")
        row.update(only_in_root=sorted(set(root_urls) - set(version_urls)),
                   only_in_version=sorted(set(version_urls) - set(root_urls)))
    if expected is not None and (set(expected) != set(root_urls) or set(expected) != set(version_urls)):
        problems.append("Served inventories differ from the supplied local build sitemap")
    row.update(state="mismatch" if problems else "verified", problems=problems)
    if not check_pages:
        return row
    if len(version_urls) > max_pages:
        row.update(state="unverified", detail="Page limit prevents complete verification")
        return row
    for url in sorted(set(version_urls)):
        # Never follow an untrusted off-site location from a fetched sitemap.
        if not url.startswith(base) or urlsplit(url).query or urlsplit(url).fragment:
            continue
        response = client.fetch(url)
        page = response.record()
        row["pages"].append(page)
        if unavailable(response, page):
            row.update(state="unverified", detail="Listed pages could not all be verified",
                       rate_limited=page["rate_limited"])
            return row
        head = PageHead()
        head.feed(response.body.decode("utf-8", errors="replace"))
        robots = head.robots + [response.headers.get("x-robots-tag", "")]
        blocked = any(re.search(r"(?:^|[\s,:])(noindex|none)(?:$|[\s,;])", r, re.IGNORECASE) for r in robots)
        passed = head.canonicals == [url] and not head.refresh and not blocked
        page.update(canonicals=head.canonicals, robots=robots,
                    meta_refresh=head.refresh, state="verified" if passed else "mismatch")
        if not passed:
            row["state"] = "mismatch"
    row["page_checks"] = "complete" if len(row["pages"]) == len(set(version_urls)) else "incomplete"
    return row


def verify_sites(sites: list[str], version: str, client: CurlClient, **options) -> dict:
    """Stop on HTTP 429 and preserve the difference between mismatch and unverified."""
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "transport": "independent HTTP GET; fresh system curl process; no browser/curlrc state",
              "sites": [], "not_checked_sites": []}
    for index, site in enumerate(sites):
        row = verify_site(site, version, client, **options)
        report["sites"].append(row)
        if row.get("rate_limited"):
            report["not_checked_sites"] = sites[index + 1:]
            break
    states = {r["state"] for r in report["sites"]}
    report["state"] = ("unverified" if "unverified" in states or report["not_checked_sites"]
                       else "mismatch" if "mismatch" in states else "verified")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", action="append", required=True, help="HTTPS documentation origin; repeatable")
    parser.add_argument("--version", required=True, help="Intended default/indexed channel; QIS uses stable")
    parser.add_argument("--check-pages", action="store_true", help="Check every listed page's canonical and robots tags")
    parser.add_argument("--max-pages", type=int, default=1000)
    parser.add_argument("--interval", type=float, default=1.0, help="Minimum seconds between requests")
    parser.add_argument("--expected-sitemap", type=Path, help="Local build sitemap; requires exactly one --site")
    parser.add_argument("--output", type=Path, help="Explicit JSON evidence file; otherwise write JSON to stdout")
    args = parser.parse_args(argv)
    if args.interval < 0 or args.max_pages < 1 or (args.expected_sitemap and len(args.site) != 1):
        parser.error("Use a nonnegative interval, positive page limit and one site per expected sitemap")
    try:
        expected = locations(args.expected_sitemap.read_bytes()) if args.expected_sitemap else None
        report = verify_sites(args.site, args.version, CurlClient(args.interval),
                              check_pages=args.check_pages, max_pages=args.max_pages, expected=expected)
    except (OSError, ValueError, ElementTree.ParseError) as error:
        report = {"state": "unverified", "error": str(error)}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        except OSError as error:
            print(json.dumps({"state": "unverified", "error": f"Cannot save evidence: {error}"}),
                  file=sys.stderr)
            return 2
    else:
        print(text, end="")
    return {"verified": 0, "mismatch": 1, "unverified": 2}[report["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
