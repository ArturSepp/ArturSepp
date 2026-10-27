"""Independent HTTP, cache evidence and honest incomplete-result regressions."""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_sitemaps as sitemap

SITE = "https://docs.example.org"
BASE = SITE + "/en/latest/"


def xml(urls):
    return ('<?xml version="1.0"?><urlset xmlns="' + sitemap.NAMESPACE + '">' +
            ''.join('<url><loc>' + u + '</loc></url>' for u in urls) + '</urlset>').encode()


def response(url, urls, **options):
    return sitemap.Response(url, 200, xml(urls), **options)


class FixtureClient:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def fetch(self, url):
        self.calls.append(url)
        return self.responses[url]


def client_for(root_urls, version_urls=None, **headers):
    return FixtureClient({
        SITE + "/sitemap.xml": response(SITE + "/sitemap.xml", root_urls, headers=headers),
        BASE + "sitemap.xml": response(BASE + "sitemap.xml", version_urls or root_urls),
    })


class SitemapTests(unittest.TestCase):
    def test_independent_root_inventory_mismatch_is_not_hidden_by_equal_counts(self):
        client = client_for([BASE + "old.html"], [BASE + "new.html"])
        result = sitemap.verify_site(SITE, "latest", client)
        self.assertEqual(result["state"], "mismatch")
        self.assertEqual(result["only_in_root"], [BASE + "old.html"])
        self.assertEqual(client.calls, [SITE + "/sitemap.xml", BASE + "sitemap.xml"])
        self.assertNotIn("stale", result["problems"][0].lower())

    def test_cache_hit_age_etag_and_serialization_differences_are_not_failures(self):
        client = client_for([BASE, BASE + "api/index.html"],
                            **{"cache-control": "max-age=14400", "age": "9000",
                               "cf-cache-status": "HIT", "etag": '"root"',
                               "set-cookie": "must-not-be-in-the-report"})
        client.responses[BASE + "sitemap.xml"] = sitemap.Response(
            BASE + "sitemap.xml", 200,
            xml([BASE + "api/index.html", BASE]).replace(b"><", b">\n<"),
            {"etag": '"version"'},
        )
        result = sitemap.verify_site(SITE, "latest", client)
        self.assertEqual(result["state"], "verified")
        self.assertTrue(result["same_inventory"])
        self.assertFalse(result["same_bytes"])
        self.assertFalse(result["same_etag"])
        self.assertEqual(result["root"]["headers"]["age"], "9000")
        self.assertNotIn("must-not-be-in-the-report", json.dumps(result))

    def test_access_errors_and_html_challenges_are_unverified(self):
        for status in (301, 403, 429, 503):
            with self.subTest(status=status):
                client = FixtureClient({SITE + "/sitemap.xml": sitemap.Response(
                    SITE + "/sitemap.xml", status, b"Access unavailable",
                )})
                result = sitemap.verify_site(SITE, "latest", client)
                self.assertEqual(result["state"], "unverified")
                self.assertEqual(len(client.calls), 1)
        client = client_for([BASE])
        client.responses[SITE + "/sitemap.xml"] = sitemap.Response(
            SITE + "/sitemap.xml", 200, b"<html><body>Security verification</body></html>",
        )
        self.assertEqual(sitemap.verify_site(SITE, "latest", client)["state"], "unverified")
        client.responses[SITE + "/sitemap.xml"] = sitemap.Response(
            SITE + "/sitemap.xml", 0, error="connection timed out",
        )
        self.assertEqual(sitemap.verify_site(SITE, "latest", client)["state"], "unverified")

    def test_rate_limit_stops_all_remaining_requests_and_cannot_pass(self):
        client = FixtureClient({SITE + "/sitemap.xml": sitemap.Response(
            SITE + "/sitemap.xml", 429, headers={"retry-after": "120"},
        )})
        result = sitemap.verify_sites([SITE, "https://other.example.org"], "latest", client)
        self.assertEqual(result["state"], "unverified")
        self.assertEqual(result["not_checked_sites"], ["https://other.example.org"])
        self.assertEqual(client.calls, [SITE + "/sitemap.xml"])
        self.assertEqual(result["sites"][0]["root"]["headers"]["retry-after"], "120")

    def test_nested_index_is_checked_as_its_own_canonical(self):
        urls = [BASE, BASE + "api/index.html"]
        client = client_for(urls)
        for url in urls:
            client.responses[url] = sitemap.Response(
                url, 200, ('<html><head><link rel="canonical" href="' + url +
                           '"></head><body>Example</body></html>').encode(),
            )
        result = sitemap.verify_site(SITE, "latest", client, check_pages=True)
        self.assertEqual(result["state"], "verified")
        self.assertEqual(result["page_checks"], "complete")
        self.assertEqual(result["pages"][1]["canonicals"], [BASE + "api/index.html"])
        for metadata, headers in [('<meta name="robots" content="noindex">', {}),
                                  ('', {"x-robots-tag": "none"}),
                                  ('<meta http-equiv="refresh" content="0; url=/">', {})]:
            client.responses[BASE] = sitemap.Response(
                BASE, 200, ('<html><head><link rel="canonical" href="' + BASE +
                            '">' + metadata + '</head></html>').encode(), headers,
            )
            with self.subTest(metadata=metadata, headers=headers):
                self.assertEqual(sitemap.verify_site(
                    SITE, "latest", client, check_pages=True,
                )["state"], "mismatch")

    def test_page_limit_and_unavailable_page_never_claim_complete_verification(self):
        client = client_for([BASE, BASE + "api.html"])
        result = sitemap.verify_site(SITE, "latest", client, check_pages=True, max_pages=1)
        self.assertEqual(result["state"], "unverified")
        self.assertEqual(result["page_checks"], "incomplete")
        self.assertEqual(len(client.calls), 2)
        client.responses[BASE] = sitemap.Response(BASE, 429)
        result = sitemap.verify_site(SITE, "latest", client, check_pages=True)
        self.assertEqual(result["state"], "unverified")
        self.assertTrue(result["rate_limited"])
        self.assertEqual(result["page_checks"], "incomplete")

    def test_aliases_duplicates_and_different_expected_build_are_detected(self):
        for urls in ([BASE + "index.html"], [BASE, BASE], [SITE + "/en/stable/"]):
            with self.subTest(urls=urls):
                self.assertEqual(sitemap.verify_site(
                    SITE, "latest", client_for(urls),
                )["state"], "mismatch")
        result = sitemap.verify_site(SITE, "latest", client_for([BASE]),
                                     expected=[BASE, BASE + "new.html"])
        self.assertEqual(result["state"], "mismatch")

    def test_cli_preserves_json_outcome_and_exit_codes(self):
        for wanted, code in (("verified", 0), ("mismatch", 1), ("unverified", 2)):
            client = client_for([BASE], [BASE + "different.html"] if code == 1 else None)
            if code == 2:
                client.responses[SITE + "/sitemap.xml"] = sitemap.Response(SITE + "/sitemap.xml", 503)
            with self.subTest(wanted=wanted), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "result.json"
                with mock.patch.object(sitemap, "CurlClient", return_value=client):
                    result = sitemap.main(["--site", SITE, "--version", "latest", "--output", str(target)])
                self.assertEqual(result, code)
                self.assertEqual(json.loads(target.read_text())["state"], wanted)

    def test_selected_stable_channel_is_preserved(self):
        base = SITE + "/en/stable/"
        client = FixtureClient({
            SITE + "/sitemap.xml": response(SITE + "/sitemap.xml", [base]),
            base + "sitemap.xml": response(base + "sitemap.xml", [base]),
        })
        result = sitemap.verify_site(SITE, "stable", client)
        self.assertEqual(result["state"], "verified")
        self.assertEqual(client.calls, [SITE + "/sitemap.xml", base + "sitemap.xml"])

    def test_http_200_explicit_security_challenge_is_unverified(self):
        client = client_for([BASE])
        client.responses[BASE] = sitemap.Response(
            BASE, 200, b"<html><head><title>Check</title></head></html>",
            {"cf-mitigated": "challenge"},
        )
        result = sitemap.verify_site(SITE, "latest", client, check_pages=True)
        self.assertEqual(result["state"], "unverified")
        self.assertEqual(result["page_checks"], "incomplete")

    def test_evidence_write_failure_is_unverified_not_a_mismatch_exit(self):
        client = client_for([BASE])
        with tempfile.TemporaryDirectory() as directory:
            occupied = Path(directory) / "file"
            occupied.write_text("existing file")
            stderr = io.StringIO()
            with mock.patch.object(sitemap, "CurlClient", return_value=client), \
                    contextlib.redirect_stderr(stderr):
                code = sitemap.main(["--site", SITE, "--version", "latest",
                                     "--output", str(occupied / "result.json")])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stderr.getvalue())["state"], "unverified")
            self.assertEqual(occupied.read_text(), "existing file")

    @unittest.skipUnless(shutil.which("curl") or shutil.which("curl.exe"), "system curl unavailable")
    def test_real_http_gets_observe_changed_server_data_without_browser_cache(self):
        state = {"urls": [], "requests": []}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                state["requests"].append((self.path, dict(self.headers)))
                body = xml(state["urls"])
                self.send_response(200)
                self.send_header("Content-Type", "application/xml")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "max-age=14400")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        try:
            site = f"http://127.0.0.1:{server.server_port}"
            base = site + "/en/latest/"
            client = sitemap.CurlClient(interval=0)
            for urls in ([base], [base, base + "api.html"]):
                state["urls"] = urls
                result = sitemap.verify_site(site, "latest", client)
                self.assertEqual(result["state"], "verified")
                self.assertEqual(result["root_urls"], urls)
                self.assertEqual(result["root"]["headers"]["cache-control"], "max-age=14400")
            self.assertEqual([p for p, _ in state["requests"]],
                             ["/sitemap.xml", "/en/latest/sitemap.xml"] * 2)
            self.assertTrue(all("Cookie" not in h and "If-None-Match" not in h
                                for _, h in state["requests"]))
            with mock.patch.object(sitemap.subprocess, "run", side_effect=OSError("missing curl")):
                self.assertEqual(client.fetch(site + "/sitemap.xml").status, 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class RedirectTests(unittest.TestCase):
    def fixture(self, status=301, location=None, anchor=True):
        target = BASE + "new.html#replacement"
        rules = [{"from_url": "/old.html", "to_url": target,
                  "redirect_type": "page", "http_status": 301, "force": False, "enabled": True}]
        client = client_for([BASE])
        source = BASE + "old.html"
        client.responses[source] = sitemap.Response(
            source, status, headers={"location": target if location is None else location},
        )
        client.responses[BASE + "new.html"] = sitemap.Response(
            BASE + "new.html", 200,
            ('<html><head><link rel="canonical" href="' + BASE + 'new.html"></head>' +
             ('<body id="replacement">Moved page</body>' if anchor else '<body>No anchor</body>') +
             '</html>').encode(),
        )
        return client, rules

    def test_permanent_legacy_redirect_and_exact_destination_anchor(self):
        client, rules = self.fixture()
        result = sitemap.verify_site(SITE, "latest", client, redirects=rules)
        self.assertEqual(result["state"], "verified")
        self.assertEqual(result["redirects"]["rules"][0]["actual_location"], rules[0]["to_url"])
        for status, location, anchor in [(404, None, True), (302, None, True),
                                         (301, BASE, True), (301, None, False)]:
            with self.subTest(status=status, location=location, anchor=anchor):
                client, rules = self.fixture(status, location, anchor)
                result = sitemap.verify_site(SITE, "latest", client, redirects=rules)
                self.assertEqual(result["state"], "mismatch")
                self.assertTrue(result["redirects"]["rules"][0]["problems"])

    def test_non_forced_rules_preserve_existing_archived_pages(self):
        client, rules = self.fixture(status=200)
        source = BASE + "old.html"
        client.responses[source].body = (
            '<html><head><link rel="canonical" href="' + source + '"></head><body>Archive</body></html>'
        ).encode()
        result = sitemap.verify_site(SITE, "latest", client, redirects=rules)
        self.assertEqual(result["state"], "verified")
        self.assertTrue(result["redirects"]["rules"][0]["existing_page_preserved"])

    def test_rate_limited_legacy_source_stops_without_following_or_bypassing(self):
        client, rules = self.fixture(status=429)
        result = sitemap.verify_sites([SITE, "https://other.example.org"], "latest", client,
                                       redirects=rules)
        self.assertEqual(result["state"], "unverified")
        self.assertEqual(result["not_checked_sites"], ["https://other.example.org"])
        self.assertEqual(client.calls[-1], BASE + "old.html")
        self.assertNotIn(BASE + "new.html", client.calls)

    def test_cli_loads_reviewed_manifest_and_rejects_forced_or_wrong_site_rules(self):
        client, rules = self.fixture()
        manifest = {"schema_version": 1, "site": SITE, "redirects": rules}
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "redirects.json"
            file.write_text(json.dumps(manifest), encoding="utf-8")
            stdout = io.StringIO()
            with mock.patch.object(sitemap, "CurlClient", return_value=client), \
                    contextlib.redirect_stdout(stdout):
                code = sitemap.main(["--site", SITE, "--version", "latest",
                                     "--redirect-manifest", str(file)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["sites"][0]["redirects"]["state"], "verified")
            rules[0]["force"] = True
            file.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ValueError):
                sitemap.read_redirects(file, SITE)
            rules[0]["force"] = False
            manifest["site"] = "https://different.example.org"
            file.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ValueError):
                sitemap.read_redirects(file, SITE)


if __name__ == "__main__":
    unittest.main()
