"""Contracts for the local ignored dashboard; explicitly run with the collector present."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[1] / "oss_adoption_dashboard.py"
if SOURCE.exists():
    spec = importlib.util.spec_from_file_location("adoption_dashboard", SOURCE)
    dashboard = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = dashboard
    spec.loader.exec_module(dashboard)
else:
    dashboard = None


@unittest.skipIf(dashboard is None, "Local collector is ignored; run its explicit candidate tests")
class PaginationTests(unittest.TestCase):
    def test_page_cap_does_not_silently_report_partial_total(self):
        client = dashboard.GitHubClient(None)
        client.get = Mock(return_value=Mock(json=lambda: [{"id": i} for i in range(100)]))
        with self.assertRaisesRegex(ValueError, "Pagination"):
            client.pages("/fixture", max_pages=1)

    def test_multiple_pages(self):
        client = dashboard.GitHubClient(None)
        client.get = Mock(side_effect=[
            Mock(json=lambda: [{"id": i} for i in range(100)]),
            Mock(json=lambda: [{"id": 100}]),
        ])
        self.assertEqual(len(client.pages("/fixture")), 101)
        self.assertEqual(client.get.call_args.kwargs["page"], 2)


@unittest.skipIf(dashboard is None, "Local collector is ignored; run its explicit candidate tests")
class ComparisonTests(unittest.TestCase):
    # Stored provider-shaped fixtures: deliberately include mirror rows and boundary days.
    DAILY = {"data": [
        {"date": "2026-04-14", "category": "without_mirrors", "downloads": 99},
        {"date": "2026-04-15", "category": "without_mirrors", "downloads": 3},
        {"date": "2026-04-16", "category": "with_mirrors", "downloads": 100},
        {"date": "2026-04-17", "category": "without_mirrors", "downloads": 7},
        {"date": "2026-04-18", "category": "without_mirrors", "downloads": 88},
    ]}

    def test_calendar_window_and_leap_day(self):
        from datetime import date
        self.assertEqual(dashboard.six_month_start(date(2026, 10, 15)), date(2026, 4, 15))
        self.assertEqual(dashboard.six_month_start(date(2024, 8, 31)), date(2024, 2, 29))
        self.assertEqual(dashboard.six_month_start(date(2025, 8, 31)), date(2025, 2, 28))

    def test_exclusive_end_missing_day_and_mirror_filter(self):
        from datetime import date
        result = dashboard.daily_downloads(self.DAILY, date(2026, 4, 15), date(2026, 4, 18))
        self.assertEqual(result["recorded_downloads"], 10)
        self.assertEqual(result["missing_days"], ["2026-04-16"])
        self.assertEqual(result["monthly"][0]["observed_days"], 2)
        self.assertFalse(result["monthly"][0]["complete"])

    def test_month_boundary(self):
        from datetime import date
        payload = {"data": [
            {"date": "2026-04-30", "category": "without_mirrors", "downloads": 0},
            {"date": "2026-05-01", "category": "without_mirrors", "downloads": 9}]}
        result = dashboard.daily_downloads(payload, date(2026, 4, 30), date(2026, 5, 2))
        self.assertEqual([r["downloads"] for r in result["monthly"]], [0, 9])
        self.assertEqual(result["missing_days"], [])

    def test_missing_month_is_not_zero(self):
        from datetime import date
        result = dashboard.daily_downloads({"data": []}, date(2026, 4, 15), date(2026, 6, 15))
        self.assertIsNone(result["recorded_downloads"])
        self.assertTrue(all(r["downloads"] is None for r in result["monthly"]))

    def test_duplicate_or_invalid_count_fails(self):
        from datetime import date
        item = self.DAILY["data"][1]
        for payload in ({"data": [item, item]},
                        {"data": [dict(item, downloads=-1)]},
                        {"data": [dict(item, downloads=True)]}):
            with self.assertRaises(ValueError):
                dashboard.daily_downloads(payload, date(2026, 4, 15), date(2026, 4, 18))

    def test_provider_failure_preserves_old_time_and_labels_cache(self):
        fail = Mock(side_effect=RuntimeError("provider 503"))
        previous = {"value": 12, "observed_at": "2026-10-10T00:00:00+00:00"}
        result = dashboard.source_observation(fail, "fixture://provider", "events", previous)
        self.assertEqual(result["status"], "cached")
        self.assertEqual(result["observed_at"], previous["observed_at"])
        self.assertEqual(result["value"], 12)
        self.assertIn("503", result["error"])
        unavailable = dashboard.source_observation(fail, "fixture://provider", "events")
        self.assertEqual(unavailable["status"], "unavailable")
        self.assertIsNone(unavailable["value"])

    def test_cache_window_is_validated_and_offline_labels_all_sources(self):
        from datetime import date
        snapshot = dict(schema=1, view="comparison", start="2026-04-15", end_exclusive="2026-10-15",
                        packages=[{"project": p[2], "sources": {"fixture": {
                            "value": 0, "observed_at": "old", "status": "current"}}}
                            for p in dashboard.COMPARISON_PACKAGES])
        cached = dashboard.cached_comparison(snapshot, date(2026, 4, 15), date(2026, 10, 15))
        self.assertEqual(cached["packages"][0]["sources"]["fixture"]["status"], "cached")
        self.assertEqual(snapshot["packages"][0]["sources"]["fixture"]["status"], "current")
        with self.assertRaisesRegex(ValueError, "Cache"):
            dashboard.cached_comparison(snapshot, date(2026, 4, 14), date(2026, 10, 14))

    def test_contribution_exclusions_and_exclusive_end(self):
        from datetime import date
        def row(login, day, kind="User"):
            return {"user": {"login": login, "type": kind}, "created_at": day + "T12:00:00Z"}
        rows = [row("maintainer", "2026-05-01"), row("helper[bot]", "2026-05-01"),
                row("bot", "2026-05-01", "Bot"), row("external", "2026-05-01"),
                row("external", "2026-04-14"), row("later", "2026-10-15")]
        counts = dashboard.activity_counts(rows, date(2026, 4, 15), date(2026, 10, 15), {"maintainer"})
        self.assertEqual(counts["all_time_prs"], 2)
        self.assertEqual(counts["six_month_prs"], 1)
        self.assertEqual(counts["all_time_authors"], 1)

    def test_wheel_presence_is_definition_not_string_match(self):
        import io
        import zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("optimalportfolios/demo.py",
                             'def gls_split(): pass\n# class EwmaCovarEstimator: pass\n')
        evidence = dashboard.wheel_capabilities(buffer.getvalue(), "optimalportfolios")
        self.assertTrue(evidence["MATF GLS alpha split"]["available_in_wheel"])
        self.assertFalse(evidence["EWMA covariance estimator"]["available_in_wheel"])
        self.assertIn("pending Q1", evidence["MATF GLS alpha split"]["verification"])

    def test_export_reconciles_and_dashboard_uses_same_values(self):
        import csv
        import json
        import tempfile
        from datetime import date
        from pathlib import Path
        value = dashboard.daily_downloads(self.DAILY, date(2026, 4, 15), date(2026, 4, 18))
        snapshot = dict(start="2026-04-15", end_exclusive="2026-04-18", generated_at="fixture",
                        packages=[{"project": "qis", "sources": {"downloads": {
                            "value": value, "status": "cached", "observed_at": "old",
                            "url": "fixture://daily", "definition": "fixture", "error": None}}}])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dashboard.export_comparison(snapshot, root / "export")
            with (root / "export/daily.csv").open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(sum(int(row["downloads"]) for row in rows), 10)
            self.assertEqual(json.loads((root / "export/snapshot.json").read_text())["packages"][0]
                             ["sources"]["downloads"]["value"]["recorded_downloads"], 10)
            dashboard.render_comparison(snapshot, root / "dashboard.html", False)
            document = (root / "dashboard.html").read_text(encoding="utf-8")
            self.assertIn("<td>10</td>", document)
            self.assertIn("cached", document)
            self.assertIn("2026-04-16", document)
            with self.assertRaises(FileExistsError):
                dashboard.export_comparison(snapshot, root / "export")


if __name__ == "__main__":
    unittest.main()
