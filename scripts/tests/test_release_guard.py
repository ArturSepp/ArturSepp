"""Exercise publishing refusal states and actual wheel/sdist metadata inspection."""
import io
import json
import sys
import tarfile
import tempfile
import unittest
import urllib.error
import zipfile
import subprocess
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "templates"))
import release_guard as guard


class ReleaseIdentityTests(unittest.TestCase):
    def test_ref_fragments_and_shell_text_rejected(self):
        for tag in ("main", "refs/tags/v1.2.3", "v1.2", "v1.2.3\n", "v1.2.3;echo bad", "v1.2.3/other"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                guard.version_from_tag(tag)
        self.assertEqual(guard.version_from_tag("v1.2.3rc1"), "1.2.3rc1")
        self.assertEqual(guard.version_from_tag("v1.2.3.dev12"), "1.2.3.dev12")
        self.assertEqual(guard.version_from_tag("v1.2.3rc1.dev2"), "1.2.3rc1.dev2")

    def test_stale_cff_and_absent_changelog_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text('[project]\nname="sample"\nversion="1.2.3"\n')
            (root / "CITATION.cff").write_text('version: "1.2.2"\ndate-released: 2026-08-01\n')
            (root / "CHANGELOG.md").write_text("## [1.2.3] - 2026-08-01\n")
            with self.assertRaisesRegex(ValueError, "CITATION"):
                guard.validate_metadata(root, "v1.2.3")

    def test_tag_outside_main_or_moved_after_push_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
            git("init", "-q")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            (root / "pyproject.toml").write_text('[project]\nname="sample"\nversion="1.2.3"\n')
            (root / "CITATION.cff").write_text('version: "1.2.3"\ndate-released: 2026-08-01\n')
            (root / "CHANGELOG.md").write_text("## [1.2.3] - 2026-08-01\n")
            git("add", ".")
            git("commit", "-qm", "initial")
            main_sha = git("rev-parse", "HEAD")
            git("update-ref", "refs/remotes/origin/main", main_sha)
            git("commit", "--allow-empty", "-qm", "unmerged")
            git("tag", "v1.2.3")
            with self.assertRaises(subprocess.CalledProcessError):
                guard.checkout_tag(root, "v1.2.3")
            with self.assertRaisesRegex(ValueError, "moved"):
                guard.checkout_tag(root, "v1.2.3", main_sha)
            (root / "CITATION.cff").write_text('version: "1.2.3"\ndate-released: 2026-08-01\n')
            self.assertEqual(guard.validate_metadata(root, "v1.2.3")["version"], "1.2.3")
            (root / "CHANGELOG.md").write_text("## [Unreleased]\n")
            with self.assertRaisesRegex(ValueError, "CHANGELOG"):
                guard.validate_metadata(root, "v1.2.3")


class DigestTests(unittest.TestCase):
    def test_new_matching_partial_and_conflicting_releases(self):
        hashes = {"sample.whl": "abc", "sample.tar.gz": "def"}
        existing = [{"filename": "sample.whl", "digests": {"sha256": "abc"}}]
        self.assertEqual(guard.pending_uploads(hashes, None), sorted(hashes))
        with self.assertRaisesRegex(ValueError, "retry_existing"):
            guard.pending_uploads(hashes, existing)
        self.assertEqual(guard.pending_uploads(hashes, existing, True), ["sample.tar.gz"])
        existing.append({"filename": "sample.tar.gz", "digests": {"sha256": "def"}})
        self.assertEqual(guard.pending_uploads(hashes, existing), [])
        existing[0]["digests"]["sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "differs"):
            guard.pending_uploads(hashes, existing, True)

    def test_only_confirmed_404_means_unpublished(self):
        with mock.patch.object(guard.urllib.request, "urlopen", side_effect=urllib.error.HTTPError("url", 404, "missing", {}, None)):
            self.assertIsNone(guard.pypi_files("sample", "1.2.3"))
        with mock.patch.object(guard.urllib.request, "urlopen", side_effect=urllib.error.HTTPError("url", 503, "unavailable", {}, None)):
            with self.assertRaises(urllib.error.HTTPError):
                guard.pypi_files("sample", "1.2.3")

    def test_actual_archives_reject_wrong_version(self):
        project = {"name": "sample", "version": "1.2.3", "description": "An example", "urls": {"Documentation": "https://example.invalid"}, "license": "MIT", "requires-python": ">=3.10", "dependencies": ["numpy>=2,<3"]}
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            def write_archives(version, license_present=True):
                metadata = f"Metadata-Version: 2.4\nName: sample\nVersion: {version}\nSummary: An example\nProject-URL: Documentation, https://example.invalid\nLicense-Expression: MIT\nLicense-File: LICENSE\nRequires-Python: >=3.10\nRequires-Dist: numpy<3,>=2\n\n"
                with zipfile.ZipFile(dist / "sample-1.2.3-py3-none-any.whl", "w") as wheel:
                    wheel.writestr("sample/__init__.py", "")
                    wheel.writestr("sample-1.2.3.dist-info/METADATA", metadata)
                    if license_present:
                        wheel.writestr("sample-1.2.3.dist-info/licenses/LICENSE", "MIT fixture")
                with tarfile.open(dist / "sample-1.2.3.tar.gz", "w:gz") as archive:
                    data = metadata.encode()
                    info = tarfile.TarInfo("sample-1.2.3/PKG-INFO")
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
                    license_info = tarfile.TarInfo("sample-1.2.3/LICENSE")
                    license_info.size = 11
                    archive.addfile(license_info, io.BytesIO(b"MIT fixture"))
                    archive.addfile(tarfile.TarInfo("sample-1.2.3/src/sample/__init__.py"), io.BytesIO(b""))
            write_archives("1.2.3")
            self.assertEqual(len(guard.inspect_artifacts(dist, project, "sample")), 2)
            with zipfile.ZipFile(dist / "sample-1.2.3-py3-none-any.whl", "a") as wheel:
                wheel.writestr("sample/run_local/export_data.py", "raise RuntimeError('maintainer only')")
            with self.assertRaisesRegex(ValueError, "development runner"):
                guard.inspect_artifacts(dist, project, "sample")
            write_archives("1.2.3", license_present=False)
            with self.assertRaisesRegex(ValueError, "license file"):
                guard.inspect_artifacts(dist, project, "sample")
            write_archives("1.2.2")
            with self.assertRaisesRegex(ValueError, "identity"):
                guard.inspect_artifacts(dist, project, "sample")


if __name__ == "__main__":
    unittest.main()
