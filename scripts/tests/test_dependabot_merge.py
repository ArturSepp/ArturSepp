"""Offline security, CI-gating and notification contracts for Dependabot merges."""

import base64
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dependabot_merge as merge
import generate_dependabot_automation as generator
from documentation_monitor_actions import GitHubError

REPO = "ArturSepp/BloombergFetch"
HEAD = "a" * 40
BASE = "b" * 40
PIN = "c" * 40
RUN = "https://github.com/" + REPO + "/actions/runs/1"


def pr():
    return {
        "number": 17,
        "state": "open",
        "draft": False,
        "html_url": "https://github.com/" + REPO + "/pull/17",
        "user": {"login": "dependabot[bot]", "type": "Bot"},
        "base": {"ref": "main", "sha": BASE, "repo": {"full_name": REPO}},
        "head": {
            "ref": "dependabot/github_actions/group",
            "sha": HEAD,
            "repo": {"full_name": REPO},
        },
    }


def action_file(path=".github/workflows/ci.yml"):
    return {
        "filename": path,
        "status": "modified",
        "patch": "@@ -1 +1 @@\n-  - uses: astral-sh/setup-uv@" + BASE + " # v1.0.0\n"
        "+  - uses: astral-sh/setup-uv@" + PIN + " # v1.0.1\n",
    }


class FixtureAPI:
    def __init__(self):
        self.pr = pr()
        self.runs = [
            {
                "id": 9,
                "workflow_id": 1,
                "head_sha": HEAD,
                "event": "pull_request",
                "status": "completed",
                "conclusion": "success",
                "html_url": RUN,
            }
        ]
        self.jobs = [{"name": "Required checks", "conclusion": "success"}]
        self.checks = [
            {"name": "unit tests", "status": "completed", "conclusion": "success"}
        ]
        self.statuses = []
        self.reviews = []
        self.files = [action_file()]
        self.comments = []
        self.calls = []
        self.hide_comments = False
        self.move_head = False
        self.pr_reads = 0
        self.merge_error = None
        self.sources = {}

    def request(self, method, path, data=None, **kwargs):
        self.calls.append((method, path, copy.deepcopy(data)))
        if method == "GET" and path == "actions/workflows/required.yml":
            return {
                "id": 1,
                "path": ".github/workflows/required.yml",
                "state": "active",
            }
        if method == "GET" and path.startswith("actions/workflows/1/runs?"):
            return {"workflow_runs": copy.deepcopy(self.runs)}
        if method == "GET" and path == "commits/" + HEAD + "/status":
            return {"statuses": copy.deepcopy(self.statuses)}
        if method == "GET" and path == "pulls/17":
            self.pr_reads += 1
            value = copy.deepcopy(self.pr)
            if self.move_head and self.pr_reads >= 2:
                value["head"]["sha"] = "d" * 40
            return value
        if method == "GET" and path.startswith("contents/"):
            if path in self.sources:
                text = self.sources[path]
            elif path.startswith("contents/.github/workflows/"):
                text = (
                    "\n".join(
                        line[1:]
                        for line in self.files[0]["patch"].splitlines()
                        if line.startswith("-" if path.endswith(BASE) else "+")
                    )
                    + "\n"
                )
            else:
                raise AssertionError(path)
            return {
                "type": "file",
                "sha": "fixture",
                "encoding": "base64",
                "content": base64.b64encode(text.encode()).decode(),
            }
        if method == "PUT" and path == "pulls/17/merge":
            if self.merge_error:
                raise self.merge_error
            return {"merged": True, "sha": "e" * 40}
        if method == "POST" and path == "issues/17/comments":
            row = {
                "id": len(self.comments) + 1,
                "body": data["body"],
                "user": {"login": "github-actions[bot]"},
            }
            self.comments.append(row)
            return row
        raise AssertionError((method, path, data))

    def items(self, path):
        if path == "pulls?state=open":
            rows = [{"number": 17}]
        elif path == "actions/runs/9/jobs?filter=latest":
            rows = self.jobs
        elif path == "commits/" + HEAD + "/check-runs?filter=latest":
            rows = self.checks
        elif path == "pulls/17/reviews":
            rows = self.reviews
        elif path == "pulls/17/files":
            rows = self.files
        elif path == "issues/17/comments":
            rows = [] if self.hide_comments else self.comments
        else:
            raise AssertionError(path)
        return iter(copy.deepcopy(rows))


class MemoryStore:
    def __init__(self, value=None):
        self.value = copy.deepcopy(value or {"notifications": {}})
        self.durable = copy.deepcopy(self.value)
        self.saves = 0
        self.fail_save = 0

    def save(self):
        self.saves += 1
        if self.saves == self.fail_save:
            raise RuntimeError("injected acknowledgment failure")
        self.durable = copy.deepcopy(self.value)


class DependabotPolicyTests(unittest.TestCase):
    def run_policy(self, api, *, apply=True, store=None):
        return merge.process(
            api,
            REPO,
            "main",
            store or MemoryStore(),
            apply,
            RUN,
            lambda action, tag: PIN,
        )

    def test_green_exact_head_merges_with_atomic_sha(self):
        api = FixtureAPI()
        result = self.run_policy(api)
        self.assertEqual(result["pull_requests"][0]["state"], "merged")
        payload = next(c[2] for c in api.calls if c[:2] == ("PUT", "pulls/17/merge"))
        self.assertEqual(payload, {"sha": HEAD, "merge_method": "squash"})
        self.assertFalse(api.comments)

    def test_human_fork_draft_and_wrong_base_never_merge(self):
        for kind in ["human", "fork", "draft", "base"]:
            with self.subTest(kind=kind):
                api = FixtureAPI()
                if kind == "human":
                    api.pr["user"] = {"login": "ArturSepp", "type": "User"}
                if kind == "fork":
                    api.pr["head"]["repo"]["full_name"] = "other/repo"
                if kind == "draft":
                    api.pr["draft"] = True
                if kind == "base":
                    api.pr["base"]["ref"] = "stable"
                self.assertFalse(self.run_policy(api)["pull_requests"])
                self.assertFalse([c for c in api.calls if c[0] != "GET"])

    def test_old_head_success_does_not_pass(self):
        api = FixtureAPI()
        api.runs[0]["head_sha"] = BASE
        self.assertEqual(self.run_policy(api)["pull_requests"][0]["state"], "pending")
        self.assertFalse(api.comments)

    def test_latest_failed_attempt_wins_over_previous_success(self):
        api = FixtureAPI()
        api.runs.append({**api.runs[0], "id": 10, "conclusion": "failure"})
        result = self.run_policy(api)
        self.assertEqual(result["pull_requests"][0]["state"], "failed")
        self.assertEqual(len(api.comments), 1)
        self.assertFalse([c for c in api.calls if c[1].endswith("/merge")])

    def test_required_rollup_must_really_exist_in_trusted_run(self):
        api = FixtureAPI()
        api.jobs = [{"name": "Something else", "conclusion": "success"}]
        self.assertEqual(self.run_policy(api)["pull_requests"][0]["state"], "blocked")

    def test_pending_and_failed_other_checks_prevent_merge(self):
        for state, expected in [("in_progress", "pending"), ("failure", "failed")]:
            api = FixtureAPI()
            if state == "in_progress":
                api.checks[0]["status"] = state
            else:
                api.checks[0]["conclusion"] = state
            self.assertEqual(
                self.run_policy(api)["pull_requests"][0]["state"], expected
            )
            self.assertFalse([c for c in api.calls if c[1].endswith("/merge")])

    def test_external_status_and_review_objection_prevent_merge(self):
        api = FixtureAPI()
        api.statuses = [{"context": "docs", "state": "failure"}]
        self.assertEqual(self.run_policy(api)["pull_requests"][0]["state"], "failed")
        api = FixtureAPI()
        api.reviews = [{"user": {"login": "reviewer"}, "state": "CHANGES_REQUESTED"}]
        self.assertEqual(self.run_policy(api)["pull_requests"][0]["state"], "blocked")

    def test_head_move_before_merge_is_not_merged_or_notified(self):
        api = FixtureAPI()
        api.move_head = True
        self.assertEqual(
            self.run_policy(api)["pull_requests"][0]["state"], "changed_during_check"
        )
        self.assertFalse([c for c in api.calls if c[0] != "GET"])

    def test_protected_merge_failure_notifies_once(self):
        api, store = FixtureAPI(), MemoryStore()
        api.merge_error = GitHubError("GitHub refused merge", status=405)
        self.assertEqual(
            self.run_policy(api, store=store)["pull_requests"][0]["state"],
            "merge_failed",
        )
        self.run_policy(api, store=store)
        self.assertEqual(len(api.comments), 1)
        self.assertIn("@ArturSepp", api.comments[0]["body"])

    def test_transient_api_error_is_unverified_not_false_ci_failure(self):
        api = FixtureAPI()
        api.merge_error = GitHubError("temporary", status=503)
        result = self.run_policy(api)
        self.assertEqual(result["pull_requests"][0]["state"], "unverified")
        self.assertTrue(result["infrastructure_errors"])
        self.assertFalse(api.comments)

    def test_dry_run_never_mutates(self):
        api = FixtureAPI()
        self.assertEqual(
            self.run_policy(api, apply=False)["pull_requests"][0]["state"], "ready"
        )
        self.assertFalse([c for c in api.calls if c[0] != "GET"])

    def test_code_policy_file_and_workflow_logic_changes_need_review(self):
        for file in [
            action_file("src/code.py"),
            action_file(merge.CALLER),
            {
                **action_file(),
                "patch": "@@ -1 +1 @@\n-permissions: read-all\n+permissions: write-all",
            },
        ]:
            api = FixtureAPI()
            api.files = [file]
            self.assertEqual(
                self.run_policy(api)["pull_requests"][0]["state"], "blocked"
            )
            self.assertFalse([c for c in api.calls if c[1].endswith("/merge")])

    def test_action_sha_must_match_upstream_tag(self):
        with self.assertRaises(merge.ManualReview):
            merge.verify_diff(FixtureAPI(), pr(), lambda action, tag: "f" * 40)

    def test_pyproject_only_dependency_versions_may_change(self):
        before = '[project]\nname="test"\nversion="1"\ndependencies=["numpy>=2"]\n'
        self.assertEqual(
            merge.project_shape(before),
            merge.project_shape(before.replace(">=2", ">=3")),
        )
        self.assertNotEqual(
            merge.project_shape(before),
            merge.project_shape(before.replace("numpy", "pandas")),
        )
        self.assertNotEqual(
            merge.project_shape(before),
            merge.project_shape(before.replace('version="1"', 'version="2"')),
        )
        with self.assertRaises(merge.ManualReview):
            merge.project_shape(
                before.replace("numpy>=2", "numpy @ https://example.org/a.whl")
            )

    def test_lock_artifact_registry_yank_and_hash_contracts(self):
        before = 'version=1\n[[package]]\nname="test"\nversion="1"\nsource={registry="https://pypi.org/simple"}\n'
        url = "https://files.pythonhosted.org/test.whl"
        after = (
            before.replace('version="1"', 'version="2"')
            + f'wheels=[{{url="{url}",hash="sha256:abc",size=1}}]\n'
        )
        metadata = {
            "urls": [
                {"url": url, "digests": {"sha256": "abc"}, "size": 1, "yanked": False}
            ]
        }
        merge.verify_lock(before, after, lambda u: metadata)
        for bad in [
            after.replace("sha256:abc", "sha256:bad"),
            after.replace("pypi.org", "evil.example.org"),
        ]:
            with self.assertRaises(merge.ManualReview):
                merge.verify_lock(before, bad, lambda u: metadata)
        metadata["urls"][0]["yanked"] = True
        with self.assertRaises(merge.ManualReview):
            merge.verify_lock(before, after, lambda u: metadata)

    def test_interrupted_notification_and_hidden_comments_cannot_duplicate(self):
        api, store = FixtureAPI(), MemoryStore()
        store.fail_save = 2
        with self.assertRaises(RuntimeError):
            merge.notify(api, store, pr(), "failed", ["unit: failure"], RUN)
        self.assertEqual(len(api.comments), 1)
        recovered = MemoryStore(store.durable)
        api.hide_comments = True
        with self.assertRaisesRegex(RuntimeError, "refusing a duplicate"):
            merge.notify(api, recovered, pr(), "failed", ["unit: failure"], RUN)
        self.assertEqual(len(api.comments), 1)
        api.hide_comments = False
        merge.notify(api, recovered, pr(), "failed", ["unit: failure"], RUN)
        self.assertEqual(len(api.comments), 1)
        self.assertEqual(
            next(iter(recovered.value["notifications"].values()))["phase"], "sent"
        )

    def test_repeat_failure_run_url_does_not_repeat_notification(self):
        api, store = FixtureAPI(), MemoryStore()
        merge.notify(
            api, store, pr(), "failed", ["Required: failure (" + RUN + ")"], RUN
        )
        merge.notify(
            api, store, pr(), "failed", ["Required: failure (" + RUN + "2)"], RUN + "2"
        )
        self.assertEqual(len(api.comments), 1)

    def test_state_write_failure_prevents_comment(self):
        api, store = FixtureAPI(), MemoryStore()
        store.fail_save = 1
        with self.assertRaises(RuntimeError):
            merge.notify(api, store, pr(), "failed", ["unit failed"], RUN)
        self.assertFalse(api.comments)

    def test_untrusted_events_and_other_repositories_cannot_apply(self):
        for event in ["pull_request", "pull_request_target"]:
            with (
                patch.dict(
                    os.environ,
                    {
                        "GITHUB_ACTIONS": "true",
                        "GITHUB_REPOSITORY": REPO,
                        "GITHUB_EVENT_NAME": event,
                        "GITHUB_REF": "refs/heads/main",
                    },
                ),
                patch.object(merge, "RepoAPI") as api,
                redirect_stdout(io.StringIO()),
                tempfile.TemporaryDirectory() as directory,
            ):
                api.return_value.request.return_value = {"default_branch": "main"}
                self.assertEqual(
                    merge.main(
                        ["--repository", REPO, "--output-dir", directory, "--apply"]
                    ),
                    2,
                )
                api.return_value.items.assert_not_called()
        with redirect_stdout(io.StringIO()), tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                merge.main(["--repository", "other/repo", "--output-dir", directory]), 2
            )

    def test_generated_callers_cover_registry_without_pr_checkout(self):
        registry = json.loads((generator.HERE / "public_registry.json").read_text())
        self.assertEqual(len(registry["packages"]), 11)
        for index, package in enumerate(registry["packages"]):
            source = generator.render(package, HEAD, 7 + 4 * index)
            value = yaml.load(source, Loader=yaml.BaseLoader)
            self.assertEqual(
                set(value["on"]), {"workflow_run", "schedule", "workflow_dispatch"}
            )
            self.assertNotIn("actions/checkout", source)
            self.assertIn("dependabot-merge@" + HEAD, source)
            self.assertEqual(value["concurrency"]["cancel-in-progress"], "false")
            self.assertEqual(value["permissions"], {})
            self.assertIn("refs/heads/main", value["jobs"]["merge"]["if"])
        with self.assertRaises(ValueError):
            generator.render({"repo": "test"}, "main", 7)

    def test_composite_action_is_pinned_and_only_executes_shared_script(self):
        source = (
            generator.HERE.parent / ".github/actions/dependabot-merge/action.yml"
        ).read_text()
        value = yaml.load(source, Loader=yaml.BaseLoader)
        for step in value["runs"]["steps"]:
            if "uses" in step:
                self.assertRegex(step["uses"], r"@[a-f0-9]{40}$")
        self.assertIn(
            "$GITHUB_ACTION_PATH/../../../scripts/dependabot_merge.py", source
        )
        self.assertNotIn("actions/checkout", source)
        self.assertNotIn("pull_request.head", source)

    def test_truncated_patch_cannot_hide_workflow_logic_change(self):
        api = FixtureAPI()
        path = "contents/.github/workflows/ci.yml?ref="
        api.sources[path + BASE] = (
            "  - uses: astral-sh/setup-uv@"
            + BASE
            + " # v1.0.0\npermissions: read-all\n"
        )
        api.sources[path + HEAD] = (
            "  - uses: astral-sh/setup-uv@"
            + PIN
            + " # v1.0.1\npermissions: write-all\n"
        )
        self.assertEqual(self.run_policy(api)["pull_requests"][0]["state"], "blocked")
        self.assertFalse([c for c in api.calls if c[1].endswith("/merge")])

    def test_paginated_job_and_check_envelopes(self):
        for path, key in [
            ("commits/a/check-runs?filter=latest", "check_runs"),
            ("actions/runs/9/jobs?filter=latest", "jobs"),
        ]:
            api = merge.RepoAPI(REPO, "fixture-token")
            with patch.object(
                api, "request", side_effect=[{key: list(range(100))}, {key: [100]}]
            ) as get:
                self.assertEqual(list(api.items(path)), list(range(101)))
                self.assertIn("page=2", get.call_args.args[1])

    def test_state_cas_reconciles_lost_ack_and_rejects_divergence(self):
        initial = {"schema_version": 1, "repository": REPO, "notifications": {}}
        intended = {**initial, "notifications": {"fixture": {"phase": "posting"}}}

        def metadata(value, sha):
            return {
                "sha": sha,
                "encoding": "base64",
                "content": base64.b64encode(json.dumps(value).encode()).decode(),
            }

        from unittest.mock import Mock

        for remote, succeeds in [(intended, True), (initial, False)]:
            api = Mock()
            api.request.side_effect = [
                metadata(initial, BASE),
                GitHubError("lost acknowledgment"),
                metadata(remote, HEAD),
            ]
            store = merge.Store(api, REPO)
            store.value = copy.deepcopy(intended)
            if succeeds:
                store.save()
                self.assertEqual(store.sha, HEAD)
            else:
                with self.assertRaisesRegex(RuntimeError, "refusing further mutations"):
                    store.save()
            payload = api.request.call_args_list[1].args[2]
            self.assertEqual(payload["sha"], BASE)
            self.assertEqual(payload["branch"], merge.BRANCH)

    def test_cli_repository_metadata_uses_canonical_root_url(self):
        api = merge.RepoAPI(REPO, "fixture-token")
        with patch(
            "documentation_monitor_actions.urllib.request.build_opener"
        ) as build:
            build.return_value.open.return_value.__enter__.return_value = io.BytesIO(
                b'{"default_branch":"main"}'
            )
            self.assertEqual(api.request("GET", "")["default_branch"], "main")
            request = build.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, "https://api.github.com/repos/" + REPO)

    def test_invalid_state_cannot_be_reset(self):
        from unittest.mock import Mock

        api = Mock()
        invalid = {"schema_version": 1, "repository": "other/repo", "notifications": {}}
        api.request.return_value = {
            "sha": BASE,
            "encoding": "base64",
            "content": base64.b64encode(json.dumps(invalid).encode()).decode(),
        }
        with self.assertRaisesRegex(ValueError, "refusing to reset"):
            merge.Store(api, REPO)
        self.assertEqual(api.request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
