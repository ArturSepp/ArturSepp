"""Contract tests for graph errors, release history and unavailable external data."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conformance as c
import update_github_about as about
import build_stats


class RegistryTests(unittest.TestCase):
    def test_approved_graph_and_additive_about_updates(self):
        registry = c.load_registry()
        self.assertEqual(len(registry["packages"]), 10)
        command = next(x for x in about.commands(registry) if "ArturSepp/privateassets" in x)
        self.assertIn("cash-flows", command)
        self.assertNotIn("--remove-topic", command)

    def test_generated_content_changes_are_detected_with_unchanged_stamp(self):
        block = "<!-- ===== SHARED AGENT CORE standalone \u2014 begin =====\nagent core v1.5. -->\nUse the public API.\n<!-- ===== SHARED AGENT CORE \u2014 end ===== -->"
        self.assertNotEqual(c.agent_block_digest(block), c.agent_block_digest(block.replace("public API", "private API")))
        package = c.load_registry()["packages"][0]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, relative in (("release.yml", ".github/workflows/release.yml"), ("release_guard.py", ".github/scripts/release_guard.py"), ("publish_tag.py", ".github/scripts/publish_tag.py")):
                source = c.render_release_template(name, package)
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source, encoding="utf-8")
            self.assertEqual(c.generated_release_drift(root, package), [])
            workflow = root / ".github/workflows/release.yml"
            workflow.write_text(workflow.read_text(encoding="utf-8").replace("skip-existing: false", "skip-existing: true"), encoding="utf-8")
            self.assertEqual(c.generated_release_drift(root, package), [".github/workflows/release.yml"])

    def test_bloomberg_release_installs_external_sdk_after_each_environment_sync(self):
        packages = c.load_registry()["packages"]
        package = next(p for p in packages if p["import"] == "bbg_fetch")
        workflow = c.render_release_template("release.yml", package)
        index = "--index-url=https://blpapi.bloomberg.com/repository/releases/python/simple blpapi"
        self.assertEqual(workflow.count(index), 3)
        for sync in ("uv sync --locked --group test", "uv sync --locked --extra docs"):
            self.assertIn(sync + "\n          uv pip install --python .venv " + index, workflow)
        self.assertNotIn(index, c.render_release_template("release.yml", packages[0]))

    def test_profile_offline_render_preserves_recorded_counts(self):
        readme = (Path(c.__file__).parent.parent / "README.md").read_text(encoding="utf-8")
        counts, downloads = build_stats.existing_metrics(readme)
        totals, table = build_stats.build_blocks(counts, downloads)
        self.assertEqual(table.count("[Docs]"), 10)
        self.assertEqual(build_stats.existing_metrics(table), (counts, downloads))

    def test_svm_release_gates_upload_and_optional_page_on_tagged_windows_regressions(self):
        packages = c.load_registry()["packages"]
        package = next(p for p in packages if p["import"] == "stochvolmodels")
        workflow = c.render_release_template("release.yml", package)
        self.assertIn('uv run --no-sync pytest -m "not slow"', workflow)
        numerical = workflow.split("  windows-numerical:\n", 1)[1].split("  publish:\n", 1)[0]
        self.assertIn("runs-on: windows-latest", numerical)
        self.assertIn("ref: ${{ needs.validate.outputs.sha }}", numerical)
        self.assertIn("uv sync --locked --group test", numerical)
        self.assertIn("uv run --no-sync pytest -m slow -v", numerical)
        self.assertNotIn("id-token:", numerical)
        self.assertIn("needs: [validate, windows-numerical]\n", workflow)
        self.assertIn("needs: [validate, windows-numerical, publish]\n", workflow)
        self.assertIn("needs.windows-numerical.result == 'success'", workflow)
        for other in packages:
            if other["import"] != "stochvolmodels":
                self.assertNotIn("windows-numerical", c.render_release_template("release.yml", other))

    def test_cycle_rejected(self):
        registry = c.load_registry()
        registry["packages"][0]["core"] = ["optimalportfolios"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cycle"):
                c.load_registry(path)

    def test_unknown_apis_never_pass(self):
        registry = c.load_registry()
        result = c.network_checks(Path("missing"), registry["packages"][0], registry, fetch=lambda _: {"message": "rate limited"})
        self.assertTrue(result)
        self.assertTrue(any(x["state"] == "unknown" for x in result))
        self.assertTrue(all(x["state"] in {"unknown", "known-gap"} for x in result))

    def test_pypi_documentation_value_is_checked_when_url_keys_match(self):
        registry = c.load_registry()
        package = registry["packages"][0]
        urls = dict.fromkeys(c.URL_KEYS, "https://example.invalid")
        urls["Documentation"] = "https://example.github.io/stale"
        def fetch(url):
            if "pypi.org" in url:
                return {"releases": {}, "info": {"summary": package["summary"], "project_urls": urls}}
            return {"description": package["summary"], "homepage": f"https://{package['rtd']}.readthedocs.io", "topics": package["topics"]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text('[project]\nname="qis"\nversion="1.0.0"\n')
            checks = c.network_checks(root, package, registry, fetch=fetch)
        self.assertEqual(next(x for x in checks if x["check"] == "pypi_metadata")["state"], "fail")


class ReleaseHistoryTests(unittest.TestCase):
    def test_recorded_gap_does_not_hide_new_untagged_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text('[project]\nname="sample"\nversion="1.0.2"\n')
            releases = {v: [{"upload_time_iso_8601": "2026-09-07T12:00:00Z"}] for v in ("1.0.0", "1.0.1")}
            checks = c.release_checks(root, {"dist": "sample"}, {"releases": releases}, "2026-08-01", {"1.0.0": {"reason": "Recorded ambiguous source"}})
            self.assertEqual(sum(x["state"] == "known-gap" for x in checks), 1)
            self.assertEqual(sum(x["state"] == "fail" for x in checks), 1)

    def test_missing_intermediate_and_wrong_tag_metadata_are_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
            git("init", "-q")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            project = root / "pyproject.toml"
            project.write_text('[project]\nname = "sample"\nversion = "1.0.0"\n', encoding="utf-8")
            git("add", "pyproject.toml")
            git("commit", "-qm", "initial")
            git("tag", "v1.0.0")
            git("tag", "v1.0.2")
            project.write_text('[project]\nname = "sample"\nversion = "1.1.0"\n', encoding="utf-8")
            releases = {v: [{"upload_time_iso_8601": "2026-09-07T12:00:00Z"}] for v in ("1.0.0", "1.0.1", "1.0.2")}
            checks = c.release_checks(root, {"dist": "sample"}, {"releases": releases}, "2026-08-01")
            self.assertEqual(sum(x["state"] == "fail" for x in checks), 2)
            self.assertEqual(checks[-1]["state"], "pass")
            self.assertIn("prepared/unpublished", checks[-1]["detail"])


if __name__ == "__main__":
    unittest.main()
