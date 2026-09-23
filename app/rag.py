"""Логика v6 из notebooks/modul6__01_citaty_i_kachestvo.py, перенесённая в сервис.

Код не меняли по смыслу — только разложили по функциям, которые можно вызывать
без Jupyter, и добавили типы там, где это не мешает читать.
"""
import html
import json
import re
import time
import urllib.request
from functools import lru_cache

from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

from app import observability, storage
from app.config import API_KEY, BASE_URL, MODEL, SITE_BASE, SITE_STRANICY

PRAVILA_V6 = """Ты помощник сервисного центра «Полярис».
Отвечай ТОЛЬКО по тексту из блока ДАННЫЕ.
Верни JSON: {"otvet": "...", "citata": "...", "istochnik": "..."}
  otvet — ответ гостю, одно-два предложения;
  citata — фрагмент из ДАННЫХ слово в слово, на котором основан ответ;
  istochnik — значение [источник] того куска, откуда взята цитата.
Если ответа в данных нет, верни {"otvet": "Не знаю, уточните у оператора",
"citata": "", "istochnik": ""}."""


def html_v_tekst(stranica):
    tekst = re.sub(r"(?is)<(script|style|nav|footer)[^>]*>.*?</\1>", " ", stranica)
    tekst = re.sub(r"(?is)<(h[1-6]|p|li|br|div|tr)[^>]*>", "\n", tekst)
    tekst = re.sub(r"(?s)<[^>]+>", " ", tekst)
    return "\n".join(s.strip() for s in html.unescape(tekst).splitlines() if s.strip())


def narezka_po_zagolovkam(stranicy):
    kuski = []
    for imya, tekst in stranicy.items():
        zagolovok_stranicy = tekst.splitlines()[0]
        tekushchiy, podzagolovok = "", zagolovok_stranicy
        for stroka in tekst.split("\n")[1:]:
            zagolovok = len(stroka) < 60 and not stroka.endswith((".", ":", "₽"))
            if zagolovok and tekushchiy:
                kuski.append({"istochnik": f"{imya}#{podzagolovok}", "tekst": tekushchiy.strip()})
                tekushchiy, podzagolovok = "", stroka
            elif zagolovok:
                podzagolovok = stroka
            else:
                tekushchiy += stroka + "\n"
        if tekushchiy.strip():
            kuski.append({"istochnik": f"{imya}#{podzagolovok}", "tekst": tekushchiy.strip()})
    return kuski


def normalizovat(tekst):
    return re.sub(r"\s+", " ", tekst.lower()).strip()


def chisla(tekst):
    return set(re.findall(r"\d+", tekst))


def proverit_citatu(rezultat, kuski):
    """Возвращает (годно, причина) — дословно из модуля 6, шаг 3."""
    citata = normalizovat(rezultat.get("citata", ""))
    if not citata:
        return ("не знаю" in rezultat["otvet"].lower(), "цитаты нет")
    for kusok in kuski:
        if citata in normalizovat(kusok["tekst"]):
            if rezultat.get("istochnik") and rezultat["istochnik"] not in kusok["istochnik"]:
                return False, f"цитата из {kusok['istochnik']}, а источник указан {rezultat['istochnik']}"
            return True, "цитата найдена в источнике"
    return False, "цитаты нет ни в одном найденном куске"


def proverit_chisla(rezultat, kuski):
    v_otvete = chisla(rezultat["otvet"])
    v_dannyh = chisla(" ".join(k["tekst"] for k in kuski))
    lishnie = v_otvete - v_dannyh
    return (not lishnie), lishnie


class Indeks:
    """Куски документов и их эмбеддинги — то, что в ноутбуке было глобальными
    переменными KUSKI/EMB/VEKTORY. Здесь это состояние сервиса, а не блокнота."""

    def __init__(self, kuski, model_name="intfloat/multilingual-e5-small"):
        self.kuski = kuski
        self.emb = SentenceTransformer(model_name)
        vektory_iz_kesha = storage.zagruzit(kuski)
        if vektory_iz_kesha is not None:
            self.vektory = vektory_iz_kesha
        else:
            self.vektory = self.emb.encode(
                [f"passage: {k['istochnik']} {k['tekst']}" for k in kuski], normalize_embeddings=True)
            storage.sohranit(kuski, self.vektory)

    def nayti(self, vopros, k=3, porog=0.80):
        vektor = self.emb.encode(f"query: {vopros}", normalize_embeddings=True)
        blizost = util.cos_sim(vektor, self.vektory)[0]
        poryadok = sorted(range(len(self.kuski)), key=lambda i: float(blizost[i]), reverse=True)
        return [self.kuski[i] for i in poryadok[:k] if float(blizost[i]) >= porog]


def skachat_stranicy(baza=SITE_BASE, imena=SITE_STRANICY):
    stranicy = {}
    for imya in imena:
        with urllib.request.urlopen(baza + imya, timeout=30) as otvet:
            stranicy[imya] = html_v_tekst(otvet.read().decode("utf-8"))
    return stranicy


@lru_cache
def zagruzit_indeks():
    """Строится при первом запросе и живёт, пока жив процесс — но теперь эмбеддинги
    ещё и лежат в файловом кэше (`app/storage.py`), так что **перезапуск** процесса
    не значит пересчёт заново (модуль 7, урок 2)."""
    stranicy = skachat_stranicy()
    kuski = narezka_po_zagolovkam(stranicy)
    return Indeks(kuski)


def sprosit_json(client, vopros, kuski, pravila=PRAVILA_V6, model=MODEL):
    nachalo = time.perf_counter()
    dannye = "\n\n".join(f"[источник: {k['istochnik']}]\n{k['tekst']}" for k in kuski)
    otvet = client.chat.completions.create(
        model=model, temperature=0, max_tokens=300, response_format={"type": "json_object"},
        messages=[{"role": "system", "content": pravila},
                  {"role": "user", "content": f"ДАННЫЕ:\n{dannye}\n\nВОПРОС: {vopros}"}])
    observability.zapisat("ask", vopros, otvet, nachalo)
    syroy = (otvet.choices[0].message.content or "").strip()
    try:
        return json.loads(syroy)
    except json.JSONDecodeError:
        return {"otvet": syroy, "citata": "", "istochnik": ""}


@lru_cache
def klient():
    return OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=30, max_retries=0)


def otvetit(vopros, indeks=None, ask=None):
    """v6 целиком (модуль 6, шаг 8), но как функция сервиса, а не ячейка ноутбука.

    `indeks` и `ask` — необязательные параметры для тестов: чтобы проверить
    отказ/проверки без реальной модели и без сети, подставляют фейковый индекс
    и фейковую функцию ответа вместо реального `sprosit_json`.
    """
    indeks = indeks or zagruzit_indeks()
    ask = ask or (lambda vopros, kuski: sprosit_json(klient(), vopros, kuski))

    kuski = indeks.nayti(vopros)
    if not kuski:
        return {"otvet": "Не знаю, уточните у оператора.", "istochnik": "", "proverki": "поиск пуст"}

    rezultat = ask(vopros, kuski)
    citata_ok, prichina = proverit_citatu(rezultat, kuski)
    chisla_ok, lishnie = proverit_chisla(rezultat, kuski)
    if not (citata_ok and chisla_ok):
        return {"otvet": "Не могу ответить уверенно, уточните у оператора.",
                "istochnik": "", "proverki": f"цитата: {citata_ok}, числа: {chisla_ok}"}
    return {**rezultat, "proverki": "пройдены"}
