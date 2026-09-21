"""Regression tests for staged exports, portable source checks and the required gate."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "oss_checks", Path(__file__).resolve().parents[1] / "repo_governance" / "oss_checks.py"
)
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class SnapshotTests(unittest.TestCase):
    def test_index_uses_staged_blob_and_preserves_space_in_path(self):
        record = b"100644 abc123 0\tfile with spaces.py\0"
        with patch.object(checks, "git", return_value=record):
            self.assertEqual(
                checks.entries(Path(".")), [("100644", "abc123", "file with spaces.py")]
            )

    def test_unmerged_index_is_rejected(self):
        with (
            patch.object(checks, "git", return_value=b"100644 abc123 2\tbroken.py\0"),
            self.assertRaises(checks.CheckFailure),
        ):
            checks.entries(Path("."))

    def test_tree_uses_committed_blob(self):
        with patch.object(checks, "git", return_value=b"100644 blob abc123\tcommitted.py\0"):
            self.assertEqual(
                checks.entries(Path("."), "HEAD"), [("100644", "abc123", "committed.py")]
            )

    def test_staged_export_does_not_read_working_file_or_honour_export_ignore(self):
        content = b"def broken(:\n"
        raw = b"abc123 blob " + str(len(content)).encode() + b"\n" + content + b"\n"
        result = subprocess.CompletedProcess([], 0, raw, b"")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "working").mkdir()
            (root / "working" / "test contract.py").write_text("valid = True\n")
            (root / "snapshot").mkdir()
            with patch.object(checks.subprocess, "run", return_value=result):
                checks.export(
                    root / "working", [("100644", "abc123", "test contract.py")], root / "snapshot"
                )
            with self.assertRaises(checks.CheckFailure):
                checks.source_checks(root / "snapshot", ["test contract.py"])
            checks.source_checks(root / "working", ["test contract.py"])

    def test_good_staged_content_is_independent_of_bad_working_content(self):
        content = b"answer = 42\n"
        raw = b"abc123 blob " + str(len(content)).encode() + b"\n" + content + b"\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "answer.py").write_text("def broken(:\n")
            snapshot = root / "snapshot"
            with patch.object(
                checks.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, raw, b"")
            ):
                checks.export(root, [("100644", "abc123", "answer.py")], snapshot)
            checks.source_checks(snapshot, ["answer.py"])
            with self.assertRaises(checks.CheckFailure):
                checks.source_checks(root, ["answer.py"])

    def test_snapshot_rejects_traversal_and_windows_drive_paths(self):
        for path in ("../outside", "/absolute", "C:/outside", "x\\..\\outside"):
            with self.subTest(path=path), self.assertRaises(checks.CheckFailure):
                checks.safe_path(path)

    def test_added_lines_excludes_deleted_hunk(self):
        patch_text = "+++ b/src/file.py\n@@ -1,2 +1,0 @@\n@@ -5 +3,2 @@\n"
        self.assertEqual(checks.added_lines(patch_text), {"src/file.py": {3, 4}})

    def test_selection_fingerprint_changes_on_deletion_or_mode(self):
        items = [("100644", "abc", "file.py")]
        self.assertNotEqual(checks.fingerprint(items), checks.fingerprint([]))
        self.assertNotEqual(
            checks.fingerprint(items), checks.fingerprint([("100755", "abc", "file.py")])
        )


class ContractTests(unittest.TestCase):
    def test_required_jobs_fail_closed(self):
        for status in ("skipped", "cancelled", "failure", "timed_out", None):
            needs = {} if status is None else {"docs": {"result": status}}
            with self.subTest(status=status), self.assertRaises(checks.CheckFailure):
                checks.validate_gate(needs, ["docs"])
        checks.validate_gate({"docs": {"result": "success"}}, ["docs"])

    def test_only_declared_optional_job_can_skip(self):
        checks.validate_gate(
            {"ci": {"result": "success"}, "audit": {"result": "skipped"}}, ["ci"], ["audit"]
        )
        with self.assertRaises(checks.CheckFailure):
            checks.validate_gate({"ci": {"result": "success"}}, ["ci"], ["audit"])

    def test_github_on_key_and_malformed_workflow(self):
        self.assertIn("on", checks.load_yaml("on:\n  push:\njobs:\n  ci: {}\n"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ".github/workflows/test.yml"
            path.parent.mkdir(parents=True)
            path.write_text("name: incomplete\n")
            with self.assertRaises(checks.CheckFailure):
                checks.source_checks(root, [".github/workflows/test.yml"])

    def test_shared_guide_anchor_regression(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "guide.md"
            url = "https://github.com/ArturSepp/ArturSepp/blob/main/docs/documentation_standard.md#"
            path.write_text(f"[guide]({url}article-structure)")
            with self.assertRaises(checks.CheckFailure):
                checks.source_checks(root, ["guide.md"])
            path.write_text(f"[guide]({url}user-content-article-structure)")
            checks.source_checks(root, ["guide.md"])

    def test_metadata_catches_partial_version_update(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text('[project]\nname="example"\nversion="2.0.0"\n')
            (root / "CITATION.cff").write_text('version: "1.0.0"\n')
            with self.assertRaises(checks.CheckFailure):
                checks.metadata_checks(root, ["pyproject.toml"])
            (root / "CITATION.cff").write_text('version: "2.0.0"\n')
            checks.metadata_checks(root, ["pyproject.toml"])

    def test_qis_lint_does_not_accept_new_violation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.py").write_text("import os\nunknown_name\n")
            findings = [
                {
                    "filename": str(root / "a.py"),
                    "location": {"row": n},
                    "code": "F821",
                    "message": "bad",
                }
                for n in (1, 2)
            ]
            result = subprocess.CompletedProcess([], 1, json.dumps(findings).encode(), b"")
            config = {"lint_paths": ["*.py"], "lint_changed_lines": True}
            with patch.object(checks.subprocess, "run", return_value=result):
                checks.lint(root, ["a.py"], {"a.py": {3}}, config)
                with self.assertRaises(checks.CheckFailure):
                    checks.lint(root, ["a.py"], {"a.py": {2}}, config)


if __name__ == "__main__":
    unittest.main()
