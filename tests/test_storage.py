"""Файловый кэш индекса — без модели и без сети, только numpy и диск."""
import numpy as np

from app import storage

KUSKI = [{"istochnik": "garantiya.html#Гарантия", "tekst": "Гарантия 12 месяцев."}]
VEKTORY = np.array([[0.1, 0.2, 0.3]], dtype="float32")


def test_zagruzit_bez_kesha_vozvrashchaet_none(tmp_path):
    assert storage.zagruzit(KUSKI, put=tmp_path) is None


def test_sohranit_i_zagruzit_daet_te_zhe_vektory(tmp_path):
    storage.sohranit(KUSKI, VEKTORY, put=tmp_path)
    iz_kesha = storage.zagruzit(KUSKI, put=tmp_path)
    assert iz_kesha is not None
    assert np.array_equal(iz_kesha, VEKTORY)


def test_izmenivshiesya_kuski_ne_beryotsya_iz_kesha(tmp_path):
    storage.sohranit(KUSKI, VEKTORY, put=tmp_path)
    drugie_kuski = [{"istochnik": "garantiya.html#Гарантия", "tekst": "Гарантия 6 месяцев."}]
    assert storage.zagruzit(drugie_kuski, put=tmp_path) is None


def test_klyuch_zavisit_ot_soderzhimogo_a_ne_ot_poryadka_klyuchey():
    a = {"istochnik": "x", "tekst": "y"}
    b = {"tekst": "y", "istochnik": "x"}
    assert storage.klyuch_keshа([a]) == storage.klyuch_keshа([b])
