"""Regression tests for QueueCraft CSV/XLSX ingestion and data-quality reporting."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_import import DataImportError, ImportOptions, import_arrival_data


class DataImportTests(unittest.TestCase):
    def test_csv_aggregated_data_reports_invalid_rows(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "arrivals.csv"
            pd.DataFrame(
                {
                    "timestamp": ["2026-01-01 08:00", "not-a-date", "2026-01-01 09:00", "2026-01-01 10:00"],
                    "arrivals": [10, 2, -1, "not-a-number"],
                }
            ).to_csv(source, index=False)
            imported = import_arrival_data(source)

            self.assertEqual(imported.historical_counts, [10.0])
            self.assertEqual(imported.quality.input_rows, 4)
            self.assertEqual(imported.quality.accepted_rows, 1)
            self.assertEqual(imported.quality.excluded_invalid_timestamp, 1)
            self.assertEqual(imported.quality.excluded_negative_count, 1)
            self.assertEqual(imported.quality.excluded_invalid_count, 1)
            self.assertEqual(imported.quality.quality_score_pct, 25.0)

    def test_xlsx_event_data_is_aggregated_and_missing_bucket_is_filled(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "events.xlsx"
            pd.DataFrame(
                {
                    "arrival_time": ["2026-01-01 08:10", "2026-01-01 08:40", "2026-01-01 10:15"],
                    "customer_id": ["a", "b", "c"],
                }
            ).to_excel(source, index=False)
            imported = import_arrival_data(source, ImportOptions(frequency="h"))

            self.assertEqual(imported.historical_counts, [2.0, 0.0, 1.0])
            self.assertTrue(imported.quality.generated_event_counts)
            self.assertEqual(imported.quality.missing_buckets_filled, 1)
            self.assertEqual(imported.quality.accepted_rows, 3)

    def test_missing_timestamp_column_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "invalid.csv"
            pd.DataFrame({"arrivals": [1, 2, 3]}).to_csv(source, index=False)
            with self.assertRaises(DataImportError):
                import_arrival_data(source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
