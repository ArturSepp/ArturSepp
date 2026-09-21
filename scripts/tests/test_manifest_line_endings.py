"""Exercise the real PowerShell manifest checker against portable source fixtures."""

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1] / "repo_governance/Update-AgentCoreManifest.ps1"
)
BLOCK = (
    "<!-- ===== SHARED AGENT CORE (builder variant) — begin =====\n"
    "Last synced 2026-09-13, agent core v1.6 -->\n"
    "Never change numerical results.\n"
    "<!-- ===== SHARED AGENT CORE — end ===== -->"
)


@unittest.skipUnless(
    shutil.which("pwsh"), "PowerShell 7 is required for the local policy tool"
)
class ManifestLineEndingTests(unittest.TestCase):
    def check_source(self, source):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Package").mkdir()
            (root / "Package/AGENTS.md").write_bytes(source.encode("utf-8"))
            registry = root / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "agent_core_version": "1.6",
                        "packages": [{"local_dir": "Package"}],
                    }
                ),
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "version": "1.6",
                        "date": "2026-09-13",
                        "sha256": {
                            "Package": hashlib.sha256(BLOCK.encode("utf-8")).hexdigest()
                        },
                    }
                ),
                encoding="utf-8",
            )
            return subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(SCRIPT),
                    "-PublicRegistryPath",
                    str(registry),
                    "-ManifestPath",
                    str(manifest),
                    "-RepositoriesRoot",
                    str(root),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

    def test_lf_source_matches(self):
        result = self.check_source(BLOCK)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_crlf_source_matches_the_same_manifest(self):
        result = self.check_source(BLOCK.replace("\n", "\r\n"))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_substantive_changes_remain_rejected(self):
        result = self.check_source(BLOCK.replace("Never", "Always"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("digest differs", result.stderr)
