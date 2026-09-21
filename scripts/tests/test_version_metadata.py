"""Version repair is explicit and leaves third-party citations untouched."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "sync_versions",
    Path(__file__).resolve().parents[1] / "repo_governance/sync_version_metadata.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class VersionMetadataTests(unittest.TestCase):
    def test_preview_repairs_coupled_versions_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[project]\nversion="2.0.0"\n[project.urls]\n'
                'Repository="https://github.com/ArturSepp/Example"\n'
            )
            (root / "CITATION.cff").write_text('version: "1.0.0"\ndate-released: 2025-01-01\n')
            own = (
                "@software{own,\nversion={1.0.0},\nurl={https://github.com/ArturSepp/Example}\n}\n"
            )
            other = (
                "@software{other,\nversion={3.0.0},\nurl={https://github.com/other/library}\n}\n"
            )
            (root / "README.md").write_text(own + other)
            proposed = module.proposed_changes(root)
            self.assertEqual(len(proposed), 2)
            self.assertIn("date-released: 2025-01-01", proposed[0][2])
            self.assertIn("version={2.0.0}", proposed[1][2])
            self.assertIn(other, proposed[1][2])
            self.assertEqual((root / "README.md").read_text(), own + other)

    def test_matching_version_does_not_reformat_citation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text('[project]\nversion="1.0.0"\n')
            (root / "CITATION.cff").write_text("version: 1.0.0\n")
            self.assertEqual(module.proposed_changes(root), [])


class ConsumerGraphTests(unittest.TestCase):
    def test_core_and_optional_edges_use_import_names(self):
        script = Path(__file__).resolve().parents[1] / "repo_governance/audit_commit_safety.py"
        spec = importlib.util.spec_from_file_location("adoption", script)
        adoption = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adoption)
        import json

        registry = json.loads((script.parents[1] / "public_registry.json").read_text())
        packages = {p["import"]: p for p in registry["packages"]}
        vanilla = adoption.consumer_targets(registry, packages["vanilla_option_pricers"])
        self.assertEqual(
            {p["module"] for p in vanilla}, {"stochvolmodels", "option_chain_analytics"}
        )
        bloomberg = adoption.consumer_targets(registry, packages["bbg_fetch"])
        self.assertEqual(
            [(p["module"], p["extra"]) for p in bloomberg],
            [("option_chain_analytics", "bloomberg")],
        )
