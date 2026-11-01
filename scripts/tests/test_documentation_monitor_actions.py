"""Offline contracts for the hosted monitor's durable state and notification outbox."""

import base64
import copy
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from collections import Counter
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import documentation_monitor_actions as actions

STAMP = "2026-10-27T08:17:00+01:00"
RUN = "https://github.com/ArturSepp/ArturSepp/actions/runs/1"


def snapshot(active=False):
    return {
        "schema_version": 1,
        "state": {
            "schema_version": 1,
            "checked_at_utc": STAMP,
            "history": {"Example": {"pages": ["old.html"]}},
            "checks": {"page:u": {"active": active}},
            "availability": {},
        },
        "delivery": {},
        "outbox": [],
    }


def report(alerts=False, recovery=False):
    row = {
        "repository": "Example",
        "url": "https://docs.example.org/old.html",
        "detail": "HTTP 404",
    }
    return {
        "checked_at_utc": STAMP,
        "state": "findings" if alerts else "verified",
        "counts": {"healthy": 1, "broken": int(alerts), "unverified": 0},
        "alerts": [row] if alerts else [],
        "recoveries": [row] if recovery else [],
        "monitor_warnings": [],
        "monitor_recoveries": [],
    }


class FixtureAPI:
    def __init__(self, value=None):
        self.value = copy.deepcopy(value or snapshot())
        self.sha = "initial"
        self.issues = []
        self.comments = []
        self.calls = []
        self.put_count = 0
        self.fail_put = 0
        self.large = False

    def request(self, method, path, data=None, **kwargs):
        self.calls.append((method, path, data))
        if method == "GET" and path.startswith("contents/"):
            return {
                "sha": self.sha,
                "encoding": "none" if self.large else "base64",
                "content": base64.b64encode(json.dumps(self.value).encode()).decode(),
            }
        if method == "GET" and path.startswith("git/blobs/"):
            return {
                "content": base64.b64encode(json.dumps(self.value).encode()).decode()
            }
        if method == "PUT":
            self.put_count += 1
            if self.put_count == self.fail_put:
                raise RuntimeError("Temporary GitHub failure")
            if data["sha"] != self.sha:
                raise RuntimeError("HTTP 409 stale state")
            self.value = json.loads(base64.b64decode(data["content"]))
            self.sha = "saved-" + str(self.put_count)
            return {"content": {"sha": self.sha}}
        if method == "POST" and path == "issues":
            row = {
                **data,
                "number": 1,
                "state": "open",
                "user": {"login": "github-actions[bot]"},
            }
            self.issues.append(row)
            return copy.deepcopy(row)
        if method == "POST" and path.endswith("/comments"):
            self.comments.append(data)
            return {"id": len(self.comments)}
        if method == "GET" and path == "issues/1":
            return copy.deepcopy(self.issues[0])
        if method == "PATCH" and path == "issues/1":
            self.issues[0].update(data)
            return copy.deepcopy(self.issues[0])
        raise AssertionError((method, path, data))

    def items(self, path):
        return iter(
            copy.deepcopy(self.comments if path.endswith("/comments") else self.issues)
        )


class HostedMonitorTests(unittest.TestCase):
    def prepare(self, api, directory, *, alerts=False, recovery=False):
        actions.restore(api, directory)
        state = copy.deepcopy(api.value["state"])
        state["checks"]["page:u"]["active"] = alerts
        (directory / "state.json").write_text(json.dumps(state))
        (directory / "latest.json").write_text(json.dumps(report(alerts, recovery)))
        actions.prepare(directory, RUN)

    def test_healthy_run_only_persists_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory)
            actions.publish(api, directory, "ArturSepp")
            self.assertFalse(api.issues)
            self.assertEqual(api.put_count, 1)
            self.assertEqual(
                api.value["state"]["history"]["Example"]["pages"], ["old.html"]
            )

    def test_new_failure_is_committed_then_assigned_notification_then_acknowledged(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(api.issues[0]["assignees"], ["ArturSepp"])
            self.assertIn("@ArturSepp", api.issues[0]["body"])
            mutations = [call[:2] for call in api.calls if call[0] in {"PUT", "POST"}]
            self.assertEqual([m[0] for m in mutations], ["PUT", "PUT", "POST", "PUT"])
            self.assertEqual(api.value["outbox"], [])
            self.assertEqual(api.value["delivery"]["issue_number"], 1)

    def test_unchanged_failure_sends_no_comment(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            actions.publish(api, directory, "ArturSepp")
            actions.restore(api, directory)
            (directory / "latest.json").write_text(json.dumps(report()))
            actions.prepare(directory, RUN)
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.issues), 1)
            self.assertFalse(api.comments)

    def test_ack_failure_replays_outbox_without_duplicate_notification(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            api.fail_put = 3
            with self.assertRaises(RuntimeError):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.value["outbox"]), 1)
            self.assertEqual(len(api.issues), 1)
            actions.restore(api, directory)
            (directory / "latest.json").write_text(json.dumps(report()))
            actions.prepare(directory, RUN)
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.issues), 1)
            self.assertFalse(api.comments)
            self.assertEqual(api.value["outbox"], [])

    def test_missing_issue_listing_after_creation_cannot_create_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            api.fail_put = 3
            with self.assertRaises(RuntimeError):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.issues), 1)
            self.assertTrue(api.value["delivery"]["issue_creation_pending"])
            actions.restore(api, directory)
            (directory / "latest.json").write_text(json.dumps(report()))
            actions.prepare(directory, RUN)
            with (
                patch.object(api, "items", return_value=iter([])),
                self.assertRaisesRegex(RuntimeError, "refusing a replacement"),
            ):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.issues), 1)
            self.assertEqual(len(api.value["outbox"]), 1)
            actions.restore(api, directory)
            actions.prepare(directory, RUN)
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.issues), 1)
            self.assertFalse(api.comments)
            self.assertFalse(api.value["outbox"])
            self.assertNotIn("issue_creation_pending", api.value["delivery"])

    def test_recovery_ack_failure_does_not_duplicate_comment_or_reopen(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            actions.publish(api, directory, "ArturSepp")
            self.prepare(api, directory, recovery=True)
            api.fail_put = api.put_count + 2
            with self.assertRaises(RuntimeError):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.comments), 1)
            self.assertEqual(api.issues[0]["state"], "closed")
            actions.restore(api, directory)
            (directory / "latest.json").write_text(json.dumps(report()))
            actions.prepare(directory, RUN)
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(api.comments), 1)
            self.assertEqual(api.issues[0]["state"], "closed")
            self.assertFalse(api.value["outbox"])

    def test_recovery_comments_and_closes_issue(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            actions.publish(api, directory, "ArturSepp")
            self.prepare(api, directory, recovery=True)
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(api.issues[0]["state"], "closed")
            self.assertEqual(len(api.comments), 1)
            self.assertIn("Verified recoveries", api.comments[0]["body"])

    def test_stale_artifact_cannot_overwrite_newer_state_or_send_notification(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            api.sha = "newer-run"
            with self.assertRaisesRegex(RuntimeError, "409"):
                actions.publish(api, directory, "ArturSepp")
            self.assertFalse(api.issues)
            self.assertEqual(api.sha, "newer-run")

    def test_state_persistence_failure_never_sends_notification(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory, api = Path(temporary), FixtureAPI()
            self.prepare(api, directory, alerts=True)
            api.fail_put = 1
            with self.assertRaises(RuntimeError):
                actions.publish(api, directory, "ArturSepp")
            self.assertFalse(api.issues)

    def test_large_snapshot_uses_exact_blob_sha(self):
        with tempfile.TemporaryDirectory() as temporary:
            api = FixtureAPI()
            api.large = True
            actions.restore(api, Path(temporary))
            self.assertIn(("GET", "git/blobs/initial", None), api.calls)

    def test_invalid_snapshot_is_not_reset(self):
        with tempfile.TemporaryDirectory() as temporary:
            api = FixtureAPI({"schema_version": 0})
            with self.assertRaises(ValueError):
                actions.restore(api, Path(temporary))
            self.assertFalse((Path(temporary) / "state.json").exists())

    def test_missing_remote_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            api = FixtureAPI()
            with (
                patch.object(api, "request", side_effect=RuntimeError("HTTP 404")),
                self.assertRaises(RuntimeError),
            ):
                actions.restore(api, Path(temporary))
            self.assertFalse((Path(temporary) / "state.json").exists())

    def test_authenticated_redirects_are_not_followed(self):
        self.assertIsNone(
            actions.NoRedirect().redirect_request(
                None, None, 302, "Found", {}, "https://other.example.org/"
            )
        )

    def test_api_refuses_cross_host_endpoints_without_network(self):
        api = actions.GitHub("ArturSepp/ArturSepp", "fake-test-token")
        with self.assertRaises(ValueError):
            api.request("GET", "https://other.example.org/")

    def test_workflow_scheduled_manual_only_and_write_permissions_separate(self):
        root = Path(__file__).resolve().parents[2]
        workflow = yaml.load(
            (root / ".github/workflows/documentation-monitor.yml").read_text(),
            Loader=yaml.BaseLoader,
        )
        self.assertEqual(set(workflow["on"]), {"schedule", "workflow_dispatch"})
        self.assertEqual(
            workflow["on"]["schedule"][0],
            {"cron": "17 8 * * *", "timezone": "Europe/Zurich"},
        )
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        writer = workflow["jobs"]["record-and-notify"]
        self.assertEqual(
            writer["permissions"], {"contents": "write", "issues": "write"}
        )
        self.assertEqual(writer["needs"], "check")
        self.assertEqual(workflow["concurrency"]["cancel-in-progress"], "false")
        required = (root / ".github/workflows/required.yml").read_text()
        self.assertNotIn("monitor_documentation.py", required)
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                if "uses" in step:
                    self.assertRegex(step["uses"], r"@[0-9a-f]{40}$")


class FaultOpener:
    """Exercise the real HTTP client against a durable fake GitHub backend."""

    def __init__(self, backend, faults):
        self.backend = backend
        self.faults = faults
        self.counts = Counter()
        self.calls = []

    def open(self, request, timeout):
        method = request.get_method()
        path = request.full_url.split("/repos/ArturSepp/ArturSepp/", 1)[1]
        data = json.loads(request.data) if request.data else None
        self.counts[method] += 1
        self.calls.append((method, path))
        fault = self.faults.get((method, self.counts[method]))

        def fail():
            error = fault[1]
            if isinstance(error, int):
                error = urllib.error.HTTPError(
                    request.full_url, error, "Injected GitHub failure", {}, None
                )
            raise error

        if fault and fault[0] == "before":
            fail()
        endpoint = path.split("?")[0]
        if method == "GET" and (endpoint == "issues" or endpoint.endswith("/comments")):
            response = list(self.backend.items(endpoint))
        else:
            try:
                response = self.backend.request(method, path, data)
            except RuntimeError as error:
                if "HTTP 409" not in str(error):
                    raise
                raise urllib.error.HTTPError(
                    request.full_url, 409, "Conflict", {}, None
                ) from None
        if fault and fault[0] == "after":
            if isinstance(fault[1], bytes):
                return io.BytesIO(fault[1])
            fail()
        return io.BytesIO(json.dumps(response).encode())


class ResilientMonitorTests(unittest.TestCase):
    @contextmanager
    def fixture(self, faults=None, *, alerts=False, large=False):
        with tempfile.TemporaryDirectory() as temporary:
            directory, backend = Path(temporary), FixtureAPI()
            HostedMonitorTests.prepare(self, backend, directory, alerts=alerts)
            backend.large = large
            opener = FaultOpener(backend, faults or {})
            api = actions.GitHub("ArturSepp/ArturSepp", "fake-test-token")
            output = io.StringIO()
            with (
                patch.object(actions.urllib.request, "build_opener", return_value=opener),
                patch("time.sleep") as sleep,
                redirect_stdout(output),
            ):
                yield api, backend, directory, opener, sleep, output

    def test_state_write_500_before_commit_recovers_and_alert_is_sent_once(self):
        with self.fixture({("PUT", 1): ("before", 500)}, alerts=True) as fixture:
            api, backend, directory, opener, sleep, _ = fixture
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(len(backend.issues), 1)
            self.assertEqual(backend.value["outbox"], [])
            self.assertEqual(opener.counts["POST"], 1)
            self.assertEqual(opener.counts["PUT"], 4)
            sleep.assert_called()

    def test_lost_write_acknowledgement_is_reconciled_without_repeating_put(self):
        for error in (500, TimeoutError("lost reply"), b"not JSON", b"{}"):
            with self.subTest(error=error), self.fixture(
                {("PUT", 1): ("after", error)}
            ) as fixture:
                api, backend, directory, opener, _, _ = fixture
                actions.publish(api, directory, "ArturSepp")
                self.assertEqual(opener.counts["PUT"], 1)
                published = json.loads((directory / "published.json").read_text())
                self.assertEqual(published["sha"], backend.sha)

    def test_acknowledgement_save_recovers_without_duplicate_notification(self):
        for position in ("before", "after"):
            with self.subTest(position=position), self.fixture(
                {("PUT", 3): (position, 503)}, alerts=True
            ) as fixture:
                api, backend, directory, opener, _, _ = fixture
                actions.publish(api, directory, "ArturSepp")
                self.assertEqual(opener.counts["POST"], 1)
                self.assertEqual(len(backend.issues), 1)
                self.assertEqual(backend.value["outbox"], [])

    def test_transient_reads_are_retried_without_resetting_history(self):
        faults = {
            ("GET", 1): ("before", 502),
            ("GET", 2): ("before", urllib.error.URLError("temporary outage")),
        }
        with self.fixture(faults) as fixture:
            api, backend, directory, opener, sleep, _ = fixture
            restored = actions.restore(api, directory)
            self.assertEqual(restored, backend.value)
            self.assertEqual(opener.counts["GET"], 3)
            self.assertEqual(sleep.call_count, 2)

    def test_permanent_http_errors_are_not_retried(self):
        for status in (401, 403, 404, 422):
            with self.subTest(status=status), self.fixture(
                {("GET", 1): ("before", status)}
            ) as fixture:
                api, _, directory, opener, sleep, _ = fixture
                with self.assertRaisesRegex(RuntimeError, str(status)):
                    actions.restore(api, directory)
                self.assertEqual(opener.counts["GET"], 1)
                sleep.assert_not_called()

    def test_read_outage_has_a_bounded_retry_budget(self):
        faults = {("GET", attempt): ("before", 503) for attempt in range(1, 5)}
        with self.fixture(faults) as fixture:
            api, _, directory, opener, sleep, _ = fixture
            with self.assertRaisesRegex(RuntimeError, "503"):
                actions.restore(api, directory)
            self.assertEqual(opener.counts["GET"], 4)
            self.assertEqual(sleep.call_count, 3)

    def test_write_outage_fails_without_notifying_or_discarding_prepared_state(self):
        faults = {("PUT", attempt): ("before", 500) for attempt in range(1, 5)}
        with self.fixture(faults, alerts=True) as fixture:
            api, backend, directory, opener, _, _ = fixture
            with self.assertRaisesRegex(RuntimeError, "500"):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(opener.counts["PUT"], 4)
            self.assertEqual(opener.counts["POST"], 0)
            self.assertEqual(backend.sha, "initial")
            prepared = json.loads((directory / "prepared.json").read_text())
            self.assertEqual(len(prepared["snapshot"]["outbox"]), 1)

    def test_newer_remote_state_is_never_overwritten_during_recovery(self):
        with self.fixture({("PUT", 1): ("before", 500)}, alerts=True) as fixture:
            api, backend, directory, opener, _, _ = fixture
            backend.sha = "newer-run"
            backend.value["state"]["checked_at_utc"] = "2026-11-01T09:00:00Z"
            newer = copy.deepcopy(backend.value)
            with self.assertRaisesRegex(RuntimeError, "stale|newer"):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(backend.value, newer)
            self.assertEqual(opener.counts["PUT"], 1)
            self.assertEqual(opener.counts["POST"], 0)

    def test_already_saved_healthy_artifact_is_safe_to_rerun(self):
        with self.fixture() as fixture:
            api, backend, directory, opener, _, _ = fixture
            actions.publish(api, directory, "ArturSepp")
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(backend.put_count, 2)
            self.assertEqual(opener.counts["POST"], 0)
            self.assertTrue((directory / "published.json").exists())

    def test_uncertain_reconciliation_never_repeats_the_write(self):
        faults = {("PUT", 1): ("before", 500)}
        faults.update({("GET", attempt): ("before", 503) for attempt in range(1, 5)})
        with self.fixture(faults, alerts=True) as fixture:
            api, _, directory, opener, _, _ = fixture
            with self.assertRaises(RuntimeError):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(opener.counts["PUT"], 1)
            self.assertEqual(opener.counts["POST"], 0)

    def test_large_snapshot_is_reconciled_using_its_exact_blob(self):
        with self.fixture({("PUT", 1): ("after", 500)}, large=True) as fixture:
            api, backend, directory, opener, _, _ = fixture
            actions.publish(api, directory, "ArturSepp")
            self.assertIn(("GET", "git/blobs/" + backend.sha), opener.calls)
            self.assertEqual(opener.counts["PUT"], 1)

    def test_lost_issue_creation_reply_is_not_blindly_retried(self):
        with self.fixture({("POST", 1): ("after", 500)}, alerts=True) as fixture:
            api, backend, directory, opener, _, _ = fixture
            with self.assertRaisesRegex(RuntimeError, "500"):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(opener.counts["POST"], 1)
            self.assertEqual(len(backend.issues), 1)
            self.assertTrue(backend.value["delivery"]["issue_creation_pending"])
            self.assertEqual(len(backend.value["outbox"]), 1)
            actions.restore(api, directory)
            actions.prepare(directory, RUN)
            actions.publish(api, directory, "ArturSepp")
            self.assertEqual(opener.counts["POST"], 1)
            self.assertEqual(backend.value["outbox"], [])

    def test_long_retry_after_is_not_ignored(self):
        error = urllib.error.HTTPError(
            "https://api.github.com/", 503, "Unavailable", {"Retry-After": "120"}, None
        )
        with self.fixture({("PUT", 1): ("before", error)}) as fixture:
            api, _, directory, opener, sleep, _ = fixture
            with self.assertRaisesRegex(RuntimeError, "503"):
                actions.publish(api, directory, "ArturSepp")
            self.assertEqual(opener.counts["PUT"], 1)
            self.assertEqual(opener.counts["GET"], 0)
            sleep.assert_not_called()

    def test_artifact_transfer_retries_are_bounded_and_exhaustion_remains_fatal(self):
        root = Path(__file__).resolve().parents[2]
        workflow = yaml.load(
            (root / ".github/workflows/documentation-monitor.yml").read_text(),
            Loader=yaml.BaseLoader,
        )
        steps = workflow["jobs"]["record-and-notify"]["steps"]
        downloads = [s for s in steps if s.get("uses", "").startswith("actions/download-artifact@")]
        self.assertEqual(len(downloads), 3)
        self.assertEqual([s.get("continue-on-error") for s in downloads], ["true", "true", None])
        self.assertNotIn("if", downloads[0])
        self.assertEqual(downloads[1]["if"], "steps.download.outcome == 'failure'")
        self.assertEqual(downloads[2]["if"], "steps.download_retry.outcome == 'failure'")
        for step in downloads:
            self.assertEqual(step["with"]["name"], "documentation-monitor")
            self.assertEqual(step["with"]["path"], "${{ runner.temp }}/documentation-monitor")
        publisher = next(s for s in steps if " publish " in s.get("run", ""))
        self.assertNotIn("continue-on-error", publisher)


if __name__ == "__main__":
    unittest.main()
