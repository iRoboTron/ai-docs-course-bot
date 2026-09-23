"""Лимит запросов и резервная модель (модуль 9, урок 2) — без сети."""
import litellm

from app import limits


def test_prevysen_limit_propuskaet_poka_ne_dostignut_potolok():
    limits.ZAPROSY.clear()
    for _ in range(3):
        assert not limits.prevysen_limit("s1", seychas=1000.0, max_zaprosov=3)
    # четвёртый в то же самое время — лимит исчерпан
    assert limits.prevysen_limit("s1", seychas=1000.0, max_zaprosov=3)


def test_prevysen_limit_starye_zaprosy_vypadayut_iz_okna():
    limits.ZAPROSY.clear()
    for _ in range(3):
        limits.prevysen_limit("s1", seychas=1000.0, max_zaprosov=3, okno=60)
    # прошла минута — старые запросы вне окна, лимит снова свободен
    assert not limits.prevysen_limit("s1", seychas=1061.0, max_zaprosov=3, okno=60)


def test_prevysen_limit_sessii_ne_delyat_schyotchik():
    limits.ZAPROSY.clear()
    for _ in range(3):
        limits.prevysen_limit("s1", seychas=1000.0, max_zaprosov=3)
    assert limits.prevysen_limit("s1", seychas=1000.0, max_zaprosov=3)
    assert not limits.prevysen_limit("s2", seychas=1000.0, max_zaprosov=3)


def test_router_perehodit_na_rezervnuyu_model_pri_otkaze(monkeypatch):
    vyzovy = []

    def fake_completion(*args, **kwargs):
        model = kwargs.get("model")
        vyzovy.append(model)
        if "qwen" in model:
            raise litellm.exceptions.APIConnectionError(
                message="сеть недоступна", llm_provider="openai", model=model)

        class FakeResp:
            choices = [type("C", (), {"message": type("M", (), {"content": "ок"})()})()]
        return FakeResp()

    monkeypatch.setattr(litellm, "completion", fake_completion)

    router = limits.postroit_router(["qwen/qwen3.7-flash", "google/gemma-3-12b-it"])
    rezultat = router.completion(
        model="qwen/qwen3.7-flash", messages=[{"role": "user", "content": "Привет"}])

    assert vyzovy == ["openai/qwen/qwen3.7-flash", "openai/google/gemma-3-12b-it"]
    assert rezultat.choices[0].message.content == "ок"
