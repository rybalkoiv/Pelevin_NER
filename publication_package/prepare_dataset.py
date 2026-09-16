#!/usr/bin/env python3
"""Build the publication-ready CSV from the repository's result.csv."""

import ast
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "source" / "result_original.csv"
OUTPUT = ROOT / "pelevin_named_entities.csv"

WORK_YEARS = {
    "Жизнь насекомых": 1993,
    "Чапаев и пустота": 1996,
    "Желтая стрела": 1993,
    "Generation «П»": 1999,
    "Священная книга оборотня": 2004,
    "Empire V": 2006,
    "t": 2009,
    "Ананасная вода для прекрасной дамы": 2010,
    "S.N.U.F.F.": 2011,
    "Бэтман Аполло": 2013,
    "Лампа_Мафусаила,_или_Крайняя_битва_чекистов_с_масонами_": 2016,
    "iPhuck 10": 2017,
    "Искусство легких касаний": 2019,
    "Непобедимое солнце": 2020,
    "TRANSHUMANISM INC": 2021,
    "KGBT+ (КГБТ+)": 2022,
    "A Sinistra  А Синистра  Левый Путь": 2023,
    "Круть": 2024,
    "Возвращение Синей Бороды": 2026,
    "Македонская_критика_французской_мысли": 2003,
    "Числа": 2003,
    "Зал поющих кариатид": 2008,
}

DISPLAY_TITLES = {
    "Лампа_Мафусаила,_или_Крайняя_битва_чекистов_с_масонами_":
        "Лампа Мафусаила, или Крайняя битва чекистов с масонами",
    "Македонская_критика_французской_мысли":
        "Македонская критика французской мысли",
    "A Sinistra  А Синистра  Левый Путь": "A Sinistra / А Синистра / Левый Путь",
}

ACTIVITY_FIXES = {
    "ученый": "учёный",
    "режжисёр": "режиссёр",
    "де-ятель": "деятель",
}

# These work/entity pairs are explicitly marked as fictionalized characters in
# analize.ipynb and excluded from the relevant analyses in the article.
EXCLUDED_AS_CHARACTER = {
    ("Empire V", "Осирис"), ("Empire V", "Гера"),
    ("Бэтман Аполло", "Гера"), ("Бэтман Аполло", "Осирис"),
    ("Чапаев и пустота", "Чапаев, Василий Иванович"),
    ("S.N.U.F.F.", "Леви, Бернар-Анри"),
    ("t", "Достоевский, Фёдор Михайлович"), ("Empire V", "Иштар"),
    ("Бэтман Аполло", "Иштар"), ("t", "Толстой, Лев Николаевич"),
    ("Непобедимое солнце", "Каракалла"),
    ("Непобедимое солнце", "Гелиогабал"), ("Empire V", "Бальдр"),
    ("Ананасная вода для прекрасной дамы", "Буш, Джордж (старший)"),
    ("Чапаев и пустота", "Шварценеггер, Арнольд"),
    ("t", "Победоносцев, Константин Петрович"),
    ("Ананасная вода для прекрасной дамы", "Аристотель"),
    ("Возвращение Синей Бороды", "Эпштейн, Джеффри"),
    ("A Sinistra  А Синистра  Левый Путь", "Медичи, Лоренцо"),
    ("Чапаев и пустота", "Кавабата, Ясунари"),
    ("Empire V", "Энлиль"), ("Бэтман Аполло", "Энлиль"),
    ("Empire V", "Брама"), ("Бэтман Аполло", "Брама"),
    ("Непобедимое солнце", "Элагабал (бог)"),
    ("A Sinistra  А Синистра  Левый Путь", "Селена"),
    ("Generation «П»", "Березовский, Борис Абрамович"),
    ("Непобедимое солнце", "Марк Лициний Красс"),
    ("S.N.U.F.F.", "Голиаф"), ("Empire V", "Мардук"),
    ("Бэтман Аполло", "Мардук"),
    ("Чапаев и пустота", "Брюсов, Валерий Яковлевич"),
    ("Чапаев и пустота", "Унгерн-Штернберг, Роман Фёдорович фон"),
}


def integer(value: str) -> str:
    if not value.strip():
        return ""
    return str(int(float(value)))


def year(value: str) -> str:
    """Use negative integers for the source's BCE dates."""
    result = integer(value)
    if result and int(result) > 2026:
        result = str(-int(result))
    return result


def activities(value: str) -> str:
    raw = ast.literal_eval(value)
    normalized = []
    for item in raw:
        # One malformed source value combines two categories in one string.
        for part in item.split(","):
            fixed = ACTIVITY_FIXES.get(part.strip(), part.strip())
            if fixed and fixed not in normalized:
                normalized.append(fixed)
    return "|".join(normalized)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    fields = [
        "work_title", "work_year", "entity", "mention_count", "activities",
        "birth_year", "death_year", "country_or_polity", "exclude_as_character",
    ]
    with OUTPUT.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            raw_title = row["source"]
            writer.writerow({
                "work_title": DISPLAY_TITLES.get(raw_title, raw_title),
                "work_year": WORK_YEARS[raw_title],
                "entity": row["entity"].strip(),
                "mention_count": integer(row["count"]),
                "activities": activities(row["activities"]),
                "birth_year": year(row["birth_year"]),
                "death_year": year(row["death_year"]),
                "country_or_polity": row["страна"].strip(),
                "exclude_as_character": str((raw_title, row["entity"]) in EXCLUDED_AS_CHARACTER).lower(),
            })


if __name__ == "__main__":
    main()
