"""Offline contracts for the hosted monitor's durable state and notification outbox."""

import base64
import copy
import json
import sys
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
