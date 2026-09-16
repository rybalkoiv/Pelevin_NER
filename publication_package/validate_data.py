#!/usr/bin/env python3
"""Consistency tests for pelevin_named_entities.csv (standard library only)."""

import csv
import unittest
from pathlib import Path


DATA = Path(__file__).with_name("pelevin_named_entities.csv")
EXPECTED_COLUMNS = [
    "work_title", "work_year", "entity", "mention_count", "activities",
    "birth_year", "death_year", "country_or_polity", "exclude_as_character",
]


class DataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with DATA.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            cls.columns = reader.fieldnames
            cls.rows = list(reader)

    def test_columns(self):
        self.assertEqual(self.columns, EXPECTED_COLUMNS)

    def test_expected_size(self):
        self.assertEqual(len(self.rows), 1456)
        self.assertEqual(len({r["entity"] for r in self.rows}), 745)
        self.assertEqual(len({r["work_title"] for r in self.rows}), 22)
        self.assertEqual(sum(int(r["mention_count"]) for r in self.rows), 5673)

    def test_primary_key(self):
        keys = [(r["work_title"], r["entity"]) for r in self.rows]
        self.assertEqual(len(keys), len(set(keys)))

    def test_required_values(self):
        for row in self.rows:
            self.assertTrue(row["work_title"])
            self.assertTrue(row["work_year"])
            self.assertTrue(row["entity"])
            self.assertGreater(int(row["mention_count"]), 0)
            self.assertIn(row["exclude_as_character"], {"true", "false"})

    def test_years(self):
        for row in self.rows:
            self.assertGreaterEqual(int(row["work_year"]), 1993)
            self.assertLessEqual(int(row["work_year"]), 2026)
            for field in ("birth_year", "death_year"):
                if row[field]:
                    self.assertGreaterEqual(int(row[field]), -5000)
                    self.assertLessEqual(int(row[field]), 2026)

    def test_normalized_activities(self):
        forbidden = {"ученый", "режжисёр", "де-ятель", "деятель, политик"}
        for row in self.rows:
            values = row["activities"].split("|")
            self.assertFalse(forbidden.intersection(values))
            self.assertEqual(len(values), len(set(values)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
