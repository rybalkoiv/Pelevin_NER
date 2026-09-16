#!/usr/bin/env python3
# Конвертация spans.jsonl -> CoNLL (простая токенизация)
import json, sys, re

TOKEN_RE = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)

def spans_to_bio_one(text, spans):
    char_labels = ['O'] * len(text)
    for s in spans:
        for i in range(s['start'], s['end']):
            if 0 <= i < len(char_labels):
                char_labels[i] = s['label']

    tokens, tags = [], []
    prev_label = 'O'

    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        start, end = m.start(), m.end()
        segment = char_labels[start:end]

        label = next((l for l in segment if l != 'O'), 'O')

        if label == 'O':
            tag = 'O'
        else:
            tag = f"B-{label}" if prev_label != label else f"I-{label}"

        tokens.append(tok)
        tags.append(tag)
        prev_label = label

    return tokens, tags

def write_conll(docs, out_path):
    with open(out_path, 'w', encoding='utf-8') as w:
        for doc in docs:
            w.write("-DOCSTART- -X- O O\n\n")
            for tok, tag in zip(doc['tokens'], doc['tags']):
                w.write(f"{tok} X X {tag}\n")
            w.write("\n")

def conll_to_ner_tsv(conll_path, tsv_path):
    with open(conll_path, encoding="utf-8") as f, open(tsv_path, "w", encoding="utf-8") as out:
        for line in f:
            line = line.strip()
            if not line:
                out.write("\n")
                continue
            if line.startswith("-DOCSTART-"):
                out.write("\n")
                continue

            cols = line.split()
            token = cols[0]
            ner = cols[-1]
            out.write(f"{token}\t{ner}\n")

def process_spans(spans_path, out_path, tsv_path):
    docs = []
    with open(spans_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            text = obj['text']
            spans = obj.get('spans', [])
            tokens, tags = spans_to_bio_one(text, spans)
            docs.append({'id': obj.get('id'), 'tokens': tokens, 'tags': tags})
    write_conll(docs, out_path)
    conll_to_ner_tsv(out_path, tsv_path=tsv_path)
    print(f"Wrote {out_path}")

if __name__ == '__main__':
    spans_path, out_path, tsv_path = sys.argv[1], sys.argv[2], sys.argv[3]
    if not tsv_path:
        tsv_path = out_path + '.tsv'
    process_spans(spans_path, out_path)
    conll_to_ner_tsv(out_path, tsv_path=tsv_path)

