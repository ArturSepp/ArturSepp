"""Fault-injection contracts for read-only retries and the workflow producer."""
import copy
import io
import json
import sys
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "templates"))
import harden_public_workflows as workflows
import release_guard as guard


def response(payload=None):
    if payload is None:
        payload = {"urls": [{"filename": "sample.whl"}]}
    return io.BytesIO(json.dumps(payload).encode())


def http_error(code, headers=None):
    return urllib.error.HTTPError("url", code, "fixture", headers or {}, None)


class MetadataRetryTests(unittest.TestCase):
    def setUp(self):
        self.sleep = mock.patch("time.sleep").start()
        self.addCleanup(mock.patch.stopall)

    def test_transient_metadata_errors_recover(self):
        for failure in (http_error(503), http_error(429), urllib.error.URLError("reset"),
                        TimeoutError("timeout"), ConnectionResetError("reset")):
            with self.subTest(failure=failure), mock.patch.object(
                    guard.urllib.request, "urlopen", side_effect=[failure, response()]) as read:
                self.assertEqual(guard.pypi_files("sample", "1.2.3")[0]["filename"], "sample.whl")
                self.assertEqual(read.call_count, 2)

    def test_retries_are_bounded_and_still_raise(self):
        with mock.patch.object(guard.urllib.request, "urlopen", side_effect=http_error(503)) as read:
            with self.assertRaises(urllib.error.HTTPError):
                guard.pypi_files("sample", "1.2.3")
            self.assertEqual(read.call_count, 4)
            self.assertEqual(self.sleep.call_args_list, [mock.call(2), mock.call(5), mock.call(10)])

    def test_auth_errors_fail_without_retry_and_only_404_means_absent(self):
        for code in (400, 401, 403):
            with self.subTest(code=code), mock.patch.object(
                    guard.urllib.request, "urlopen", side_effect=http_error(code)) as read:
                with self.assertRaises(urllib.error.HTTPError):
                    guard.pypi_files("sample", "1.2.3")
                self.assertEqual(read.call_count, 1)
        with mock.patch.object(guard.urllib.request, "urlopen", side_effect=http_error(404)):
            self.assertIsNone(guard.pypi_files("sample", "1.2.3"))
        self.sleep.assert_not_called()

    def test_retry_after_is_respected_within_budget(self):
        with mock.patch.object(guard.urllib.request, "urlopen", side_effect=[
                http_error(429, {"Retry-After": "12"}), response()]):
            self.assertTrue(guard.pypi_files("sample", "1.2.3"))
        self.sleep.assert_called_once_with(12)

    def test_unbounded_or_invalid_server_delay_fails_closed(self):
        for value in ("300", "-1", "invalid"):
            with self.subTest(value=value), mock.patch.object(
                    guard.urllib.request, "urlopen", side_effect=http_error(429, {"Retry-After": value})) as read:
                with self.assertRaises(urllib.error.HTTPError):
                    guard.pypi_files("sample", "1.2.3")
                self.assertEqual(read.call_count, 1)
        self.sleep.assert_not_called()

    def test_retry_after_date_is_respected(self):
        import datetime as dt
        import email.utils
        now = dt.datetime(2026, 11, 1, tzinfo=dt.UTC)
        after = email.utils.format_datetime(now + dt.timedelta(seconds=15), usegmt=True)
        with mock.patch.object(guard.dt, "datetime", wraps=dt.datetime) as clock:
            clock.now.return_value = now
            with mock.patch.object(guard.urllib.request, "urlopen", side_effect=[
                    http_error(503, {"Retry-After": after}), response()]):
                self.assertTrue(guard.pypi_files("sample", "1.2.3"))
        self.sleep.assert_called_once_with(15)

    def test_incomplete_json_recovers_but_schema_errors_fail_closed(self):
        with mock.patch.object(guard.urllib.request, "urlopen", side_effect=[io.BytesIO(b'{'), response()]):
            self.assertTrue(guard.pypi_files("sample", "1.2.3"))
        self.sleep.reset_mock()
        for payload in ({"urls": []}, {"other": []}, [], {"urls": "wrong"}):
            with self.subTest(payload=payload), mock.patch.object(
                    guard.urllib.request, "urlopen", return_value=response(payload)) as read:
                with self.assertRaises(ValueError):
                    guard.pypi_files("sample", "1.2.3")
                self.assertEqual(read.call_count, 1)
        self.sleep.assert_not_called()


class WorkflowRetryTests(unittest.TestCase):
    SOURCE = """name: Fixture
on: [push]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: astral-sh/setup-uv@immutable
      - run: uv pip install sample
      - run: python -m pip install build
      - name: Get wheel
        uses: actions/download-artifact@immutable
        with:
          pattern: ci-coverage-*
          merge-multiple: true
          path: ${{ runner.temp }}/coverage
      - run: pytest
      - uses: pypa/gh-action-pypi-publish@immutable
        with:
          skip-existing: false
"""

    def test_producer_is_idempotent_and_preserves_semantics(self):
        before = yaml.load(self.SOURCE, Loader=yaml.BaseLoader)
        proposed = workflows.harden_workflow(self.SOURCE)
        self.assertEqual(workflows.harden_workflow(proposed), proposed)
        after = yaml.load(proposed, Loader=yaml.BaseLoader)
        self.assertEqual(after["env"], {"UV_HTTP_RETRIES": "5", "UV_HTTP_TIMEOUT": "60",
                                        "PIP_RETRIES": "5", "PIP_TIMEOUT": "60"})
        for key in ("name", "on", "permissions"):
            self.assertEqual(before[key], after[key])
        old_steps = before["jobs"]["test"]["steps"]
        new_steps = after["jobs"]["test"]["steps"]
        self.assertEqual([s for s in old_steps if not s.get("uses", "").startswith(workflows.DOWNLOAD)],
                         [s for s in new_steps if workflows.MARKER not in str(s)
                          and not s.get("id", "").startswith(workflows.PREFIX)
                          and not s.get("name", "").startswith("Wait before")])
        downloads = [s for s in new_steps if s.get("uses", "").startswith(workflows.DOWNLOAD)]
        self.assertEqual(len(downloads), 3)
        self.assertEqual([s["with"] for s in downloads], [old_steps[3]["with"]] * 3)
        self.assertNotIn("continue-on-error", downloads[-1])
        workflows.validate_artifacts(after)

    def test_validator_rejects_advisory_final_attempt_or_changed_inputs(self):
        document = yaml.load(workflows.harden_workflow(self.SOURCE), Loader=yaml.BaseLoader)
        final = next(s for s in document["jobs"]["test"]["steps"] if s.get("id", "").endswith("_final"))
        original = copy.deepcopy(final)
        for key, value in (("continue-on-error", "true"), ("with", {"name": "other"}), ("if", "always()")):
            final.clear()
            final.update(original)
            final[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                workflows.validate_artifacts(document)

    def test_checker_detects_new_unprotected_workflows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ".github/workflows/ci.yml"
            path.parent.mkdir(parents=True)
            path.write_text(self.SOURCE, encoding="utf-8")
            self.assertTrue(workflows.workflow_retry_drift(root))
            path.write_text(workflows.harden_workflow(self.SOURCE), encoding="utf-8")
            self.assertEqual(workflows.workflow_retry_drift(root), [])
            source = path.read_text(encoding="utf-8").replace("continue-on-error: true", "continue-on-error: false", 1)
            path.write_text(source, encoding="utf-8")
            self.assertTrue(workflows.workflow_retry_drift(root))

    def test_keep_explicit_dependency_settings_and_reusable_workflows(self):
        source = self.SOURCE.replace("jobs:", 'env:\n  UV_HTTP_RETRIES: "8"\njobs:', 1)
        hardened = yaml.load(workflows.harden_workflow(source), Loader=yaml.BaseLoader)
        self.assertEqual(hardened["env"]["UV_HTTP_RETRIES"], "8")
        reusable = "name: Caller\non: [push]\njobs:\n  docs:\n    uses: owner/repo/.github/workflows/docs.yml@main\n"
        self.assertEqual(workflows.harden_workflow(reusable), reusable)


class CollectorStartupTests(unittest.TestCase):
    def test_download_collector_starts_with_only_the_standard_library(self):
        program = (
            "import runpy, sys\n"
            f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
            "sys.argv = ['refresh_downloads.py', '--help']\n"
            "try:\n"
            f"    runpy.run_path({str(SCRIPTS / 'refresh_downloads.py')!r}, run_name='__main__')\n"
            "except SystemExit as error:\n"
            "    if error.code not in (0, None): raise\n"
            "assert 'yaml' not in sys.modules\n"
            "assert 'harden_public_workflows' not in sys.modules\n"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-S", "-B", "-c", program],
            capture_output=True, text=True, check=False, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
