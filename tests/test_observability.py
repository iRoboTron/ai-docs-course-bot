"""Стоимость и журнал (модуль 9, урок 1) — без сети: подставной ответ модели,
такой же по форме, как настоящий openai.types.chat.ChatCompletion."""
import json

from litellm.types.utils import Choices, Message, ModelResponse, Usage

from app import observability


def fake_otvet(model, prompt_tokens, completion_tokens):
    """litellm.types.utils.ModelResponse — тот же тип, что реально возвращает
    вызов модели; используем его и в тестах, а не свой класс наугад, чтобы
    litellm.completion_cost узнал в нём usage так же, как в настоящем ответе."""
    return ModelResponse(
        id="test", created=0, model=model,
        choices=[Choices(finish_reason="stop", index=0,
                          message=Message(role="assistant", content="ответ"))],
        usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens))


def test_stoimost_schitaetsya_po_faktcheskim_tokenam():
    # намеренно разные числа входа/выхода — если перепутать цены местами,
    # это тест должен заметить (при равных 1:1 разницы было бы не видно)
    otvet = fake_otvet("qwen/qwen3.7-flash", prompt_tokens=2_000_000, completion_tokens=1_000_000)
    # 2 * 0.03 + 1 * 0.15 = 0.21 $
    assert round(observability.stoimost(otvet), 6) == 0.21


def test_zapisat_pishet_odnu_strochku_jsonl(tmp_path):
    put = tmp_path / "usage.jsonl"
    otvet = fake_otvet("qwen/qwen3.7-flash", prompt_tokens=100, completion_tokens=20)

    zapis = observability.zapisat("ask", "Какая гарантия?", otvet, nachalo=0, put=put)

    stroki = put.read_text(encoding="utf-8").strip().split("\n")
    assert len(stroki) == 1
    iz_fayla = json.loads(stroki[0])
    assert iz_fayla["endpoint"] == "ask"
    assert iz_fayla["prompt_tokens"] == 100
    assert iz_fayla["completion_tokens"] == 20
    assert iz_fayla["stoimost_usd"] == zapis["stoimost_usd"]


def test_zapisat_dobavlyaet_a_ne_perezapisyvaet(tmp_path):
    put = tmp_path / "usage.jsonl"
    otvet = fake_otvet("qwen/qwen3.7-flash", prompt_tokens=10, completion_tokens=5)

    observability.zapisat("ask", "Первый вопрос", otvet, nachalo=0, put=put)
    observability.zapisat("ask", "Второй вопрос", otvet, nachalo=0, put=put)

    stroki = put.read_text(encoding="utf-8").strip().split("\n")
    assert len(stroki) == 2
