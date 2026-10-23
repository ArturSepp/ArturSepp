"""Run the real setup and launcher with only one registered checkout present."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

GOVERNANCE = Path(__file__).resolve().parents[1] / "repo_governance"
SHELLS = [path for name in ("powershell.exe", "pwsh") if (path := shutil.which(name))]


@unittest.skipUnless(os.name == "nt" and SHELLS, "Windows PowerShell is required")
class AgentRepoSetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agent repo setup ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repositories = self.root / "repositories"
        self.repo = self.repositories / "Present"
        self.repo.mkdir(parents=True)
        self.worktree = self.root / "linked worktree"
        self.worktree.mkdir()
        self.python_root = self.root / "python"
        interpreter = self.python_root / "Present312/Scripts/python.exe"
        interpreter.parent.mkdir(parents=True)
        interpreter.touch()  # Dry runs only: no environment or interpreter is created.
        self.present = {
            "name": "Present",
            "directory": "Present",
            "python_environment": "Present312",
            "tasks": {"check": {"steps": [{"name": "Fixture check", "kind": "code",
                                           "code": "print('fixture')"}]}},
        }
        self.entries = [dict(self.present, name="MissingBefore", directory="MissingBefore"),
                        self.present,
                        dict(self.present, name="MissingAfter", directory="MissingAfter")]

    @staticmethod
    def quote(value):
        return "'" + str(value).replace("'", "''") + "'"

    def run_script(self, shell, script, *, cwd=None, arguments=""):
        registry = self.root / "registry.json"
        registry.write_text(json.dumps({"external_environment_root": str(self.python_root),
                                        "repositories": self.entries}), encoding="utf-8")
        cwd = cwd or self.repo
        command = f"""
$ErrorActionPreference = 'Stop'
# Model Git's two read-only responses without creating disposable Git metadata.
function global:git {{
    $global:LASTEXITCODE = 0
    if ($args -contains '--git-common-dir') {{ {self.quote(self.repo / '.git')}; return }}
    if ($args -contains '--show-toplevel') {{ {self.quote(cwd)}; return }}
    throw 'Unexpected Git query in setup regression'
}}
Set-Location -LiteralPath {self.quote(cwd)}
& {self.quote(GOVERNANCE / script)} -RegistryPath {self.quote(registry)} `
    -RepositoriesRoot {self.quote(self.repositories)} {arguments}
"""
        environment = dict(os.environ, LOCALAPPDATA=str(self.root / "local"),
                           PORTFOLIO_PYTHON_ROOT=str(self.python_root))
        return subprocess.run([shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                               "-Command", command],
                              capture_output=True, text=True, errors="replace",
                              env=environment, timeout=30, check=False)

    def assert_success(self, script, *, cwd=None, arguments="", expected="Present"):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_script(shell, script, cwd=cwd, arguments=arguments)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(expected, result.stdout)

    def test_setup_ignores_missing_siblings(self):
        self.assert_success("Enter-AgentRepo.ps1")

    def test_launcher_infers_checkout_with_missing_siblings(self):
        self.assert_success("Invoke-Repo.ps1", arguments="-Task check -DryRun",
                            expected="0 failures")

    def test_launcher_explicit_checkout_with_missing_siblings(self):
        self.assert_success("Invoke-Repo.ps1", arguments="-Task check -Repo Present -DryRun",
                            expected="0 failures")

    def test_setup_recognises_linked_worktree_with_missing_siblings(self):
        self.assert_success("Enter-AgentRepo.ps1", cwd=self.worktree,
                            expected="Present312")

    def test_launcher_infers_linked_worktree_with_missing_siblings(self):
        self.assert_success("Invoke-Repo.ps1", cwd=self.worktree,
                            arguments="-Task check -DryRun", expected="0 failures")

    def test_unregistered_checkout_is_rejected(self):
        self.entries = [self.entries[0], self.entries[2]]
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_script(shell, "Enter-AgentRepo.ps1")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("does not resolve to exactly one repository", result.stderr)

    def test_explicit_missing_checkout_is_rejected(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_script(shell, "Invoke-Repo.ps1",
                                         arguments="-Task check -Repo MissingBefore -DryRun")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("MissingBefore", result.stderr)

    def test_ambiguous_checkout_is_rejected(self):
        self.entries = [self.present, dict(self.present, name="Duplicate")]
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_script(shell, "Enter-AgentRepo.ps1")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("does not resolve to exactly one repository", result.stderr)
