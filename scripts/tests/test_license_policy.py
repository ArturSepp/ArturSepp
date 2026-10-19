"""Controlled failures/restorations for the bounded, manually reviewed runtime."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conformance
import license_policy as policy


class LicensePolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.inspect = {
            "environment": {"sys_platform": "win32", "python_version": "3.12", "platform_machine": "AMD64"},
            "installed": [],
        }
        self.review = {
            "scope": "Synthetic exact-version contract fixture; not a distribution clearance",
            "qualifications": ["Retain the reviewed FTL alternative and GCC exception; no wholly permissive binary claim."],
            "packages": {}, "native_binaries": [],
        }
        for name, expression, terms, disposition in (
            ("factorlasso", "MIT", "MIT with retained attribution", "reviewed"),
            ("freetype-fixture", "FTL OR GPL-2.0-or-later", "FTL alternative selected with full notice", "reviewed"),
            ("runtime-fixture", "GPL-3.0-or-later WITH GCC-exception-3.1", "GCC runtime exception retained", "reviewed_with_compiler_exception"),
        ):
            metadata = {"name": name, "version": "1.0", "license_expression": expression, "license_file": ["LICENSE"]}
            self.inspect["installed"].append({"metadata": metadata})
            self.review["packages"][name] = {
                "version": "1.0", "reviewed_terms": terms, "disposition": disposition,
                "metadata_licence": policy.fingerprint(metadata),
                "notices": [self.file(name + "/LICENSE", (terms + "\ncomplete retained notice\n").encode())],
            }
        self.review["native_binaries"] = [self.file("runtime-fixture/runtime.dll", b"exact reviewed fixture bytes")]

    def file(self, relative, contents):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)
        return {"path": relative, "sha256": hashlib.sha256(contents).hexdigest()}

    def check(self, inspect=None, review=None):
        return policy.check_runtime(self.inspect if inspect is None else inspect,
                                    self.review if review is None else review, self.root)

    def reject_and_restore(self, change, reason, *, review=False):
        target = copy.deepcopy(self.review if review else self.inspect)
        change(target)
        with self.assertRaisesRegex(ValueError, reason):
            self.check(**{"review" if review else "inspect": target})
        self.assertEqual(self.check()["runtime_count"], 3)

    def test_reviewed_alternative_and_compiler_exception_are_not_substring_rejected(self):
        receipt = self.check()
        self.assertEqual(receipt["runtime_count"], 3)
        self.assertEqual(receipt["notice_count"], 3)
        self.assertEqual(receipt["native_binary_count"], 1)
        self.assertEqual(receipt["qualifications"], self.review["qualifications"])

    def test_ordinary_copyleft_fails_even_if_review_fingerprint_was_updated(self):
        for expression in ("GPL-3.0-or-later", "AGPL-3.0-only", "LGPL-2.1-or-later"):
            with self.subTest(expression=expression):
                changed = copy.deepcopy(self.inspect)
                changed["installed"][0]["metadata"]["license_expression"] = expression
                reviewed = copy.deepcopy(self.review)
                reviewed["packages"]["factorlasso"]["metadata_licence"] = policy.fingerprint(changed["installed"][0]["metadata"])
                with self.assertRaisesRegex(ValueError, "Ordinary copyleft"):
                    self.check(changed, reviewed)
                self.check()

    def test_legacy_plain_gpl_license_field_rejected(self):
        self.reject_and_restore(lambda item: item["installed"][0]["metadata"].update(license="GPLv2+"), "Ordinary copyleft")

    def test_unknown_permissive_package_rejected(self):
        self.reject_and_restore(lambda item: item["installed"].append({"metadata": {
            "name": "new-mit-package", "version": "1", "license_expression": "MIT"}}), "Unreviewed package")

    def test_unknown_version_rejected(self):
        self.reject_and_restore(lambda item: item["installed"][0]["metadata"].update(version="1.1"), "Unreviewed version")

    def test_unknown_metadata_rejected(self):
        self.reject_and_restore(lambda item: item["installed"][0]["metadata"].update(license_expression="MIT OR GPL-3.0-only"), "Unreviewed licence metadata")

    def test_unknown_review_disposition_rejected(self):
        self.reject_and_restore(lambda item: item["packages"]["factorlasso"].update(disposition="unknown"), "Unresolved licence", review=True)

    def test_missing_notices_or_terms_rejected(self):
        for field in ("notices", "reviewed_terms"):
            self.reject_and_restore(lambda item: item["packages"]["factorlasso"].update({field: []}), "Incomplete terms/notices", review=True)

    def test_changed_or_missing_full_notice_rejected_and_restored(self):
        target = self.root / "factorlasso/LICENSE"
        original = target.read_bytes()
        for replacement in (b"MIT\n", None):
            if replacement is None:
                target.unlink()
            else:
                target.write_bytes(replacement)
            with self.assertRaisesRegex(ValueError, "Changed/missing complete notice"):
                self.check()
            target.write_bytes(original)
            self.check()

    def test_changed_native_binary_rejected_and_restored(self):
        target = self.root / "runtime-fixture/runtime.dll"
        original = target.read_bytes()
        target.write_bytes(b"different backend build")
        with self.assertRaisesRegex(ValueError, "Changed/missing complete native binary"):
            self.check()
        target.write_bytes(original)
        self.check()

    def test_missing_and_duplicate_runtime_packages_rejected(self):
        self.reject_and_restore(lambda item: item["installed"].pop(), "Missing reviewed packages")
        self.reject_and_restore(lambda item: item["installed"].append(item["installed"][0]), "Duplicate runtime package")

    def test_unreviewed_platform_rejected(self):
        self.reject_and_restore(lambda item: item["environment"].update(sys_platform="linux"), "Unreviewed platform")

    def test_explicit_full_python_version_is_checked(self):
        review = copy.deepcopy(self.review)
        review["platform"] = dict(self.inspect["environment"], python_full_version="3.12.10")
        with self.assertRaisesRegex(ValueError, "Unreviewed platform: python_full_version"):
            self.check(review=review)
        self.check()

    def test_empty_scope_or_qualifications_rejected(self):
        for field in ("scope", "qualifications", "packages"):
            self.reject_and_restore(lambda item: item.update({field: {}}), "Incomplete reviewed", review=True)

    def test_only_seeded_pip_is_excluded(self):
        changed = copy.deepcopy(self.inspect)
        changed["installed"].append({"metadata": {"name": "pip", "version": "26"}})
        self.assertEqual(self.check(inspect=changed)["runtime_count"], 3)
        changed["installed"][-1]["metadata"]["name"] = "pytest"
        with self.assertRaisesRegex(ValueError, "Unreviewed package: pytest"):
            self.check(inspect=changed)
        self.check()

    def test_notice_path_cannot_escape_site_packages(self):
        self.reject_and_restore(lambda item: item["packages"]["factorlasso"]["notices"][0].update(path="../outside"), "Invalid notice evidence path", review=True)

    def test_standalone_cli_receipt_fails_then_restores(self):
        inspect_path = self.root / "inspect.json"
        review_path = self.root / "review.json"
        output = self.root / "receipt.json"
        review_path.write_text(json.dumps(self.review), encoding="utf-8")
        argv = ["license_policy.py", "--inspect", str(inspect_path), "--review", str(review_path), "--site", str(self.root), "--output", str(output)]
        for name, expected_exit in (("unknown", 1), ("factorlasso", 0)):
            changed = copy.deepcopy(self.inspect)
            changed["installed"][0]["metadata"]["name"] = name
            inspect_path.write_text(json.dumps(changed), encoding="utf-8")
            with mock.patch.object(sys, "argv", argv), mock.patch("builtins.print"):
                self.assertEqual(policy.main(), expected_exit)
            receipt = json.loads(output.read_text(encoding="utf-8"))
            if expected_exit == 0:
                self.assertEqual(receipt["inspect_sha256"], hashlib.sha256(inspect_path.read_bytes()).hexdigest())
            else:
                self.assertEqual(receipt["status"], "failed")

    def test_conformance_keeps_policy_failure_independent_of_drift_flag(self):
        args = ["conformance.py", "--repos-root", str(self.root), "--output", str(self.root),
                "--license-inspect", "inspect", "--license-review", "review", "--license-site", "site"]
        with mock.patch.object(sys, "argv", args), mock.patch.object(conformance, "load_registry", return_value={"packages": []}), \
             mock.patch("builtins.print"):
            with mock.patch.object(policy, "check_files", side_effect=ValueError("Ordinary copyleft licence: forbidden")):
                self.assertEqual(conformance.main(), 1)
            with mock.patch.object(policy, "check_files", return_value=self.check()):
                self.assertEqual(conformance.main(), 0)
        report = json.loads((self.root / "CONFORMANCE.json").read_text(encoding="utf-8"))
        self.assertEqual(report["runtime_license"]["receipt"]["qualifications"], self.review["qualifications"])

    def test_conformance_without_evidence_cannot_claim_runtime_pass(self):
        with mock.patch.object(sys, "argv", ["conformance.py", "--repos-root", str(self.root), "--output", str(self.root)]), \
             mock.patch.object(conformance, "load_registry", return_value={"packages": []}), mock.patch("builtins.print"):
            self.assertEqual(conformance.main(), 0)
        report = json.loads((self.root / "CONFORMANCE.json").read_text(encoding="utf-8"))
        self.assertEqual(report["runtime_license"]["state"], "unknown")


if __name__ == "__main__":
    unittest.main()
