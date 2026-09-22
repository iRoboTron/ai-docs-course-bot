"""Поток без памяти (модуль 8, урок 1) — с подставным клиентом, без сети."""
from app import chat


class FakeDelta:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.delta = FakeDelta(content)


class FakeChunk:
    def __init__(self, content=None, s_vyborom=True):
        self.choices = [FakeChoice(content)] if s_vyborom else []


class FakeCompletions:
    def __init__(self, kuski):
        self.kuski = kuski

    def create(self, **kwargs):
        return iter(self.kuski)


class FakeClient:
    def __init__(self, kuski):
        self.chat = self
        self.completions = FakeCompletions(kuski)


def test_potok_otveta_sobiraet_kuski_v_poryadke():
    fake = FakeClient([FakeChunk("При"), FakeChunk("вет"), FakeChunk("!")])
    kuski = list(chat.poток_otveta("Привет", client_=fake))
    assert kuski == ["При", "вет", "!"]


def test_potok_otveta_propuskaet_pustye_kuski():
    """Некоторые провайдеры шлют финальный кусок без choices — это не ошибка."""
    fake = FakeClient([FakeChunk("текст"), FakeChunk(s_vyborom=False)])
    kuski = list(chat.poток_otveta("Привет", client_=fake))
    assert kuski == ["текст"]
