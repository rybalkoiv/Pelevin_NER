#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate BIO tags in CoNLL **without** sentence splitting.
- Treats each `-DOCSTART-` block as a single flat sequence of tags.
- Blank lines are ignored (do not start a new sequence).

Usage:
  python check_bio.py path/to/file.conll
Exit code 0 if OK, 1 if issues found, 2 for usage.
"""
import sys
import statistics


def validate_bio(tags):
    """Simple IOB2 validator.
    Rules:
      - O resets state
      - B-XXX starts a new entity of type XXX
      - I-XXX must follow B-XXX or I-XXX of the same type
    """
    prev_type = None
    inside = False
    errors = []
    for i, tag in enumerate(tags):
        if tag == 'O':
            inside = False
            prev_type = None
            continue
        if '-' not in tag:
            errors.append((i, tag, 'Tag missing "-" (expected B-XXX/I-XXX)'))
            inside = False
            prev_type = None
            continue
        pref, ent = tag.split('-', 1)
        if pref == 'B':
            inside = True
            prev_type = ent
        elif pref == 'I':
            if not inside or prev_type != ent:
                errors.append((i, tag, 'I without preceding B/I of same type'))
            inside = True
            prev_type = ent
        else:
            errors.append((i, tag, 'Unknown prefix (expected B/I/O)'))
    return errors


def read_conll_docs(path):
    """Read CoNLL file into flat sequences per document.
    - `-DOCSTART-` starts a new document.
    - Blank lines are ignored (no sentence boundaries).
    - Tag is taken from the last column in each token line.
    """
    docs = []
    tags = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                # ignore blank lines entirely (no sentence splitting)
                continue
            if line.startswith('-DOCSTART-'):
                if tags:
                    docs.append(tags)
                    tags = []
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            tags.append(parts[-1])
    if tags:
        docs.append(tags)
    return docs


def compute_stats(docs):
    """Compute simple stats for flat CoNLL docs.
    Returns a dict with document/token counts and entity counts (by B-* tags).
    """
    num_docs = len(docs)
    tokens_per_doc = [len(tags) for tags in docs]
    total_tokens = sum(tokens_per_doc)
    mean_tokens = statistics.mean(tokens_per_doc) if num_docs else 0
    median_tokens = statistics.median(tokens_per_doc) if num_docs else 0
    min_tokens = min(tokens_per_doc) if num_docs else 0
    max_tokens = max(tokens_per_doc) if num_docs else 0

    entity_total = 0
    entity_by_type = {}
    tag_counts = {}
    for tags in docs:
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if tag.startswith('B-'):
                entity_total += 1
                ent = tag.split('-', 1)[1]
                entity_by_type[ent] = entity_by_type.get(ent, 0) + 1

    return {
        'num_docs': num_docs,
        'tokens_per_doc': tokens_per_doc,
        'total_tokens': total_tokens,
        'mean_tokens': mean_tokens,
        'median_tokens': median_tokens,
        'min_tokens': min_tokens,
        'max_tokens': max_tokens,
        'entity_total': entity_total,
        'entity_by_type': entity_by_type,
        'tag_counts': tag_counts,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python check_bio.py path/to/file.conll')
        sys.exit(2)
    path = sys.argv[1]
    total_err = 0
    docs = read_conll_docs(path)
    for di, tags in enumerate(docs):
        errs = validate_bio(tags)
        for i, tag, msg in errs:
            print(f'doc={di} idx={i} tag={tag}: {msg}')
        total_err += len(errs)

    # --- Stats ---
    st = compute_stats(docs)
    print("--- Stats ---")
    print(f"Documents: {st['num_docs']}")
    print(f"Tokens total: {st['total_tokens']}")
    if st['num_docs']:
        print(
            "Tokens/doc: "
            f"mean={st['mean_tokens']:.1f}, median={st['median_tokens']}, "
            f"min={st['min_tokens']}, max={st['max_tokens']}"
        )
    print(f"Entities (via B-*): {st['entity_total']}")
    if st['entity_by_type']:
        for ent, cnt in sorted(st['entity_by_type'].items()):
            print(f"  {ent}: {cnt}")

    if total_err == 0:
        print('BIO looks consistent')
    else:
        print(f'Found {total_err} issues !!! ')
        sys.exit(1)
