---
author: "Rybalko, Ivan; Titov, Alexey"
title: "Named Entities in Victor Pelevin's Prose: Persons, Mention Frequencies, and Biographical Metadata"
abstract: "The dataset contains the results of extracting and verifying mentions of real-world persons and mythological figures in 22 major works by Victor Pelevin published between 1993 and 2026. Each of the 1,456 records represents a work–entity pair and includes mention frequency, activities, life dates, country or historical polity, and a manually assigned character-exclusion flag. The dataset contains 745 unique entities and 5,673 mentions."
---

# General description

The dataset represents the results of a quantitative study of named entities in 22 major works of prose by Victor Pelevin published between 1993 and 2026. Its purpose is to support research into the way real-world persons mentioned in literary texts reflect cultural imaginaries and changes in the post-Soviet social context.

The unit of observation is a **work–entity pair**. Each row records how often an entity was detected in one work and provides available biographical metadata. The publication table contains:

- 1,456 records;
- 745 unique entities;
- 22 literary works;
- 5,673 mentions.

Full texts of Pelevin's works are not included for copyright reasons.

# Data collection and processing

The source material consisted of electronic texts of Pelevin's works. The preparation pipeline included:

1. Text cleaning: removal of outer line quotation marks, normalization of dashes and quotation marks, and whitespace normalization.
2. Independent extraction of `PER` entities with Natasha/SlovNet and spaCy (`ru_core_news_lg`) followed by lemmatization.
3. Merging of model outputs. If an entity was found by both models, the maximum of the two mention counts was retained to avoid double-counting.
4. Search in Russian Wikipedia, resolution to a canonical article title, and rejection of disambiguation pages and records without biographical markers.
5. Extraction of activities and life dates from the lead section of the Wikipedia article; geographic or historical-polity information was added from the available biographical metadata.
6. Manual review. Thirty-three work–entity pairs in which a name functions as a fictionalized literary character were explicitly flagged. They remain in the dataset for transparency but may be excluded from analyses with `exclude_as_character=true`.
7. Publication normalization: integer formatting, readable work titles, normalized activity labels, and negative integer representation of BCE years.

# Dataset format

The main file is `pelevin_named_entities.csv`, encoded in UTF-8 and using a comma delimiter. It has nine columns:

- `work_title` — normalized title of the literary work.
- `work_year` — year of first publication.
- `entity` — canonical entity name, usually the title of the corresponding Russian Wikipedia article.
- `mention_count` — number of mentions in this work produced by the merged NER pipeline.
- `activities` — zero or more activities separated by `|`.
- `birth_year` — year of birth; blank when unavailable; BCE years are negative.
- `death_year` — year of death; blank when unavailable or not extracted; BCE years are negative.
- `country_or_polity` — country, place, or historical polity; blank when unavailable.
- `exclude_as_character` — `true` for manually flagged fictionalized uses, otherwise `false`.

## Example record

```csv
work_title,work_year,entity,mention_count,activities,birth_year,death_year,country_or_polity,exclude_as_character
Generation «П»,1999,Оруэлл Джордж,1,писатель|публицист,1903,1950,Великобритания,false
```

# Files

- `pelevin_named_entities.csv` — publication-ready dataset.
- `PelevinDataset.py` — dependency-free helper class for loading and querying the dataset.
- `Dataset_Usage.ipynb` — usage examples.
- `Testing.ipynb` — statistics and consistency-check examples.
- `validate_data.py` — automated consistency tests.
- `prepare_dataset.py` — reproducible conversion of the original CSV to the publication format.
- `README.md` / `Readme_en.md` — Russian and English documentation.
- `requirements.txt` — pinned dependencies for the example notebooks.
- `source/pelevin_ner.py` — original NER and Wikipedia-enrichment pipeline.
- `source/analize.ipynb` — sanitized research notebook with stored outputs and local paths removed.
- `source/result_original.csv` — unmodified source table from GitHub.
- `source/requirements_pipeline.txt` — direct dependencies of the original pipeline and analysis, pinned to versions from the authors' preserved working environment.
- `CHANGELOG.md` — publication-version history.

# Usage

## Dependencies

```text
python >= 3.10
pandas==2.2.3
matplotlib==3.10.1
```

Install the example dependencies with:

```shell
pip install -Ur requirements.txt
```

The helper class itself uses only the Python standard library:

```python
from PelevinDataset import PelevinDataset

dataset = PelevinDataset("pelevin_named_entities.csv")
dataset.summary()
dataset.get_sample_by_id(10)
dataset.get_entities_by_work("Generation «П»", include_characters=False)
dataset.get_occurrences_by_entity("Оруэлл, Джордж")
dataset.get_entities_by_activity("писатель")
```

# Validation

Run the automated tests from the dataset directory:

```shell
python3 validate_data.py
```

The tests verify the schema, record/entity/work/mention totals, uniqueness of the `work_title + entity` key, numeric ranges, Boolean values, and normalized activity labels.

# Statistics and missing values

| Measure | Value |
|---|---:|
| Records | 1,456 |
| Unique entities | 745 |
| Works | 22 |
| Total mentions | 5,673 |
| Rows flagged as fictionalized characters | 33 |
| Rows without extracted activities | 2 |
| Rows without country or historical polity | 220 |

# Limitations

- The corpus covers 22 major works rather than Pelevin's complete oeuvre, and work lengths differ.
- Automatic NER and Wikipedia linking may contain omissions or incorrect resolutions despite manual review.
- Mention frequency is the maximum of two model counts, not a manually annotated gold-standard count.
- A blank `death_year` may mean that a person was alive or that the year was not extracted.
- `country_or_polity` mixes modern countries, historical states, and places and should not be treated as a normalized modern-country field.
- Direct dependency versions were recovered from the authors' preserved environment; compatibility with Python versions other than the notebook's Python 3.12.3 has not been independently verified.
- The full source texts and the intermediate Wikipedia cache are not distributed, limiting exact end-to-end reproduction.
- The public code does not preserve a standalone step that runs NER for all 22 works, adds country metadata, and combines per-work results into `result_original.csv`.
- Analyses normalized by work length require a private local `texts/` directory and cannot be reproduced from the public package alone.
- Biographical years and activity labels require a final content review: repeated entities contain contradictory values, including BCE sign problems and several clearly incorrect life dates.

# Related publication

Rybalko, I. A.; Titov, A. S. “Named Entities in Victor Pelevin's Prose in a Sociological Context.” Manuscript prepared for *Quantitative Philology*. The final bibliographic reference and DOI should be added after publication.

# License and citation

CC BY 4.0 is the recommended license, subject to confirmation by both authors. After publication, users should cite the automatically generated Dataverse citation including the DOI and dataset version.
