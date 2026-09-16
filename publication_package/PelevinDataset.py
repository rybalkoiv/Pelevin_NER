"""Utilities for loading and exploring the Pelevin named-entity dataset."""

import csv
from collections import Counter, defaultdict
from pathlib import Path


class PelevinDataset:
    """Small dependency-free interface modelled after the reference dataset."""

    def __init__(self, dataset_path="pelevin_named_entities.csv"):
        self.dataset_path = Path(dataset_path)
        self.data = []
        self.columns = []
        self.load_dataset(self.dataset_path)

    def load_dataset(self, dataset_path):
        self.dataset_path = Path(dataset_path)
        with self.dataset_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            self.columns = reader.fieldnames or []
            self.data = list(reader)
        return self

    @property
    def number_of_samples(self):
        return len(self.data)

    @property
    def works(self):
        return sorted({row["work_title"] for row in self.data})

    @property
    def entities(self):
        return sorted({row["entity"] for row in self.data})

    @property
    def total_mentions(self):
        return sum(int(row["mention_count"]) for row in self.data)

    def get_sample_by_id(self, sample_id):
        return self.data[int(sample_id)]

    def get_entities_by_work(self, work_title, include_characters=True):
        rows = [row for row in self.data if row["work_title"] == work_title]
        if not include_characters:
            rows = [row for row in rows if row["exclude_as_character"] == "false"]
        return rows

    def get_occurrences_by_entity(self, entity):
        return [row for row in self.data if row["entity"] == entity]

    def get_entities_by_activity(self, activity):
        return [
            row for row in self.data
            if activity in row["activities"].split("|")
        ]

    def activity_counts(self, unique_entities=False):
        values = defaultdict(set) if unique_entities else Counter()
        for row in self.data:
            for activity in filter(None, row["activities"].split("|")):
                if unique_entities:
                    values[activity].add(row["entity"])
                else:
                    values[activity] += 1
        if unique_entities:
            return Counter({key: len(items) for key, items in values.items()})
        return values

    def summary(self):
        return {
            "records": self.number_of_samples,
            "unique_entities": len(self.entities),
            "works": len(self.works),
            "total_mentions": self.total_mentions,
            "character_rows": sum(
                row["exclude_as_character"] == "true" for row in self.data
            ),
            "missing_activities": sum(not row["activities"] for row in self.data),
            "missing_country_or_polity": sum(
                not row["country_or_polity"] for row in self.data
            ),
        }
