---
author: "Kassab, Kenan; Teslya, Nikolai; Vozhik, Ekaterina"
title: "Named entities in the Pushkin Encyclopedia"
abstract: "The dataset contains text markup from the Pushkin Encyclopedia (Pushkin Encyclopedia: Works. Vol. 1, A–D. — St. Petersburg: Nestor-Istoriya, 2009. — 520 p., ill.) to solve the named entity retrieval (NER) problem. The dataset is based on five entity types: work (WORK-OF-ART), person (PER), date (DATE), organization (ORG), and location (LOC). The BRAT service was used to create the dataset. The results of training the BERT model on the resulting dataset showed an average accuracy of named entity detection and classification of approximately 94%."
---

Dataset citation format:

> *Kassab, Kenan; Teslya, Nikolai; Vozhik, Ekaterina* Named
> entities in the Pushkin Encyclopedia // Open Data Repository on
> Russian Literature and Folklore. 2026. V1. DOI:
> [https://doi.org/10.31860/openlit-2024.7-A001](https://doi.org/10.31860/openlit-2024.7-A001).


# General description of the data

The dataset consists of annotated texts from the first volume of the encyclopedia devoted to the works of A. S. Pushkin  
(*Pushkin Encyclopedia: Works. Issue 1. A–D. St. Petersburg: Nestor-History, 2009. 520 pages, illustrated*).  
The total number of processed articles is **228**.

The source texts were split into paragraphs and then automatically annotated using the **DeepPavlov** library to extract the following entity types:

- **PER** (*Person*) — people such as historical figures, writers, critics, and commentators.
- **DATE** (*Date*) — all temporal entities that define the chronological structure of the text, such as periods and specific dates.
- **LOC** (*Location*) — regions and places mentioned in the text, such as cities, countries, names of rivers, seas, and other geographical entities.
- **ORG** (*Organization*) — associations and communities mentioned in the text, such as companies and institutions, names of journals and organizations  
  (lyceums, schools, societies, publishing houses, etc.).
- **WORK-OF-ART** (*Work of Art*) — works related to the text, such as books and literary works.

If an entity is nested within another entity type, **only the top-level entity is annotated**.  
For example, if a person (`PER`) is mentioned inside a `WORK-OF-ART` entity, it is not annotated separately.



## Example of Text Annotation for the NER Task

Let us consider a clear example from an encyclopedic article.

### Source Text Fragment

> “**Alfons Saddles His Horse…**” — a poetic fragment based on an episode from a novel by Jan Potocki…

### Semantic Analysis

In this fragment, the word **“Alfons”** can be interpreted in two ways:

1. as the name of a character (a potential `PER` entity);
2. as part of the title of a literary work  
   **“Alfons Saddles His Horse…”** (a `WORK-OF-ART` entity).

From the perspective of NER annotation, the following rule must be taken into account.

### Nested Entity Rule

Within the applied annotation scheme (BIO / CoNLL):

- **one entity cannot contain another entity**;
- nested entities are **not annotated**;
- if a text fragment contains two entities and one is fully included in the other,  
  only the **entity with the larger span** is annotated.

### Applying the Rule to the Example

In the title:

```text
“Alfons Saddles His Horse…”
```

the entire sequence of tokens forms **a single entity**:

- type: `WORK-OF-ART`;
- span: from the opening quotation mark to the closing one.

The separate annotation of the word **“Alfons”** as `PER` is **not performed**, because:
- it is part of a longer entity;
- nested entity annotation is not supported in this corpus.

### Final Annotation (BIO)

```text
“           B-WORK-OF-ART
Alfons      I-WORK-OF-ART
Saddles     I-WORK-OF-ART
His         I-WORK-OF-ART
Horse       I-WORK-OF-ART
...         I-WORK-OF-ART
”           I-WORK-OF-ART
```

After annotation, the dataset was reviewed and verified to correct errors and ensure that all entities correspond to their tags and positions in the text.

---

# Dataset description

The dataset is provided in the file `entities.json` and contains **1,567** objects in JSON format.  
Each object has the following structure, adapted for training BERT-based models using the **spaCy** framework:

- **text** (*str*) — contains the text to which annotation is applied.
- **entities** (*list of lists*) — includes entities found in the text, with their corresponding positions and types.
- **tokens** (*list*) — contains tokens extracted from the text.
- **BIO-Tags** (*list*) — contains BIO tags for the tokens used in annotation.

Entities are represented as lists of three values in the following order:

```text
[start_span, end_span, entity_type]
```

where:
- `start_span` — index of the beginning of the text fragment relative to the start of the text;
- `end_span` — index of the end of the text fragment;
- `entity_type` — type of the entity.

---

## Conversion to CoNLL Format

In addition, a script was created to convert the dataset into the **CoNLL** format, which is a standard format for named entity recognition tasks.  
As a result of running the script, the following directories and files are created in the `encylopedia_ner_bio_dataset` folder:

```text
encylopedia_ner_bio_dataset/
├─ labels.txt                (Entity types)
├─ splits/
│  ├── train.conll           (CoNLL annotation)
│  └── train.tsv             (Simplified NER-TSV: TOKEN<TAB>NER)
├─ raw/                      (Raw texts)
├─ spans/
│  └── spans.jsonl           (Text fragments corresponding
                                           to entity spans)
└─ scripts/
└── {check_bio.py, spans_to_bio.py} (Project scripts,
                                     not created automatically)
```

The script for converting from spaCy format to CoNLL format is provided in the file `convert_to_conll.py`.


# Usage

## Dependencies

```text
python <= 3.13
spacy==3.8.11
tqdm==4.67.1
matplotlib==3.10.8
pandas==2.3.3
ipywidgets==8.1.8
```

To install all required dependencies, run:

```shell
pip install -Ur requirements.txt
```

The `convert_to_conll.py` script also performs automatic checking and installation of missing dependencies.


## Using the Dataset in spaCy

Import the `Pushkin_Dataset` module to work with the dataset as follows:

```python
from Puskin_Dataset import *

path_to_dataset = "entities.json"
PD = Puskin_Dataset()
PD.load_dataset(path_to_dataset)
```

Get the number of samples:

```python
N = PD.number_of_samples
```

Get information about a specific sample:

```python
text, entities, tokens, BIO_tags = PD.get_sample_by_id("10")
```

Entity visualization:

```python
PD.display_tags(text, entities)
```

Retrieve all entities of a given type from the dataset:

```python
PD.get_entites_by_type("LOC")
```

---

## Converting the Dataset to CoNLL

1. To convert the dataset from JSON format to JSONL, run the script `convert_to_conll.py`:
   ```shell
   python convert_to_conll.py
   ```

2. Validate the conversion results and print statistics:
   ```shell
   cd encyclopedia_ner_bio_dataset
   python scripts/check_bio.py splits/train.conll
   ```

---

# Statistics

*Number of entities for each type in the dataset:*

|   WORK-OF-ART             |PER                          |DATE                         |LOC                          |ORG                         |
|----------------|-------------------------------|-----------------------------|-------------------------------|-----------------------------|
|3206|7844            |2536           |890          |221     |

*Statistical measures for text fragments:*

|   Number of fragments             |Overall length                          |Total \# of tokens                         |Mean fragment length                          |Mean \# of tokens in a fragment                         |
|----------------|-------------------------------|-----------------------------|-------------------------------|-----------------------------|
|1567|1064459            |201613           |679.297384          |128.661774     |
