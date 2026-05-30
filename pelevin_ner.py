# pelevin_ner.py — Конвейер для распознавания именованных сущностей в русских литературных текстах.
#
# Использование:
#   from pelevin_ner import NERPipeline
#
#   pipeline = NERPipeline()
#   df = pipeline.run_from_file("texts/genp_text.txt")
#   df = pipeline.run(text)
#
#   Отдельные этапы можно вызывать для отладки:
#   cleaned = pipeline.clean_text(raw)
#   nat_res = pipeline.extract_natasha(cleaned)
#   spc_res = pipeline.extract_spacy(cleaned)
#   merged  = pipeline.merge_results(nat_res, spc_res)
#   final   = pipeline.enrich_with_wiki(merged)
#   df      = pipeline.to_dataframe(final)
#
# Кеш Wikipedia хранится в wiki_cache.json рядом со скриптом.
# Удалите файл, чтобы принудительно обновить данные.

import json
import os
import re
import time
import requests
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import wikipediaapi
import pandas as pd
import spacy
from nltk.corpus import stopwords
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, NewsNERTagger, Doc


# Слова в биографии, указывающие что статья о реальном человеке
PERSON_MARKERS = [
    'родился', 'родилась', 'умер', 'умерла', 'скончался', 'скончалась',
    'писатель', 'писательница', 'поэт', 'поэтесса', 'драматург',
    'переводчик', 'сценарист', 'критик', 'публицист', 'журналист', 'литератор',
    'актёр', 'актриса', 'режиссёр',
    'музыкант', 'певец', 'певица', 'композитор',
    'художник', 'скульптор', 'архитектор', 'живописец', 'гравёр',
    'учёный', 'историк', 'философ', 'психолог', 'социолог', 'лингвист',
    'политик', 'деятель', 'революционер', 'военачальник', 'полководец',
    'правитель', 'предводитель', 'император', 'царь',
    'предприниматель', 'изобретатель', 'инженер',
    'лётчик', 'космонавт',
    'спортсмен', 'спортсменка',
    'богослов', 'священник', 'монах', 'святой', 'апостол', 'пророк',
    'мистик', 'гуру',
    'бог', 'богиня', 'божество',
]

# Профессии и роды деятельности, которые сохраняются в итоговом результате
ACTIVITIES = [
    'писатель', 'писательница', 'поэт', 'поэтесса', 'драматург',
    'переводчик', 'сценарист', 'критик', 'публицист', 'журналист', 'литератор',
    'актёр', 'актриса', 'режиссёр',
    'музыкант', 'певец', 'певица', 'композитор',
    'художник', 'скульптор', 'архитектор', 'живописец', 'гравёр',
    'учёный', 'историк', 'философ', 'психолог', 'социолог', 'лингвист',
    'политик', 'деятель', 'революционер', 'военачальник', 'полководец',
    'правитель', 'предводитель', 'император', 'царь',
    'предприниматель', 'изобретатель', 'инженер',
    'лётчик', 'космонавт',
    'спортсмен', 'спортсменка',
    'богослов', 'священник', 'монах', 'святой', 'апостол', 'пророк',
    'мистик', 'гуру',
    'бог', 'богиня', 'божество',
]

# Признаки страницы-дизамбига
DISAMBIGUATION_SIGNS = [
    'многозначный', 'неоднозначность',
    'может означать', 'матронимическ', 'патронимическ',
    'страница значений',
]


class NERPipeline:

    def __init__(
        self,
        spacy_model: str = 'ru_core_news_lg',
        wiki_user_agent: str = 'pelevin-ner-project',
    ):
        self.spacy_model_name = spacy_model
        self.wiki_user_agent = wiki_user_agent
        self.nlp = None
        self.natasha = None
        self.local = threading.local()
        self.wiki_cache: dict = {}
        self.cache_lock = threading.Lock()

    def run_from_file(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        return self.run(raw)

    def run(self, text: str):
        cleaned = self.clean_text(text)
        merged = self.merge_results(
            self.extract_natasha(cleaned),
            self.extract_spacy(cleaned),
        )
        final = self.enrich_with_wiki(merged)
        return self.to_dataframe(final)

    # --- Предобработка ---

    def clean_text(self, text: str):
        parts = []
        for line in text.splitlines():
            line = re.sub(r'^"', '', line)
            line = re.sub(r'"\s*$', ' ', line)
            line = line.replace('—', '-').replace('–', '-')
            line = line.replace('«', '"').replace('»', '"')
            line = re.sub(r'\s+', ' ', line).strip()
            if line:
                parts.append(line)
        return ' '.join(parts)

    # --- Natasha ---

    def load_natasha(self):
        if self.natasha is None:
            emb = NewsEmbedding()
            self.natasha = {
                'segmenter':    Segmenter(),
                'morph_vocab':  MorphVocab(),
                'morph_tagger': NewsMorphTagger(emb),
                'ner_tagger':   NewsNERTagger(emb),
            }
        return self.natasha

    def extract_natasha(self, text: str):
        c = self.load_natasha()
        doc = Doc(text)
        doc.segment(c['segmenter'])
        doc.tag_morph(c['morph_tagger'])
        for token in doc.tokens:
            token.lemmatize(c['morph_vocab'])
        doc.tag_ner(c['ner_tagger'])
        persons = [
            ' '.join(t.lemma for t in span.tokens).lower()
            for span in doc.spans
            if span.type == 'PER'
        ]
        result = self.counter_to_info(Counter(persons))
        print(f'Natasha: {len(persons)} упоминаний, {len(result)} уникальных')
        return result

    # --- spaCy ---

    def load_spacy(self):
        if self.nlp is None:
            self.nlp = spacy.load(self.spacy_model_name)
        return self.nlp

    def extract_spacy(self, text: str):
        doc = self.load_spacy()(text)
        persons = [
            ' '.join(t.lemma_ for t in ent).lower()
            for ent in doc.ents
            if ent.label_ == 'PER'
        ]
        result = self.counter_to_info(Counter(persons))
        print(f'spaCy: {len(persons)} упоминаний, {len(result)} уникальных')
        return result

    def merge_results(self, store1: dict, store2: dict):
        merged = {}
        for ent in set(store1) | set(store2):
            info1, info2 = store1.get(ent), store2.get(ent)
            if info1 and info2:
                merged[ent] = {'count': max(info1['count'], info2['count'])}
            else:
                merged[ent] = (info1 or info2).copy()
        print(f'После объединения: {len(merged)} уникальных сущностей')
        return merged

    # --- Wikipedia ---

    def get_thread_wiki(self):
        if not hasattr(self.local, 'wiki'):
            self.local.wiki = wikipediaapi.Wikipedia(
                language='ru', user_agent=self.wiki_user_agent,
            )
        return self.local.wiki

    def get_session(self):
        if not hasattr(self.local, 'session'):
            s = requests.Session()
            s.headers['User-Agent'] = self.wiki_user_agent
            self.local.session = s
        return self.local.session

    # Загружает кеш, запускает параллельное обогащение, сохраняет кеш.
    def enrich_with_wiki(self, merged_persons: dict, max_workers: int = 4,
                         cache_path: str = 'wiki_cache.json'):
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                self.wiki_cache = json.load(f)
        else:
            self.wiki_cache = {}

        cached_hits = sum(1 for v in self.wiki_cache.values() if v.get('found'))
        print(f'Кеш: {len(self.wiki_cache)} записей, из них найдено {cached_hits}')

        final_persons = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_entity, ent, info): ent
                for ent, info in merged_persons.items()
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception:
                    continue
                if result is None:
                    continue
                canonical, data = result
                if canonical in final_persons:
                    final_persons[canonical]['count'] += data['count']
                else:
                    final_persons[canonical] = data

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.wiki_cache, f, ensure_ascii=False, indent=2)

        print(f'После обогащения Wikipedia: {len(final_persons)} персон')
        return final_persons

    # Сначала проверяет кеш, затем лезет в Wikipedia.
    # None без исключения = страницы нет → кешируем.
    # Исключение = сетевая ошибка → ретраим, не кешируем.
    def process_entity(self, ent: str, info: dict):
        cached = self.wiki_cache.get(ent)
        if cached is not None:
            if not cached['found']:
                return None
            first_part = ' ' + cached['summary'].lower()
            return self.extract_result(first_part, info, cached['canonical'])

        wiki = self.get_thread_wiki()
        for attempt in range(3):
            try:
                page = self.find_wiki_page(wiki, ent)

                if page is None:
                    with self.cache_lock:
                        self.wiki_cache[ent] = {'found': False}
                    return None

                summary = page.summary[:600] if page.summary else ''
                with self.cache_lock:
                    self.wiki_cache[ent] = {
                        'found':     True,
                        'canonical': page.title,
                        'summary':   summary,
                    }

                first_part = (' ' + summary.lower()) if summary else ''
                return self.extract_result(first_part, info, page.title)

            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return None

    # Возвращает страницу или None (страницы нет).
    # Сетевые ошибки из API-запроса пробрасываются наверх — вызывающий код
    # отличает их от None и не кеширует временные сбои как «не найдено».
    # Для многословных запросов выбирает из 5 результатов наиболее близкий
    # к запросу по пересечению слов в заголовке.
    def find_wiki_page(self, wiki, ent: str):
        try:
            page = wiki.page(ent.title())
            if page.exists() and not self.is_disambiguation(page):
                return page
        except Exception:
            pass

        r = self.get_session().get(
            'https://ru.wikipedia.org/w/api.php',
            params={
                'action': 'query', 'list': 'search',
                'srsearch': ent, 'format': 'json', 'srlimit': 5,
            },
            timeout=10,
        )
        results = r.json().get('query', {}).get('search', [])

        best_page, best_score = None, -1
        for result in results:
            try:
                p = wiki.page(result['title'])
                if p.exists() and not self.is_disambiguation(p):
                    score = self.name_score(ent, p.title)
                    if score > best_score:
                        best_score = score
                        best_page = p
            except Exception:
                continue
        return best_page

    def is_disambiguation(self, page):
        title = page.title or ''
        if '(значения)' in title:
            return True
        s = page.summary[:300].lower() if page.summary else ''
        if not s:
            return True
        if re.search(r'\bфамилия\b', s):
            is_bio_mention = re.search(
                r'(?:настоящ|при рождении|урождён|псевдоним).{0,25}фамилия'
                r'|фамилия.{0,25}(?:при рождении|настоящ)',
                s,
            )
            if not is_bio_mention:
                return True
        return any(sign in s for sign in DISAMBIGUATION_SIGNS)

    # Формирует итоговую запись из сводки Wikipedia.
    def extract_result(self, first_part: str, info: dict, canonical: str):
        if not self.has_marker(first_part, PERSON_MARKERS):
            return None
        activities = self.find_activities(first_part, ACTIVITIES)
        is_deity   = any(w in activities for w in ('бог', 'богиня', 'божество'))
        birth_year = death_year = None
        if not is_deity:
            birth_year, death_year = self._extract_years_from_parens(first_part)
        return canonical, {
            'count':      info['count'],
            'activities': activities,
            'birth_year': birth_year,
            'death_year': death_year,
        }

    # Ищет годы рождения и смерти в первом скобочном блоке после имени.
    # Формат в русской Википедии: (... год_рождения ... — ... год_смерти ...)
    # для умерших, или (... год_рождения ...) для живых.
    # Поддерживает один уровень вложенных скобок (напр. 17 (29) января для
    # дат по старому/новому стилю).
    def _extract_years_from_parens(self, text: str):
        birth_year = death_year = None
        for m in re.finditer(r'\((?:[^()]*|\([^()]*\))*\)', text):
            paren_text = m.group(0)[1:-1]
            first_year = re.search(r'(1[0-9]{3}|20[0-9]{2})', paren_text)
            if not first_year:
                continue
            birth_year = int(first_year.group(1))
            after_birth = paren_text[first_year.end():]
            dash = re.search(r'[—–]', after_birth)
            if dash:
                death_match = re.search(r'(1[0-9]{3}|20[0-9]{2})', after_birth[dash.end():])
                if death_match:
                    death_year = int(death_match.group(1))
            break
        return birth_year, death_year

    # --- Вспомогательные методы ---

    def has_marker(self, text: str, markers: list) -> bool:
        return any(re.search(r'\b' + re.escape(m) + r'\b', text) for m in markers)

    def find_activities(self, text: str, activities: list) -> list:
        return [a for a in activities if re.search(r'\b' + re.escape(a) + r'\b', text)]

    # Сколько слов запроса встречается в заголовке страницы (подстрока в любую сторону).
    # Покрывает падежи: 'цветаев' ⊂ 'цветаева', 'уайльда' ⊃ 'уайльд'.
    def name_score(self, ent: str, page_title: str) -> int:
        ent_words = [w for w in ent.lower().split() if len(w) > 2]
        if not ent_words:
            return 0
        title_parts = [p for p in re.split(r'\W+', page_title.lower()) if p]
        return sum(
            1 for ew in ent_words
            if any(ew in tp or tp in ew for tp in title_parts)
        )

    def counter_to_info(self, counter: Counter) -> dict:
        return {ent: {'count': cnt} for ent, cnt in counter.items()}

    # --- Результат ---

    def to_dataframe(self, final_persons: dict):
        df = pd.DataFrame.from_dict(final_persons, orient='index')
        df.index.name = 'entity'
        df.reset_index(inplace=True)
        return df
