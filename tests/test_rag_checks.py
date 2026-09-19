"""Проверки цитат и чисел — чистые функции, без сети и без модели."""
from app.rag import narezka_po_zagolovkam, proverit_chisla, proverit_citatu

KUSKI = [{"istochnik": "garantiya.html#Гарантия",
          "tekst": "На выполненные работы мы даём гарантию 12 месяцев."}]


def test_proverit_citatu_naxodit_dosolvnuyu_citatu():
    rezultat = {"otvet": "12 месяцев", "citata": "мы даём гарантию 12 месяцев",
                "istochnik": "garantiya.html"}
    godno, _ = proverit_citatu(rezultat, KUSKI)
    assert godno


def test_proverit_citatu_lovit_pereskaz():
    rezultat = {"otvet": "3 месяца", "citata": "гарантия три месяца", "istochnik": "garantiya.html"}
    godno, prichina = proverit_citatu(rezultat, KUSKI)
    assert not godno
    assert "не найдена" not in prichina  # причина описательная, не пустая


def test_proverit_citatu_pustaya_citata_eto_otkaz():
    rezultat = {"otvet": "Не знаю, уточните у оператора", "citata": "", "istochnik": ""}
    godno, _ = proverit_citatu(rezultat, KUSKI)
    assert godno


def test_proverit_chisla_lovit_vydumannuyu_cifru():
    rezultat = {"otvet": "Гарантия 6 месяцев"}
    ok, lishnie = proverit_chisla(rezultat, KUSKI)
    assert not ok
    assert lishnie == {"6"}


def test_proverit_chisla_propuskaet_svoi_cifry():
    rezultat = {"otvet": "Гарантия 12 месяцев"}
    ok, lishnie = proverit_chisla(rezultat, KUSKI)
    assert ok
    assert not lishnie


def test_narezka_po_zagolovkam_delit_na_kuski_s_istochnikom():
    stranicy = {"test.html": "Заголовок страницы\nПодраздел\nТекст подраздела."}
    kuski = narezka_po_zagolovkam(stranicy)
    assert kuski
    assert all("istochnik" in k and "tekst" in k for k in kuski)
