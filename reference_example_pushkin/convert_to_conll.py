#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def ensure_requirements(requirements_path="requirements.txt"):
    import sys
    import subprocess
    from pathlib import Path
    from importlib import metadata

    print(f"[deps] checking {requirements_path}")

    if not Path(requirements_path).exists():
        print("[deps] requirements.txt not found, skipping")
        return

    def ok(pkg):
        try:
            metadata.version(pkg)
            __import__(pkg)
            print(f"[deps] OK: {pkg}")
            return True
        except Exception as e:
            print(f"[deps] BROKEN: {pkg} ({e.__class__.__name__})")
            return False

    missing = []
    with open(requirements_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = line.split("==")[0].split(">=")[0].split("<=")[0]
            if not ok(pkg):
                missing.append(line)

    if not missing:
        print("[deps] all requirements satisfied")
        return

    print(f"[deps] reinstalling {len(missing)} package(s): {missing}")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--force-reinstall", *missing]
    )
    print("[deps] installation complete")

def to_spans_record(
    rec: dict,
    *,
    fallback_id: str,
    id_field: str | None = None,
    strict: bool = True,
) -> dict:
    """Convert a single record {text, entities} -> {id, text, spans}.

    - Validates offsets are within [0, len(text)].
    - Ensures start < end and label is str.
    - If id_field present in input, uses it; else uses fallback_id.
    """
    if "text" not in rec:
        raise ValueError("Record missing 'text'")
    text: str = rec["text"]

    ents = rec.get("entities", [])
    if not isinstance(ents, list):
        raise ValueError("'entities' must be a list of [start, end, label]")

    spans: list[dict] = []
    for j, triplet in enumerate(ents):
        if not (isinstance(triplet, (list, tuple)) and len(triplet) == 3):
            raise ValueError(f"Entity #{j} is not [start, end, label]: {triplet!r}")
        start, end, label = triplet
        if not (isinstance(start, int) and isinstance(end, int)):
            raise ValueError(f"Entity #{j} start/end must be int: {triplet!r}")
        if not isinstance(label, str):
            raise ValueError(f"Entity #{j} label must be str: {triplet!r}")
        if not (0 <= start < end <= len(text)):
            msg = (
                f"Entity #{j} offsets out of range or invalid: start={start}, end={end}, len={len(text)}"
            )
            if strict:
                raise ValueError(msg)
            else:
                # skip silently in non-strict mode
                continue
        spans.append({"start": start, "end": end, "label": label})

    rid = (
        rec.get(id_field) if (id_field and isinstance(rec.get(id_field), (str, int))) else fallback_id
    )

    return {"id": str(rid), "text": text, "spans": spans}

def convert_dataset():
    from Puskin_Dataset import Puskin_Dataset
    from tqdm import tqdm
    import json
    from pathlib import Path
    from encyclopedia_ner_bio_dataset.scripts.spans_to_bio import process_spans

    out = Path("encyclopedia_ner_bio_dataset")
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "splits").mkdir(parents=True, exist_ok=True)
    (out / "spans").mkdir(parents=True, exist_ok=True)
    spans_out = (out / "spans" / "spans.jsonl")
    conll_out = (out / "splits" / "train.conll")
    tsv_out = (out / "splits" / "train.tsv")
    path_to_dataset = "dataset_25_04_2024.json"
    PD = Puskin_Dataset()
    PD.load_dataset(path_to_dataset)

    bio_labels = ['PER', 'WORK-OF-ART', 'DATE', 'LOC', 'ORG']

    # создание лейблов
    labels = ["O"] + [f"{pref}-{lab}" for lab in bio_labels for pref in ("B", "I")]
    (out / "labels.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")

    # формирование набора данных
    with spans_out.open("w", encoding="utf-8") as w:
        for idx in tqdm(PD.data):
            # print(PD.data[idx]['BIO_Tags'])
            out_obj = to_spans_record(
                PD.data[idx],
                fallback_id=f"doc{idx}"
            )
            w.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            (out / "raw" / (idx + ".txt")).write_text(PD.data[idx]['text'], encoding="utf-8")
    process_spans(spans_out, conll_out, tsv_out)


if __name__ =='__main__':
    ensure_requirements('requirements.txt')
    convert_dataset()