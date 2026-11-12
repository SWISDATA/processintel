import unittest
import xml.etree.ElementTree as ET

import pandas as pd

from app.converters.csv_to_xes_converter import CsvToXesConverter


class TestMissingValues(unittest.TestCase):

    def setUp(self):
        # Two correct events from an online shop
        self.df = pd.DataFrame(
            {
                "case": ["ORD-1001", "ORD-1002"],
                "event": ["Order placed", "Order packed"],
                "time": ["2026-10-21 09:00", "2026-10-21 10:00"],
            }
        )

    def convert(self, df):
        return CsvToXesConverter().convert(df, "case", "event", "time")

    def test_valid_csv(self):
        tree, summary, removed = self.convert(self.df.copy())
        self.assertEqual(removed, 0)
        self.assertEqual(summary["Events"], 2)
        self.assertEqual(summary["Cases"], 2)

    def test_missing_case(self):
        df = self.df.copy()
        df.loc[1, "case"] = None

        tree, summary, removed = self.convert(df)

        self.assertEqual(removed, 1)
        self.assertEqual(summary["Events"], 1)
        self.assertEqual(summary["Cases"], 1)
        self.assertNotIn('value="nan"', ET.tostring(tree.getroot(), encoding="unicode"))

    def test_missing_activity(self):
        df = self.df.copy()
        df.loc[1, "event"] = None

        tree, summary, removed = self.convert(df)

        self.assertEqual(removed, 1)
        self.assertEqual(summary["Events"], 1)
        self.assertEqual(summary["Activities"], 1)
        self.assertNotIn('value="nan"', ET.tostring(tree.getroot(), encoding="unicode"))

    def test_missing_timestamp(self):
        df = self.df.copy()
        df.loc[1, "time"] = None

        _, summary, removed = self.convert(df)

        self.assertEqual(removed, 1)
        self.assertEqual(summary["Events"], 1)

    def test_three_missing_fields(self):
        df = pd.DataFrame(
            {
                "case": ["ORD-1001", None, "ORD-1001", "ORD-1001"],
                "event": ["Order placed", "Order packed", None, "Order shipped"],
                "time": [
                    "2026-10-21 09:00",
                    "2026-10-21 10:00",
                    "2026-10-21 11:00",
                    None,
                ],
            }
        )

        _, summary, removed = self.convert(df)

        self.assertEqual(removed, 3)
        self.assertEqual(summary["Events"], 1)

    def test_all_missing(self):
        for column in ("case", "event"):
            with self.subTest(column=column):
                df = self.df.copy()
                df[column] = None

                with self.assertRaisesRegex(ValueError, "No valid data remaining"):
                    self.convert(df)


if __name__ == "__main__":
    unittest.main()
