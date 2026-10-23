"""Contract tests for graph errors, release history and unavailable external data."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conformance as c
import update_github_about as about
import build_stats
import generate_release_files


class RegistryTests(unittest.TestCase):
    def test_approved_graph_and_additive_about_updates(self):
        registry = c.load_registry()
        self.assertEqual(len(registry["packages"]), 11)
        fm = next(p for p in registry["packages"] if p["import"] == "factormodels")
        self.assertEqual(fm["core"], ["qis", "factorlasso"])
        op = next(p for p in registry["packages"] if p["import"] == "optimalportfolios")
        self.assertEqual(op["core"], ["qis"])
        self.assertEqual(op["extras"], {})
        command = next(x for x in about.commands(registry) if "ArturSepp/privateassets" in x)
        self.assertIn("cash-flows", command)
        self.assertNotIn("--remove-topic", command)

    def test_documentation_override_and_existing_rtd_defaults(self):
        packages = c.load_registry()["packages"]
        fm = next(p for p in packages if p["import"] == "factormodels")
        expected = "https://github.com/ArturSepp/FactorModels/blob/main/docs/index.md"
        self.assertEqual(c.documentation_url(fm), expected)
        for package in packages:
            if package["import"] != "factormodels":
                self.assertEqual(c.documentation_url(package),
                                 f"https://{package['rtd']}.readthedocs.io")
        self.assertEqual(build_stats.DOCS[fm["dist"]], expected)
        command = next(x for x in about.commands({"owner": "ArturSepp", "packages": [fm]}))
        self.assertEqual(command[command.index("--homepage") + 1], expected)

    def test_invalid_documentation_override_rejected(self):
        for value in ("", "/docs/index.md", "http://example.org/docs", 7):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                registry = c.load_registry()
                registry["packages"][0]["documentation_url"] = value
                path = Path(temporary) / "registry.json"
                path.write_text(json.dumps(registry), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "documentation_url"):
                    c.load_registry(path)

    def test_documentation_override_drives_source_and_remote_checks(self):
        registry = c.load_registry()
        package = next(p for p in registry["packages"] if p["import"] == "factormodels")
        expected = "https://github.com/ArturSepp/FactorModels/blob/main/docs/index.md"
        urls = dict.fromkeys(c.URL_KEYS, "https://example.org")
        urls["Documentation"] = expected
        def fetch(url):
            if "pypi.org" in url:
                return {"releases": {}, "info": {"summary": package["summary"], "project_urls": urls}}
            return {"description": package["summary"], "homepage": urls["Documentation"],
                    "topics": package["topics"]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = (f"[project]\nname={json.dumps(package['dist'])}\nversion='0.1.0'\n"
                      f"description={json.dumps(package['summary'])}\n[project.urls]\n")
            source += "".join(f"{key}={json.dumps(value)}\n" for key, value in urls.items())
            (root / "pyproject.toml").write_text(source, encoding="utf-8")
            with mock.patch.object(c, "git", return_value=""), \
                 mock.patch.object(c, "generated_release_drift", return_value=[]):
                checks = c.offline_checks(root, package, registry)
            self.assertEqual(next(x for x in checks if x["check"] == "source_metadata")["state"], "pass")
            checks = c.network_checks(root, package, registry, fetch=fetch)
            for name in ("pypi_metadata", "github_about"):
                self.assertEqual(next(x for x in checks if x["check"] == name)["state"], "pass")
            urls["Documentation"] = "https://tradablefactors.readthedocs.io"
            checks = c.network_checks(root, package, registry, fetch=fetch)
            for name in ("pypi_metadata", "github_about"):
                self.assertEqual(next(x for x in checks if x["check"] == name)["state"], "fail")

    def test_agent_manifest_matches_registry_version_and_repository_set(self):
        registry = c.load_registry()
        manifest = json.loads(c.AGENT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], registry["agent_core_version"])
        self.assertEqual(set(manifest["sha256"]), {p["local_dir"] for p in registry["packages"]})

    def test_generated_content_changes_are_detected_with_unchanged_stamp(self):
        block = "<!-- ===== SHARED AGENT CORE standalone \u2014 begin =====\nagent core v1.6. -->\nUse the public API.\n<!-- ===== SHARED AGENT CORE \u2014 end ===== -->"
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

    def test_factormodels_navigation_gate_is_scoped_and_precedes_release_builds(self):
        packages = c.load_registry()["packages"]
        package = next(p for p in packages if p["import"] == "factormodels")
        workflow = c.render_release_template("release.yml", package)
        command = "python tools/check_navigation_refs.py --require-current-source"
        self.assertEqual(workflow.count(command), 1)
        self.assertLess(workflow.index(command), workflow.index("uv sync --locked"))
        self.assertLess(workflow.index("checkout --tag"), workflow.index(command))
        self.assertIn("id-token: write", workflow)
        self.assertIn("skip-existing: false", workflow)
        self.assertIn("environment:\n      name: pypi", workflow)
        for other in packages:
            if other["import"] != "factormodels":
                self.assertNotIn(command, c.render_release_template("release.yml", other))
        with self.assertRaisesRegex(ValueError, "belongs to factormodels"):
            c.render_release_template("release.yml", dict(packages[0], release_navigation_check=True))

    def test_profile_table_uses_live_metrics_for_each_package(self):
        readme = (Path(c.__file__).parent.parent / "README.md").read_text(encoding="utf-8")
        table = build_stats.build_table()
        self.assertEqual(table.count("[Docs]"), len(c.load_registry()["packages"]))
        self.assertEqual(set(build_stats.REPOS),
                         {p["repo"] for p in c.load_registry()["packages"]})
        self.assertEqual(readme, build_stats.replace_table(readme, table))
        for repo, slug in build_stats.REPOS.items():
            self.assertIn(f"img.shields.io/github/stars/ArturSepp/{repo}", table)
            self.assertIn(f"img.shields.io/github/forks/ArturSepp/{repo}", table)
            self.assertIn(f"{build_stats.DOWNLOAD_BADGES}/{slug}-month.svg", table)
            self.assertIn(f"{build_stats.DOWNLOAD_BADGES}/{slug}-total.svg", table)

    def test_profile_render_is_independent_of_working_directory(self):
        source = build_stats.README_PATH.read_text(encoding="utf-8")
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text(source, encoding="utf-8")
            elsewhere = root / "elsewhere"
            elsewhere.mkdir()
            try:
                os.chdir(elsewhere)
                with mock.patch.object(build_stats, "README_PATH", readme), \
                     mock.patch.object(sys, "argv", ["build_stats.py"]):
                    build_stats.main()
            finally:
                os.chdir(original_cwd)
            self.assertEqual(readme.read_text(encoding="utf-8"), source)

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
        # Slow documentation examples run per case on Linux in ci.yml; serially they exceed the Windows timeout.
        self.assertIn("--ignore=src/stochvolmodels/tests/test_docs_examples.py", numerical)
        self.assertNotIn("id-token:", numerical)
        self.assertIn("needs: [validate, windows-numerical]\n", workflow)
        self.assertIn("needs: [validate, windows-numerical, publish]\n", workflow)
        self.assertIn("needs.windows-numerical.result == 'success'", workflow)
        for other in packages:
            if other["import"] != "stochvolmodels":
                self.assertNotIn("windows-numerical", c.render_release_template("release.yml", other))

    def test_op_release_preserves_timezone_and_requires_explicit_backend_lane(self):
        packages = c.load_registry()["packages"]
        package = next(p for p in packages if p["import"] == "optimalportfolios")
        workflow = c.render_release_template("release.yml", package)
        self.assertIn("  TZ: Europe/Zurich\n", workflow)
        self.assertIn("uv sync --locked --group test --extra riskbudget", workflow)
        self.assertIn('OP_REQUIRE_RISKBUDGET: "1"', workflow)
        self.assertIn('pytest -m "riskbudget and not factor_integration"', workflow)
        self.assertLess(workflow.index("uv run --no-sync pytest\n"), workflow.index("--extra riskbudget"))
        self.assertLess(workflow.index("--extra riskbudget"), workflow.index("Build the tagged documentation"))
        self.assertIn("    needs: validate\n", workflow)
        for other in packages:
            if other["import"] != "optimalportfolios":
                rendered = c.render_release_template("release.yml", other)
                self.assertNotIn("riskbudget", rendered)
                self.assertNotIn("\n  TZ: Europe/Zurich\n", rendered)

    def test_op_backend_release_guard_rejects_empty_failed_errored_or_skipped_results(self):
        package = next(p for p in c.load_registry()["packages"] if p["import"] == "optimalportfolios")
        workflow = c.render_release_template("release.yml", package)
        line = next(line for line in workflow.splitlines() if "xml.etree.ElementTree" in line)
        code = line.split('python -c "', 1)[1].removesuffix('"')
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "riskbudget.xml"
            for inner, expected in (("", 1), ("<testcase><failure/></testcase>", 1),
                                    ("<testcase><error/></testcase>", 1),
                                    ("<testcase><skipped/></testcase>", 1), ("<testcase/>", 0)):
                target.write_text("<testsuites><testsuite>" + inner + "</testsuite></testsuites>", encoding="utf-8")
                result = subprocess.run([sys.executable, "-c", code],
                                        env=dict(os.environ, RUNNER_TEMP=temporary), capture_output=True)
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_selected_workflow_generation_preserves_helpers_and_other_repositories(self):
        package = next(p for p in c.load_registry()["packages"] if p["import"] == "optimalportfolios")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / package["local_dir"]
            (target / ".github/scripts").mkdir(parents=True)
            (target / "pyproject.toml").write_text("[project]\nname='optimalportfolios'\n")
            helper = target / ".github/scripts/release_guard.py"
            helper.write_text("# Existing package-specific helper\n")
            arguments = ["generate_release_files.py", "--repos-root", str(root),
                         "--package", "optimalportfolios", "--workflow-only"]
            with mock.patch.object(sys, "argv", arguments), mock.patch("builtins.print"):
                generate_release_files.main()
            self.assertEqual(helper.read_text(), "# Existing package-specific helper\n")
            self.assertEqual((target / ".github/workflows/release.yml").read_text(encoding="utf-8"),
                             c.render_release_template("release.yml", package))
            self.assertEqual(list(root.iterdir()), [target])
            with mock.patch.object(sys, "argv", arguments + ["--check"]), mock.patch("builtins.print"):
                generate_release_files.main()

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
