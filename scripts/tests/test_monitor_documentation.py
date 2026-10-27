"""Offline contracts for documentation monitoring and notification deltas."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import monitor_documentation as monitor
from verify_sitemaps import Response

SITE = "https://docs.readthedocs.io"
BASE = SITE + "/en/stable/"
PACKAGE = {"repo": "Example", "owner": "Owner", "rtd": "docs"}
MANIFEST = (
    "https://raw.githubusercontent.com/Owner/Example/main/tools/docs_redirects.json"
)
SEED = {
    "site": SITE,
    "version": "stable",
    "channels": ["latest", "stable"],
    "pages": ["", "old.html"],
    "legacy_paths": [],
}


def xml(urls):
    return (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{u}</loc></url>" for u in urls)
        + "</urlset>"
    ).encode()


def html(url, ids=""):
    return f'<html><head><link rel="canonical" href="{url}"></head><body>{ids}</body></html>'.encode()


class FixtureClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        if url in self.responses:
            return self.responses[url]
        return Response(url, 404)


def fixtures(urls=None):
    urls = urls or [BASE]
    return {
        SITE + "/sitemap.xml": Response(SITE + "/sitemap.xml", 200, xml(urls)),
        BASE + "sitemap.xml": Response(BASE + "sitemap.xml", 200, xml(urls)),
        **{u: Response(u, 200, html(u)) for u in urls},
    }


class MonitorTests(unittest.TestCase):
    def check(self, responses, history=None, seed=None):
        return monitor.check_package(
            PACKAGE, seed or SEED, history or {}, FixtureClient(responses), {SITE}
        )

    def test_history_survives_removed_sitemap_page(self):
        first = self.check(fixtures([BASE, BASE + "new.html"]))
        second = self.check(fixtures(), first["history"])
        self.assertIn("new.html", second["history"]["pages"])
        self.assertEqual(
            second["observations"]["page:" + BASE + "new.html"]["state"], "broken"
        )
        self.assertEqual(second["observations"]["sitemap:" + SITE]["state"], "healthy")

    def test_confirmation_and_recovery_deduplicate(self):
        previous = {}

        def step(state, stamp):
            nonlocal previous
            previous, delta = monitor.reconcile(
                previous,
                {"page:u": {"state": state, "repository": "Example", "url": "u"}},
                stamp,
                ["Example"],
            )
            return delta

        self.assertFalse(
            step("broken", "2026-10-27T08:00:00+00:00")["notification_required"]
        )
        self.assertFalse(
            step("broken", "2026-10-27T08:10:00+00:00")["notification_required"]
        )
        self.assertEqual(len(step("broken", "2026-10-28T08:00:00+00:00")["alerts"]), 1)
        self.assertFalse(
            step("broken", "2026-10-29T08:00:00+00:00")["notification_required"]
        )
        self.assertFalse(step("unverified", "2026-10-30T08:00:00+00:00")["recoveries"])
        self.assertEqual(
            len(step("healthy", "2026-10-31T08:00:00+00:00")["recoveries"]), 1
        )
        self.assertFalse(
            step("healthy", "2026-11-01T08:00:00+00:00")["notification_required"]
        )

    def test_unverified_resets_pending_confirmation(self):
        previous = {}
        for day, status in [(27, "broken"), (28, "unverified"), (29, "broken")]:
            previous, delta = monitor.reconcile(
                previous,
                {"u": {"state": status, "repository": "Example"}},
                f"2026-10-{day}T08:00:00+00:00",
                ["Example"],
            )
            self.assertFalse(delta["alerts"])

    def test_missing_observation_cannot_recover_active_issue(self):
        previous = {
            "checks": {
                "u": {
                    "active": True,
                    "observation": {"repository": "Example", "state": "broken"},
                }
            }
        }
        state, delta = monitor.reconcile(
            previous, {}, "2026-10-27T08:00:00+00:00", ["Example"]
        )
        self.assertTrue(state["checks"]["u"]["active"])
        self.assertFalse(delta["recoveries"])

    def test_transient_responses_never_mean_broken(self):
        for response in [
            Response(BASE, 503),
            Response(BASE, 403),
            Response(BASE, 429),
            Response(BASE, 0, error="timeout"),
            Response(BASE, 200, b"<title>Just a moment...</title>"),
        ]:
            with self.subTest(response=response):
                responses = fixtures()
                responses[BASE] = response
                result = self.check(responses)
                self.assertEqual(
                    result["observations"]["page:" + BASE]["state"], "unverified"
                )

    def test_real_404_and_canonical_defect_are_broken(self):
        for response in [
            Response(BASE, 404),
            Response(BASE, 410),
            Response(BASE, 200, html(BASE + "wrong")),
        ]:
            responses = fixtures()
            responses[BASE] = response
            self.assertEqual(
                self.check(responses)["observations"]["page:" + BASE]["state"], "broken"
            )

    def test_sitemap_outage_circuit_breaker_preserves_history(self):
        responses = fixtures()
        responses[SITE + "/sitemap.xml"] = Response(SITE + "/sitemap.xml", 503)
        client = FixtureClient(responses)
        result = monitor.check_package(PACKAGE, SEED, {}, client, {SITE})
        self.assertNotIn(BASE + "old.html", client.calls)
        self.assertIn("old.html", result["history"]["pages"])

    def test_optional_absent_manifest_and_required_unavailable(self):
        first = self.check(fixtures())
        self.assertEqual(first["observations"]["manifest:Example"]["state"], "healthy")
        second = self.check(fixtures(), {"manifest_seen": True})
        self.assertEqual(
            second["observations"]["manifest:Example"]["state"], "unverified"
        )

    def test_reviewed_redirect_location_and_anchor_on_both_channels(self):
        target = BASE + "#section"
        rule = {
            "from_url": "/old.html",
            "to_url": target,
            "redirect_type": "page",
            "http_status": 301,
            "force": False,
            "enabled": True,
        }
        responses = fixtures()
        responses[BASE] = Response(BASE, 200, html(BASE, '<h1 id="section">x</h1>'))
        responses[MANIFEST] = Response(
            MANIFEST,
            200,
            json.dumps(
                {"schema_version": 1, "site": SITE, "redirects": [rule]}
            ).encode(),
        )
        for channel in ("stable", "latest"):
            url = SITE + f"/en/{channel}/old.html"
            responses[url] = Response(url, 301, headers={"location": target})
        result = self.check(responses)
        self.assertEqual(result["observations"]["anchor:" + target]["state"], "healthy")
        wrong = SITE + "/en/latest/old.html"
        responses[wrong] = Response(wrong, 301, headers={"location": BASE + "#missing"})
        result = self.check(responses)
        self.assertEqual(result["observations"]["page:" + wrong]["state"], "broken")
        self.assertEqual(
            result["observations"]["anchor:" + BASE + "#missing"]["state"], "broken"
        )

    def test_destination_redirect_chain_cannot_be_hidden_by_historical_source(self):
        seed = {**SEED, "pages": ["", "a.html", "z.html"]}
        responses = fixtures()
        a, z = BASE + "a.html", BASE + "z.html"
        responses[a] = Response(a, 301, headers={"location": z})
        responses[z] = Response(z, 301, headers={"location": BASE})
        result = self.check(responses, seed=seed)
        self.assertEqual(result["observations"]["page:" + z]["state"], "healthy")
        self.assertEqual(result["observations"]["destination:" + z]["state"], "broken")

    def test_retired_404_recovers_when_permanent_redirect_is_added(self):
        responses = fixtures()
        old = BASE + "old.html"
        first = self.check(responses)
        previous, _ = monitor.reconcile(
            {}, first["observations"], "2026-10-27T08:00:00+00:00", ["Example"]
        )
        previous, _ = monitor.reconcile(
            previous, first["observations"], "2026-10-28T08:00:00+00:00", ["Example"]
        )
        responses[old] = Response(old, 301, headers={"location": BASE})
        second = self.check(responses)
        _, delta = monitor.reconcile(
            previous, second["observations"], "2026-10-29T08:00:00+00:00", ["Example"]
        )
        self.assertEqual([r["url"] for r in delta["recoveries"]], [old])

    def test_existing_noindex_archive_is_preserved(self):
        responses = fixtures()
        old = BASE + "old.html"
        responses[old] = Response(
            old,
            200,
            html(old).replace(
                b"</head>", b'<meta name="robots" content="noindex"></head>'
            ),
        )
        self.assertEqual(
            self.check(responses)["observations"]["page:" + old]["state"], "healthy"
        )

    def test_unverified_monitor_warning_once_after_three_runs(self):
        state = {}
        for day in range(27, 31):
            state, delta = monitor.reconcile(
                state,
                {"u": {"repository": "Example", "state": "unverified"}},
                f"2026-10-{day}T08:00:00+00:00",
                ["Example"],
            )
            self.assertEqual(
                delta["monitor_warnings"], ["Example"] if day == 29 else []
            )
        _, delta = monitor.reconcile(
            state,
            {"u": {"repository": "Example", "state": "healthy"}},
            "2026-10-31T08:00:00+00:00",
            ["Example"],
        )
        self.assertEqual(delta["monitor_recoveries"], ["Example"])

    def test_global_rate_limit_stops_further_requests(self):
        class Transport:
            def __init__(self, **kwargs):
                pass

            def fetch(self, url):
                return Response(url, 429)

        with patch.object(monitor, "CurlClient", Transport):
            client = monitor.Client()
            self.assertEqual(client.fetch(BASE).status, 429)
            self.assertIn(
                "global HTTP 429", client.fetch("https://other.example.org/").error
            )
            self.assertEqual(len(client.cache), 1)

    def test_lock_prevents_overlapping_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                monitor.exclusive_run(Path(directory)) as first,
                monitor.exclusive_run(Path(directory)) as second,
            ):
                self.assertTrue(first)
                self.assertFalse(second)
            self.assertFalse((Path(directory) / "monitor.lock").exists())

    def test_cli_network_findings_exit_zero_and_config_failure_is_distinct(self):
        for state in ("unverified", "findings"):
            with (
                tempfile.TemporaryDirectory() as directory,
                contextlib.redirect_stdout(io.StringIO()),
                patch.object(monitor, "load_configuration", return_value=([], {})),
                patch.object(monitor, "Client"),
                patch.object(
                    monitor,
                    "run",
                    return_value=(
                        {"schema_version": 1},
                        {"state": state, "packages": []},
                    ),
                ),
            ):
                self.assertEqual(monitor.main(["--state-dir", directory]), 0)
                self.assertTrue((Path(directory) / "latest.json").exists())
        with (
            tempfile.TemporaryDirectory() as directory,
            contextlib.redirect_stdout(io.StringIO()),
            patch.object(
                monitor, "load_configuration", side_effect=ValueError("invalid config")
            ),
        ):
            self.assertEqual(monitor.main(["--state-dir", directory]), 2)

    def test_registry_seed_coverage_and_correct_qis_channel(self):
        packages, seeds = monitor.load_configuration(
            monitor.HERE / "public_registry.json",
            monitor.HERE / "documentation_monitor_seed.json",
        )
        self.assertEqual(len(packages), 11)
        self.assertEqual(seeds["QuantInvestStrats"]["version"], "stable")
        self.assertEqual(sum(len(s["pages"]) for s in seeds.values()), 928)
        self.assertEqual(sum(len(s["legacy_paths"]) for s in seeds.values()), 98)


if __name__ == "__main__":
    unittest.main()
