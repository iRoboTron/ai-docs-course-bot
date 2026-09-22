"""Память диалога (модуль 8, урок 2) — без сети: подставная модель, реальный
trim_messages (он сам по себе не ходит в сеть и не нуждается в подмене)."""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app import chat


class FakeChunk:
    def __init__(self, content):
        self.content = content


class ZapominayushchayaModel:
    """Записывает, какие сообщения ей передали — чтобы проверить, что модель
    действительно увидела историю, а не только последний вопрос."""

    poslednie_vyzovy = []

    def stream(self, soobshcheniya):
        ZapominayushchayaModel.poslednie_vyzovy.append(soobshcheniya)
        yield FakeChunk("ок")


def test_obrezat_istoriyu_ostavlyaet_svezhie_soobshcheniya():
    istoriya = [
        SystemMessage("Правила"),
        HumanMessage("Во сколько вы закрываетесь в субботу?"),
        AIMessage("В субботу мы работаем до 17:00."),
        HumanMessage("А в воскресенье?"),
        AIMessage("В воскресенье мы не работаем."),
        HumanMessage("Какая у вас гарантия на ремонт?"),
    ]
    obrezano = chat.obrezat_istoriyu(istoriya, max_tokens=50)
    teksty = [m.content for m in obrezano]
    assert teksty[0] == "Правила"  # системное правило остаётся всегда
    assert teksty[-1] == "Какая у вас гарантия на ремонт?"
    assert not any("субботу" in t for t in teksty)  # самый старый обмен обрезан


def test_potok_otveta_sobiraet_kuski_i_sohranyaet_istoriyu():
    chat.ISTORII.clear()
    kuski = list(chat.poток_otveta("s1", "Привет", model_factory=ZapominayushchayaModel))
    assert kuski == ["ок"]
    assert len(chat.ISTORII["s1"]) == 2  # вопрос гостя + ответ бота


def test_potok_otveta_pomnit_predydushchiy_vopros():
    chat.ISTORII.clear()
    ZapominayushchayaModel.poslednie_vyzovy.clear()

    list(chat.poток_otveta("s1", "Меня зовут Женя", model_factory=ZapominayushchayaModel))
    list(chat.poток_otveta("s1", "Как меня зовут?", model_factory=ZapominayushchayaModel))

    vtoroy_zapros = ZapominayushchayaModel.poslednie_vyzovy[1]
    teksty = [m.content for m in vtoroy_zapros]
    assert any("Женя" in t for t in teksty)


def test_raznye_sessii_ne_delyat_istoriyu():
    chat.ISTORII.clear()
    list(chat.poток_otveta("s1", "Меня зовут Женя", model_factory=ZapominayushchayaModel))
    list(chat.poток_otveta("s2", "Как меня зовут?", model_factory=ZapominayushchayaModel))
    teksty_s2 = [m.content for m in chat.ISTORII["s2"]]
    assert not any("Женя" in t for t in teksty_s2)
