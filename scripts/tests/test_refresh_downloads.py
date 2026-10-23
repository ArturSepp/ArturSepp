"""Download-source validation and preservation of the last good snapshot."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import refresh_downloads as downloads


class DownloadTests(unittest.TestCase):
    def test_visible_summary_handles_markup_and_ignores_script_copies(self):
        summary = "qis has been downloaded <b>231,050</b> times in total on PyPI, including 19,232 in the last 30 days"
        html = f"<script>{summary}</script><p>{summary}</p>"
        self.assertEqual(downloads.parse_counts(html, "qis"), {"month": 19232, "total": 231050})

    def test_missing_ambiguous_wrong_package_and_invalid_totals_are_rejected(self):
        summary = "qis has been downloaded 20 times in total on PyPI, including 10 in the last 30 days"
        for html in ("Service unavailable", f"<p>{summary}</p><p>{summary}</p>", summary.replace("qis", "other"),
                     summary.replace("including 10", "including 30")):
            with self.subTest(html=html), self.assertRaises(ValueError):
                downloads.parse_counts(html, "qis")

    def test_failed_source_preserves_every_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "counts.json").write_text("previous successful data")
            with mock.patch.object(downloads, "fetch_counts", side_effect=ValueError("source changed")):
                with self.assertRaises(ValueError):
                    downloads.refresh(root)
            self.assertEqual(list(root.iterdir()), [root / "counts.json"])
            self.assertEqual((root / "counts.json").read_text(), "previous successful data")

    def test_snapshot_preserves_exact_counts_and_badge_shows_thousands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(downloads, "REPOS", {"Example": "qis"}), \
                 mock.patch.object(downloads, "fetch_counts", return_value={
                     "source": "https://pepy.tech/projects/qis", "month": 19232, "total": 231050}):
                snapshot = downloads.refresh(root)
            self.assertEqual(json.loads((root / "counts.json").read_text()), snapshot)
            svg = ET.parse(root / "qis-total-blue.svg").getroot()
            self.assertEqual(svg.find("{http://www.w3.org/2000/svg}text").text, "231K")
            self.assertIn("231,050", svg.get("aria-label"))
            self.assertIn("UTC", svg.get("aria-label"))
            self.assertFalse((root / "qis-month.svg").exists())
            self.assertTrue((root / "updated.svg").exists())


if __name__ == "__main__":
    unittest.main()
