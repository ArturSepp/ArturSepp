"""Read-only daily documentation monitor; network findings never fail normal commits."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree

from verify_sitemaps import (
    CurlClient,
    Response,
    locations,
    page_metadata,
    read_redirects,
    site_origin,
)

HERE = Path(__file__).resolve().parent


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class Client:
    """Two package workers share host pacing, an in-run cache and a global throttle stop."""

    def __init__(self):
        self.guard = threading.Lock()
        self.hosts = {}
        self.cache = {}
        self.stopped = threading.Event()

    def fetch(self, url):
        with self.guard:
            host = urlsplit(url).netloc
            if host not in self.hosts:
                self.hosts[host] = (threading.Lock(), CurlClient(interval=1.0))
            lock, transport = self.hosts[host]
        with lock:
            if url in self.cache:
                return self.cache[url]
            if self.stopped.is_set():
                return Response(url, 0, error="Not requested: global HTTP 429 stop")
            response = transport.fetch(url)
            self.cache[url] = response
            if response.status == 429:
                self.stopped.set()
            return response


def uncertain(response):
    text = response.body[:10000].decode("utf-8", errors="replace").lower()
    return bool(
        response.error
        or response.status in {0, 401, 403, 408, 425, 429}
        or response.status >= 500
        or response.headers.get("cf-mitigated", "").lower() == "challenge"
        or any(
            marker in text
            for marker in (
                "<title>just a moment",
                "<title>attention required",
                "cf-chl-",
                "<title>verify you are human",
            )
        )
    )


def safe_page(url, base):
    parsed = urlsplit(url)
    return (
        url.startswith(base)
        and not parsed.query
        and not parsed.fragment
        and not parsed.username
        and not parsed.password
        and not any(part in {".", ".."} for part in unquote(parsed.path).split("/"))
        and not any(c.isspace() for c in url)
    )


def check_package(package, seed, history, client, origins):
    repo, site = package["repo"], site_origin(seed["site"])
    version, channels = seed["version"], seed["channels"]
    base = f"{site}/en/{version}/"
    rows, evidence = {}, {}
    ledger = set(seed["pages"]) | set(history.get("pages", []))
    legacy = set(seed["legacy_paths"]) | set(history.get("legacy_paths", []))

    def observe(key, state, detail, url):
        rows[key] = {"repository": repo, "state": state, "detail": detail, "url": url}

    def fetch(url):
        response = client.fetch(url)
        evidence[url] = response.record()
        return response

    def page(url, *, archive=False, destination=False):
        response = fetch(url)
        key = ("destination:" if destination else "page:") + url
        if uncertain(response):
            observe(key, "unverified", "Access/transport unavailable", url)
            return None
        if response.status != 200:
            observe(
                key, "broken", f"Expected direct HTTP 200; got {response.status}", url
            )
            return None
        head, _, passed = page_metadata(response, url)
        if archive:
            passed = head.canonicals == [url] and not head.refresh
        observe(
            key,
            "healthy" if passed else "broken",
            "Canonical/indexability metadata"
            if not passed
            else "Direct page available",
            url,
        )
        return head

    root, version_map = fetch(site + "/sitemap.xml"), fetch(base + "sitemap.xml")
    maps_key = "sitemap:" + site
    current = set()
    maps_available = not (uncertain(root) or uncertain(version_map))
    if not maps_available:
        observe(
            maps_key,
            "unverified",
            "Sitemap access unavailable; package circuit breaker",
            site,
        )
    elif root.status != 200 or version_map.status != 200:
        observe(maps_key, "broken", "Root/version sitemap is not HTTP 200", site)
        maps_available = False
    else:
        try:
            roots, versions = locations(root.body), locations(version_map.body)
            valid = (
                set(roots) == set(versions)
                and len(roots) == len(set(roots))
                and len(versions) == len(set(versions))
                and base + "index.html" not in roots
                and base + "index.html" not in versions
                and all(safe_page(u, base) for u in roots + versions)
            )
            observe(
                maps_key,
                "healthy" if valid else "broken",
                "Root/version canonical inventories agree"
                if valid
                else "Sitemap inventory mismatch",
                site,
            )
            current = {u for u in roots + versions if safe_page(u, base)}
            ledger.update(u[len(base) :] for u in current)
        except (ElementTree.ParseError, ValueError):
            observe(
                maps_key,
                "unverified",
                "Invalid XML or challenge; inventory not replaced",
                site,
            )
            maps_available = False

    manifest_url = (
        f"https://raw.githubusercontent.com/{package['owner']}/{repo}"
        "/main/tools/docs_redirects.json"
    )
    manifest_response = fetch(manifest_url)
    rules = []
    required = bool(legacy or history.get("manifest_seen"))
    manifest_seen = history.get("manifest_seen", False)
    if (
        manifest_response.status == 404
        and not required
        and not uncertain(manifest_response)
    ):
        observe("manifest:" + repo, "healthy", "Optional manifest absent", manifest_url)
    elif manifest_response.status != 200 or uncertain(manifest_response):
        observe(
            "manifest:" + repo,
            "unverified",
            "Published redirect manifest unavailable",
            manifest_url,
        )
    else:
        try:
            with tempfile.TemporaryDirectory(
                prefix="oss-monitor-manifest-"
            ) as directory:
                path = Path(directory) / "manifest.json"
                path.write_bytes(manifest_response.body)
                rules = read_redirects(path, site)
            if any(
                site_origin(urlunsplit((*urlsplit(r["to_url"])[:2], "", "", "")))
                not in origins
                for r in rules
            ):
                raise ValueError("Destination outside registered documentation origins")
            legacy.update(r["from_url"] for r in rules)
            manifest_seen = True
            observe(
                "manifest:" + repo,
                "healthy",
                "Published redirect manifest read",
                manifest_url,
            )
        except (KeyError, ValueError, TypeError, AttributeError):
            observe(
                "manifest:" + repo,
                "unverified",
                "Invalid published redirect manifest",
                manifest_url,
            )
            rules = []
    expected = {r["from_url"]: r["to_url"] for r in rules}

    def historical(url, target=None):
        response = fetch(url)
        key = "page:" + url
        if uncertain(response):
            observe(key, "unverified", "Historical URL access unavailable", url)
            return
        if response.status == 200:
            page(url, archive=url not in current)
            return
        destination = urljoin(url, response.headers.get("location", ""))
        parsed = urlsplit(destination)
        origin = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        if (
            response.status != 301
            or origin not in origins
            or parsed.query
            or not safe_page(destination.split("#")[0], origin + "/en/")
        ):
            observe(
                key,
                "broken",
                f"Expected safe permanent redirect; HTTP {response.status}",
                url,
            )
            return
        if target and destination != target:
            observe(
                key, "broken", "Location differs from published reviewed mapping", url
            )
        elif url in current:
            observe(key, "broken", "Current canonical sitemap page redirects", url)
        elif (
            target is None
            and required
            and urlsplit(url).path.split("/", 3)[-1] in {p.lstrip("/") for p in legacy}
            and not rules
        ):
            observe(
                key,
                "unverified",
                "Cannot compare mapping without published manifest",
                url,
            )
        else:
            observe(key, "healthy", "Permanent Location verified", url)
        target_page = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        head = page(target_page, destination=True)
        if parsed.fragment:
            observe(
                "anchor:" + destination,
                "unverified"
                if head is None
                else "healthy"
                if unquote(parsed.fragment) in head.ids
                else "broken",
                "Replacement fragment",
                destination,
            )

    if maps_available:
        for path in sorted(ledger):
            url = base + path
            if url in current:
                page(url)
            else:
                historical(url, expected.get("/" + path))
        for path in sorted(legacy):
            for channel in channels:
                url = site + "/en/" + channel + path
                if url not in current:
                    historical(url, expected.get(path))

    return {
        "repository": repo,
        "site": site,
        "version": version,
        "current_pages": len(current),
        "known_pages": len(ledger),
        "legacy_rules": len(legacy),
        "observations": rows,
        "evidence": list(evidence.values()),
        "history": {
            "pages": sorted(ledger),
            "legacy_paths": sorted(legacy),
            "manifest_seen": manifest_seen,
        },
    }


def reconcile(previous, observations, timestamp, packages):
    """Confirm twice >=1h apart; unavailable observations cannot confirm or recover."""
    checks, alerts, recoveries = {}, [], []
    stamp = datetime.fromisoformat(timestamp)
    for key in sorted(set(previous.get("checks", {})) | set(observations)):
        old = previous.get("checks", {}).get(key, {})
        if key not in observations and not old.get("active") and not old.get("streak"):
            continue
        row = observations.get(
            key,
            {
                **old.get("observation", {}),
                "state": "unverified",
                "detail": "Not observed in this incomplete run",
            },
        )
        entry = {
            "active": old.get("active", False),
            "streak": 0,
            "first_failure": None,
            "observation": row,
        }
        if row["state"] == "broken":
            entry["streak"] = old.get("streak", 0) + 1
            entry["first_failure"] = old.get("first_failure") or timestamp
            elapsed = (
                stamp - datetime.fromisoformat(entry["first_failure"])
            ).total_seconds()
            if not entry["active"] and entry["streak"] >= 2 and elapsed >= 3600:
                entry["active"] = True
                alerts.append({"key": key, **row})
        elif row["state"] == "healthy" and entry["active"]:
            entry["active"] = False
            recoveries.append({"key": key, **row})
        checks[key] = entry
    warnings, monitoring_recoveries, availability = [], [], {}
    for repo in packages:
        incomplete = any(
            not key.startswith("anchor:")
            and v["observation"].get("repository") == repo
            and v["observation"]["state"] == "unverified"
            for key, v in checks.items()
        )
        old = previous.get("availability", {}).get(repo, {})
        streak = old.get("streak", 0) + 1 if incomplete else 0
        active = old.get("active", False)
        if streak >= 3 and not active:
            warnings.append(repo)
            active = True
        elif not incomplete and active:
            monitoring_recoveries.append(repo)
            active = False
        availability[repo] = {"streak": streak, "active": active}
    return {"checks": checks, "availability": availability}, {
        "alerts": alerts,
        "recoveries": recoveries,
        "monitor_warnings": warnings,
        "monitor_recoveries": monitoring_recoveries,
        "notification_required": bool(
            alerts or recoveries or warnings or monitoring_recoveries
        ),
    }


def load_configuration(registry_path, seed_path):
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    if seed.get("schema_version") != 1:
        raise ValueError("Unsupported monitor seed")
    packages = [{**p, "owner": registry["owner"]} for p in registry["packages"]]
    if {p["repo"] for p in packages} != set(seed["packages"]):
        raise ValueError(
            "Registry/seed packages differ; review documentation channels before monitoring"
        )
    for package in packages:
        config = seed["packages"][package["repo"]]
        if config["site"] != f"https://{package['rtd']}.readthedocs.io":
            raise ValueError("Seed site disagrees with registry")
        for version in [config["version"], *config["channels"]]:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
                raise ValueError("Invalid documentation channel")
        base = config["site"] + "/en/" + config["version"] + "/"
        if any(not safe_page(base + p, base) for p in config["pages"]):
            raise ValueError("Unsafe seed page path")
        if any(
            not p.startswith("/") or not safe_page(base + p[1:], base)
            for p in config["legacy_paths"]
        ):
            raise ValueError("Unsafe legacy source path")
    return packages, seed["packages"]


@contextmanager
def exclusive_run(directory):
    lock = directory / "monitor.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        yield False
        return
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"pid": os.getpid(), "started_at_utc": now_utc()}, stream)
        yield True
    finally:
        lock.unlink()


def run(packages, seeds, previous, client, timestamp):
    origins = {s["site"] for s in seeds.values()}

    def worker(package):
        repo = package["repo"]
        return check_package(
            package,
            seeds[repo],
            previous.get("history", {}).get(repo, {}),
            client,
            origins,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, packages))
    observations = {
        key: value
        for result in results
        for key, value in result["observations"].items()
    }
    state, notifications = reconcile(previous, observations, timestamp, seeds)
    state.update(
        schema_version=1,
        checked_at_utc=timestamp,
        history={r["repository"]: r["history"] for r in results},
    )
    states = [v["observation"]["state"] for v in state["checks"].values()]
    report = {
        "checked_at_utc": timestamp,
        **notifications,
        "state": "unverified"
        if "unverified" in states
        else "findings"
        if "broken" in states
        else "verified",
        "counts": {
            name: states.count(name) for name in ("healthy", "broken", "unverified")
        },
        "active_issues": [k for k, v in state["checks"].items() if v["active"]],
        "packages": [{k: v for k, v in r.items() if k != "history"} for r in results],
    }
    return state, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=HERE / "public_registry.json")
    parser.add_argument(
        "--seed", type=Path, default=HERE / "documentation_monitor_seed.json"
    )
    parser.add_argument("--state-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        directory = args.state_dir.resolve()
        if "onedrive" in {p.lower() for p in directory.parts}:
            raise ValueError("Monitor state and evidence must be outside OneDrive")
        packages, seeds = load_configuration(args.registry, args.seed)
        directory.mkdir(parents=True, exist_ok=True)
        with exclusive_run(directory) as acquired:
            if not acquired:
                print(
                    json.dumps(
                        {
                            "state": "skipped",
                            "reason": "Monitor lock exists; no requests made",
                        }
                    )
                )
                return 0
            state_path = directory / "state.json"
            previous = (
                json.loads(state_path.read_text(encoding="utf-8"))
                if state_path.exists()
                else {}
            )
            if previous and previous.get("schema_version") != 1:
                raise ValueError(
                    "Unsupported persistent state; preserve it for migration"
                )
            stamp = now_utc()
            state, report = run(packages, seeds, previous, Client(), stamp)
            report_path = directory / (
                "report-" + stamp.replace(":", "").replace("+", "_") + ".json"
            )
            atomic_json(report_path, report)
            atomic_json(directory / "latest.json", report)
            atomic_json(state_path, state)
            print(
                json.dumps(
                    {k: v for k, v in report.items() if k != "packages"}
                    | {"report": str(report_path)}
                )
            )
        return (
            0  # Findings/access failures belong to notifications, never a commit gate.
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "monitor_error", "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
