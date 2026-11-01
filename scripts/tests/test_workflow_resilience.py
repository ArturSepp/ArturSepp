"""Fault-injection contracts for report publication and read-only workflow retries."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import clone_public
import conformance
import refresh_downloads
import workflow_support as support

OLD = "2026-10-30T08:00:00+00:00"
NEW = "2026-11-01T08:00:00+00:00"


def run_git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=30,
    ).stdout.strip()


def make_snapshot(root, kind, stamp):
    root.mkdir(parents=True, exist_ok=True)
    if kind == "conformance":
        value = {"observed_at": stamp, "mode": "online", "packages": [
            {"dist": slug, "checks": []} for slug in sorted(support.DISTRIBUTIONS)
        ]}
        files = {"CONFORMANCE.json": json.dumps(value) + "\n", "CONFORMANCE.md": stamp + "\n"}
    else:
        value = {"observed_at": stamp, "packages": {slug: {"total": 100, "month": 10}
                 for slug in sorted(support.DISTRIBUTIONS)}}
        files = {"counts.json": json.dumps(value) + "\n", "updated.svg": stamp + "\n"}
        files.update({f"{slug}-total-blue.svg": stamp + "\n" for slug in support.DISTRIBUTIONS})
    for name, content in files.items():
        (root / name).write_text(content, encoding="utf-8", newline="\n")


@contextmanager
def publication_fixture(kind="downloads"):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        remote, seed, work = root / "remote.git", root / "seed", root / "work"
        remote.mkdir()
        run_git(remote, "init", "--bare")
        seed.mkdir()
        run_git(seed, "init", "--initial-branch=main")
        run_git(seed, "config", "core.autocrlf", "false")
        run_git(seed, "config", "user.name", "fixture")
        run_git(seed, "config", "user.email", "fixture@example.invalid")
        make_snapshot(seed, "conformance", OLD)
        make_snapshot(seed / "profile-downloads", "downloads", OLD)
        (seed / "README.md").write_text("preserve unrelated files\n", encoding="utf-8")
        run_git(seed, "add", ".")
        run_git(seed, "commit", "-m", "initial reports")
        run_git(seed, "remote", "add", "origin", str(remote))
        run_git(seed, "push", "origin", "HEAD:refs/heads/automation/reports")
        run_git(root, "-c", "core.autocrlf=false", "clone", "--branch", support.BRANCH, str(remote), str(work))
        run_git(work, "config", "core.autocrlf", "false")
        artifact = root / "artifact"
        make_snapshot(artifact, kind, NEW)
        with patch.object(support.time, "sleep"), redirect_stdout(io.StringIO()):
            yield root, remote, work, artifact


class PublicationTests(unittest.TestCase):
    def test_each_publisher_preserves_the_other_reports_and_unrelated_files(self):
        for kind in ("conformance", "downloads"):
            with self.subTest(kind=kind), publication_fixture(kind) as fixture:
                _, remote, work, artifact = fixture
                unrelated = ("profile-downloads/counts.json" if kind == "conformance"
                             else "CONFORMANCE.json")
                before = run_git(remote, "show", f"{support.BRANCH}:{unrelated}")
                (artifact / "README.md").write_text("must never be published")
                self.assertEqual(support.publish(kind, artifact, work), "published")
                self.assertEqual(run_git(remote, "show", f"{support.BRANCH}:{unrelated}"), before)
                self.assertEqual(run_git(remote, "show", f"{support.BRANCH}:README.md"),
                                 "preserve unrelated files")
                metadata = "CONFORMANCE.json" if kind == "conformance" else "profile-downloads/counts.json"
                published = json.loads(run_git(remote, "show", f"{support.BRANCH}:{metadata}"))
                self.assertEqual(published["observed_at"], NEW)

    def test_lost_push_reply_is_reconciled_without_a_duplicate_commit(self):
        with publication_fixture() as (_, remote, work, artifact):
            original, pushes = support.git, []
            def lost_reply(root, *args, **kwargs):
                result = original(root, *args, **kwargs)
                if args[0] == "push":
                    pushes.append(args)
                    return subprocess.CompletedProcess(args, 128, "", "HTTP 500 lost reply")
                return result
            with patch.object(support, "git", side_effect=lost_reply):
                self.assertEqual(support.publish("downloads", artifact, work), "already_published")
            self.assertEqual(len(pushes), 1)
            self.assertEqual(run_git(remote, "rev-list", "--count", support.BRANCH), "2")

    def test_failed_push_retries_the_same_immutable_commit(self):
        with publication_fixture() as (_, remote, work, artifact):
            original, pushes = support.git, []
            def outage(root, *args, **kwargs):
                if args[0] == "push":
                    pushes.append(args)
                    if len(pushes) < 3:
                        return subprocess.CompletedProcess(args, 128, "", "HTTP 503")
                return original(root, *args, **kwargs)
            with patch.object(support, "git", side_effect=outage):
                self.assertEqual(support.publish("downloads", artifact, work), "published")
            self.assertEqual(len(pushes), 3)
            self.assertEqual(len(set(pushes)), 1)
            self.assertEqual(run_git(remote, "rev-list", "--count", support.BRANCH), "2")

    def test_push_outage_exhausts_budget_without_changing_remote(self):
        with publication_fixture() as (_, remote, work, artifact):
            original, pushes = support.git, []
            before = run_git(remote, "rev-parse", support.BRANCH)
            def outage(root, *args, **kwargs):
                if args[0] == "push":
                    pushes.append(args)
                    return subprocess.CompletedProcess(args, 128, "", "HTTP 502")
                return original(root, *args, **kwargs)
            with patch.object(support, "git", side_effect=outage), self.assertRaises(RuntimeError):
                support.publish("downloads", artifact, work)
            self.assertEqual(len(pushes), 4)
            self.assertEqual(run_git(remote, "rev-parse", support.BRANCH), before)

    def test_fetch_failure_does_not_recreate_or_push_the_branch(self):
        with publication_fixture() as (_, remote, work, artifact):
            original, calls = support.git, []
            before = run_git(remote, "rev-parse", support.BRANCH)
            def outage(root, *args, **kwargs):
                calls.append(args[0])
                if args[0] == "fetch":
                    return subprocess.CompletedProcess(args, 128, "", "HTTP 500")
                return original(root, *args, **kwargs)
            with patch.object(support, "git", side_effect=outage), self.assertRaisesRegex(
                RuntimeError, "refusing to recreate"
            ):
                support.publish("downloads", artifact, work)
            self.assertEqual(calls.count("fetch"), 4)
            self.assertNotIn("push", calls)
            self.assertNotIn("switch", calls)
            self.assertEqual(run_git(remote, "rev-parse", support.BRANCH), before)

    def test_concurrent_remote_advance_is_preserved(self):
        with publication_fixture() as (_, remote, work, artifact):
            original, pushes = support.git, []
            def concurrent_writer(root, *args, **kwargs):
                if args[0] == "push":
                    pushes.append(args)
                    other = work.parent / "other"
                    run_git(work.parent, "clone", "--branch", support.BRANCH, str(remote), str(other))
                    run_git(other, "config", "user.name", "other")
                    run_git(other, "config", "user.email", "other@example.invalid")
                    (other / "README.md").write_text("concurrent change\n")
                    run_git(other, "add", "README.md")
                    run_git(other, "commit", "-m", "other update")
                    run_git(other, "push", "origin", f"HEAD:refs/heads/{support.BRANCH}")
                    return subprocess.CompletedProcess(args, 128, "", "HTTP 500")
                return original(root, *args, **kwargs)
            with patch.object(support, "git", side_effect=concurrent_writer), self.assertRaisesRegex(
                RuntimeError, "concurrent work"
            ):
                support.publish("downloads", artifact, work)
            self.assertEqual(len(pushes), 1)
            self.assertEqual(run_git(remote, "show", f"{support.BRANCH}:README.md"), "concurrent change")
            value = json.loads(run_git(remote, "show", f"{support.BRANCH}:profile-downloads/counts.json"))
            self.assertEqual(value["observed_at"], OLD)

    def test_stale_conflicting_and_incomplete_artifacts_never_publish(self):
        with publication_fixture() as (_, remote, work, artifact):
            before = run_git(remote, "rev-parse", support.BRANCH)
            make_snapshot(artifact, "downloads", "2026-10-29T08:00:00+00:00")
            with self.assertRaisesRegex(RuntimeError, "stale artifact"):
                support.publish("downloads", artifact, work)
            make_snapshot(artifact, "downloads", OLD)
            (artifact / "updated.svg").write_text("conflict")
            with self.assertRaisesRegex(RuntimeError, "Conflicting report"):
                support.publish("downloads", artifact, work)
            (artifact / "updated.svg").unlink()
            with patch.object(support, "git") as git, self.assertRaises(FileNotFoundError):
                support.publish("downloads", artifact, work)
            git.assert_not_called()
            self.assertEqual(run_git(remote, "rev-parse", support.BRANCH), before)

    def test_successful_snapshot_can_be_replayed_without_another_commit(self):
        with publication_fixture() as (_, remote, work, artifact):
            support.publish("downloads", artifact, work)
            before = run_git(remote, "rev-parse", support.BRANCH)
            self.assertEqual(support.publish("downloads", artifact, work), "already_published")
            self.assertEqual(run_git(remote, "rev-parse", support.BRANCH), before)


    def test_cli_survives_switching_to_a_report_branch_without_its_source_file(self):
        with publication_fixture() as (_, remote, work, artifact):
            scripts = work / "scripts"
            scripts.mkdir()
            entry = scripts / "workflow_support.py"
            entry.write_bytes(Path(support.__file__).read_bytes())
            registry = Path(support.__file__).with_name("public_registry.json")
            (scripts / registry.name).write_bytes(registry.read_bytes())
            run_git(work, "add", "scripts")
            run_git(work, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-m", "source checkout includes the new helper")
            environment = dict(os.environ, GITHUB_ACTIONS="true")
            result = subprocess.run(
                [sys.executable, str(entry), "downloads", "--source", str(artifact)],
                cwd=work, env=environment, capture_output=True, text=True, check=False, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "published")
            self.assertFalse(entry.exists())
            value = json.loads(run_git(remote, "show", f"{support.BRANCH}:profile-downloads/counts.json"))
            self.assertEqual(value["observed_at"], NEW)


class ReadAndWorkflowTests(unittest.TestCase):
    def test_pepy_permission_and_missing_pages_fail_without_retry(self):
        for status in (401, 403, 404):
            error = urllib.error.HTTPError("https://pepy.tech/", status, "denied", {}, None)
            with self.subTest(status=status), patch.object(
                refresh_downloads, "urlopen", side_effect=error
            ) as request, patch("time.sleep") as sleep:
                with self.assertRaises(urllib.error.HTTPError):
                    refresh_downloads.fetch_counts("qis")
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()

    def test_pepy_transient_failure_recovers_but_invalid_data_does_not_retry(self):
        summary = b"qis has been downloaded 100 times in total on PyPI, including 10 in the last 30 days"
        error = urllib.error.HTTPError("https://pepy.tech/", 503, "unavailable", {}, None)
        with patch.object(refresh_downloads, "urlopen", side_effect=[error, io.BytesIO(summary)]) as read, \
             patch("time.sleep"):
            self.assertEqual(refresh_downloads.fetch_counts("qis")["total"], 100)
            self.assertEqual(read.call_count, 2)
        with patch.object(refresh_downloads, "urlopen", return_value=io.BytesIO(b"source changed")) as read:
            with self.assertRaises(ValueError):
                refresh_downloads.fetch_counts("qis")
            self.assertEqual(read.call_count, 1)

    def test_conformance_read_does_not_retry_permission_errors_or_ignore_retry_after(self):
        for status, headers, expected in ((403, {}, urllib.error.HTTPError),
                                           (503, {"Retry-After": "120"}, urllib.error.HTTPError)):
            error = urllib.error.HTTPError("https://api.github.com/", status, "error", headers, None)
            with self.subTest(status=status), patch.object(
                conformance.urllib.request, "urlopen", side_effect=error
            ) as request, patch("time.sleep") as sleep:
                with self.assertRaises(expected):
                    conformance.fetch_json("https://api.github.com/example")
                self.assertEqual(request.call_count, 1)
                sleep.assert_not_called()

    def test_source_clone_uses_fresh_attempts_and_preserves_existing_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "Example"
            results = [subprocess.TimeoutExpired(["git", "clone"], 180),
                       subprocess.CompletedProcess([], 128, "", "HTTP 503"),
                       subprocess.CompletedProcess([], 0, "", "")]
            with patch.object(clone_public.subprocess, "run", side_effect=results) as clone, \
                 patch("time.sleep"):
                self.assertTrue(clone_public.clone_one("https://github.com/example/repo.git", target))
                self.assertEqual(clone.call_count, 3)
                paths = [call.args[0][-1] for call in clone.call_args_list]
                self.assertEqual(len(set(paths)), 3)
                self.assertNotIn(str(target), paths)
                self.assertTrue(target.is_dir())
            with patch.object(clone_public.subprocess, "run") as clone:
                with self.assertRaisesRegex(ValueError, "existing checkout"):
                    clone_public.clone_one("https://github.com/example/repo.git", target)
                clone.assert_not_called()

    def test_other_workflows_have_fatal_last_download_attempt_and_safe_publishers(self):
        root = Path(__file__).resolve().parents[2]
        for filename, kind in (("conformance.yml", "conformance"), ("profile-downloads.yml", "downloads")):
            workflow = yaml.load((root / ".github/workflows" / filename).read_text(), Loader=yaml.BaseLoader)
            writer = workflow["jobs"]["record"]
            steps = writer["steps"]
            downloads = [s for s in steps if s.get("uses", "").startswith("actions/download-artifact@")]
            with self.subTest(workflow=filename):
                self.assertEqual(len(downloads), 3)
                self.assertEqual([s.get("continue-on-error") for s in downloads], ["true", "true", None])
                self.assertEqual(downloads[1]["if"], "steps.download.outcome == 'failure'")
                self.assertEqual(downloads[2]["if"], "steps.download_retry.outcome == 'failure'")
                self.assertTrue(all("runner.temp" in s["with"]["path"] for s in downloads))
                publisher = next(s for s in steps if "workflow_support.py" in s.get("run", ""))
                self.assertIn(f"workflow_support.py {kind}", publisher["run"])
                self.assertNotIn("continue-on-error", publisher)
                self.assertNotIn("git push", publisher["run"])
                self.assertNotIn("|| true", str(steps))
                self.assertTrue(any(s.get("with", {}).get("python-version") == "3.12" for s in steps))
                self.assertEqual(writer["concurrency"], "public-generated-reports")

    def test_dependency_installs_have_explicit_transport_retry_budgets(self):
        root = Path(__file__).resolve().parents[2]
        for filename in ("conformance.yml", "required.yml"):
            workflow = yaml.load((root / ".github/workflows" / filename).read_text(), Loader=yaml.BaseLoader)
            commands = [s["run"] for j in workflow["jobs"].values() for s in j["steps"]
                        if "pip install" in s.get("run", "")]
            self.assertTrue(commands)
            for command in commands:
                self.assertIn("--retries 5", command)
                self.assertIn("--timeout 60", command)


if __name__ == "__main__":
    unittest.main()
