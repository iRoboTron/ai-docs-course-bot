"""Хранилище индекса: куски и эмбеддинги переживают перезапуск процесса.

Файловый кэш на диске — самый простой вариант, что работает. Ключ кэша — хэш
самих кусков: если сайт поменялся, старый кэш просто не совпадёт и пересчитается
заново, разбираться со сроком годности вручную не нужно.
"""
import hashlib
import json
import os
from pathlib import Path

import numpy as np

CACHE_DIR = Path(os.environ.get("INDEX_CACHE_DIR", ".index_cache"))


def klyuch_keshа(kuski):
    """Хэш содержимого кусков — не имени файла и не даты, а именно текста."""
    soderzhimoe = "\n".join(f"{k['istochnik']}|{k['tekst']}" for k in kuski)
    return hashlib.sha256(soderzhimoe.encode("utf-8")).hexdigest()[:16]


def sohranit(kuski, vektory, put=CACHE_DIR):
    put.mkdir(parents=True, exist_ok=True)
    klyuch = klyuch_keshа(kuski)
    np.save(put / f"{klyuch}.npy", vektory)
    (put / f"{klyuch}.json").write_text(json.dumps(kuski, ensure_ascii=False), encoding="utf-8")
    return klyuch


def zagruzit(kuski, put=CACHE_DIR):
    """Возвращает готовые векторы, если на диске лежит кэш для этих же кусков — иначе None."""
    klyuch = klyuch_keshа(kuski)
    put_npy = put / f"{klyuch}.npy"
    put_json = put / f"{klyuch}.json"
    if not (put_npy.is_file() and put_json.is_file()):
        return None
    kuski_iz_kesha = json.loads(put_json.read_text(encoding="utf-8"))
    if kuski_iz_kesha != kuski:
        return None  # на всякий случай: хэш совпал, а содержимое — нет (коллизия)
    return np.load(put_npy)
