"""Reference validation rejects real defects without mistaking outages for edits."""

import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

SPEC = importlib.util.spec_from_file_location(
    "references", Path(__file__).resolve().parents[1] / "repo_governance/check_new_references.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class Response(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {"Content-Type": "text/html"}


class ReferenceTests(unittest.TestCase):
    def test_only_added_lines_and_balanced_parentheses(self):
        patch_text = (
            "--- a/page.md\n+++ b/page.md\n-https://old.example/\n"
            "+[new](https://example.org/A_(B))\n+https://example.org/next.\n"
        )
        self.assertEqual(
            module.added_urls(patch_text), ["https://example.org/A_(B)", "https://example.org/next"]
        )

    def test_authorship_emphasis_and_rst_wrappers(self):
        patch_text = (
            "+*[Artur Sepp](https://github.com/ArturSepp)*\n"
            "+**[guide](https://example.org/guide)**\n"
            "+`https://example.org/code` and `RST <https://example.org/rst>`_\n"
        )
        self.assertEqual(
            module.added_urls(patch_text),
            [
                "https://example.org/code",
                "https://example.org/guide",
                "https://example.org/rst",
                "https://github.com/ArturSepp",
            ],
        )

    def test_repeated_not_found_blocks(self):
        error = HTTPError("https://example.org", 404, "missing", {}, None)
        with patch.object(module, "urlopen", side_effect=error), patch.object(module.time, "sleep"):
            self.assertEqual(module.inspect_url("https://example.org")["status"], "broken")

    def test_rate_limit_is_deferred(self):
        error = HTTPError("https://example.org", 429, "limited", {}, None)
        with patch.object(module, "urlopen", side_effect=error):
            self.assertEqual(module.inspect_url("https://example.org")["status"], "deferred")

    def test_static_anchor_contract(self):
        with patch.object(
            module, "urlopen", return_value=Response(b'<h2 id="user-content-method">')
        ):
            self.assertEqual(
                module.inspect_url("https://example.org#user-content-method")["status"], "ok"
            )
        with (
            patch.object(module, "urlopen", side_effect=lambda *a, **k: Response(b"<html></html>")),
            patch.object(module.time, "sleep"),
        ):
            self.assertEqual(module.inspect_url("https://example.org#missing")["status"], "broken")

    def test_a_successful_retry_is_not_reported_as_broken(self):
        error = HTTPError("https://example.org", 404, "missing", {}, None)
        with (
            patch.object(module, "urlopen", side_effect=[error, Response(b"ok")]),
            patch.object(module.time, "sleep"),
        ):
            self.assertEqual(module.inspect_url("https://example.org")["status"], "ok")
