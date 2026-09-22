"""Тесты API поверх фейкового индекса и фейкового ответа модели — не ходят в сеть."""
from fastapi.testclient import TestClient

from app.main import app
from app import rag

client = TestClient(app)


class FakeIndeks:
    """Заменяет Indeks в тестах: всегда отдаёт один и тот же набор кусков, без
    эмбеддингов и без модели поиска — качество поиска здесь не проверяем, оно
    проверено отдельно в модуле 5. Тестируем только то, что происходит после
    поиска: проверки цитаты и чисел."""

    def __init__(self, kuski):
        self.kuski = kuski

    def nayti(self, vopros, k=3, porog=0.80):
        return self.kuski


KUSKI = [{"istochnik": "garantiya.html#Гарантия",
          "tekst": "На выполненные работы мы даём гарантию 12 месяцев."}]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_vozvrashchaet_otvet_kogda_proverki_proshli():
    fake_indeks = FakeIndeks(KUSKI)
    fake_ask = lambda vopros, kuski: {
        "otvet": "Гарантия 12 месяцев.", "citata": "мы даём гарантию 12 месяцев",
        "istochnik": "garantiya.html#Гарантия"}
    rezultat = rag.otvetit("Какая гарантия?", indeks=fake_indeks, ask=fake_ask)
    assert rezultat["proverki"] == "пройдены"
    assert "12" in rezultat["otvet"]


def test_ask_otkazyvaet_kogda_citata_pridumana(monkeypatch):
    fake_indeks = FakeIndeks(KUSKI)
    fake_ask = lambda vopros, kuski: {
        "otvet": "Гарантия 3 месяца.", "citata": "выдуманная цитата",
        "istochnik": "garantiya.html#Гарантия"}
    rezultat = rag.otvetit("Какая гарантия?", indeks=fake_indeks, ask=fake_ask)
    assert "уточните" in rezultat["otvet"].lower()
    assert rezultat["proverki"] != "пройдены"


def test_ask_endpoint_ispolzuet_otvetit(monkeypatch):
    # main.py импортировал otvetit напрямую (`from app.rag import otvetit`) —
    # патчить нужно ссылку в app.main, а не в app.rag.
    import app.main as main_module
    monkeypatch.setattr(main_module, "otvetit", lambda vopros: {"otvet": "заглушка"})
    response = client.post("/ask", json={"vopros": "Во сколько вы закрываетесь?"})
    assert response.status_code == 200
    assert response.json()["otvet"] == "заглушка"


def test_chat_endpoint_streamit_kuski_v_sse(monkeypatch):
    import app.chat as chat_module
    monkeypatch.setattr(chat_module, "poток_otveta", lambda session_id, vopros: iter(["При", "вет"]))
    response = client.post("/chat", json={"session_id": "t1", "vopros": "Привет"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"tekst": "При"}' in response.text
    assert response.text.strip().endswith("data: [DONE]")


def test_widget_razdayotsya_statikoy():
    response = client.get("/widget/widget.html")
    assert response.status_code == 200
    assert "Полярис" in response.text
