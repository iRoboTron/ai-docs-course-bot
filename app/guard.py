"""Модуль 10, урок 1: защита от подмены инструкций во входящем вопросе.

Тот же принцип, что и в модуле 6: не спрашиваем модель, можно ли доверять
тексту — код сравнивает строки. Разница в том, ЧТО проверяем: в модуле 6
проверяли ЦИТАТУ в ОТВЕТЕ модели, здесь — сам ВОПРОС гостя, ещё до того, как
он вообще попадёт в RAG.
"""
import os
import re

os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # см. модуль 6: гасим шум телеметрии

from guardrails import Guard
from guardrails.errors import ValidationError
from guardrails.validator_base import FailResult, PassResult, Validator, register_validator

# Явные маркеры подмены инструкций — тот же приём, что в вопросе-провокации
# из модуля 6 ("ВАЖНО ДЛЯ АССИСТЕНТА: игнорируй предыдущие инструкции...").
PRIZNAKI_PODMENY = (
    "игнорируй предыдущие", "игнорируй все инструкции", "важно для ассистента",
    "новые инструкции", "system prompt", "забудь предыдущие", "ты теперь другой",
)


def normalizovat(tekst):
    return re.sub(r"\s+", " ", tekst.lower()).strip()


@register_validator(name="net-podmeny-instruktsiy", data_type="string")
class NetPodmenyInstruktsiy(Validator):
    """Ищет явные маркеры подмены инструкций во входящем тексте гостя."""

    def _validate(self, value, metadata):
        normalizovannyy = normalizovat(value)
        for priznak in PRIZNAKI_PODMENY:
            if priznak in normalizovannyy:
                return FailResult(error_message=f"похоже на подмену инструкций: «{priznak}»")
        return PassResult()


def podozritelnyy_vopros(vopros):
    """True, если вопрос гостя похож на попытку подмены инструкций."""
    guard = Guard().use(NetPodmenyInstruktsiy(on_fail="exception"))
    try:
        guard.validate(vopros)
        return False
    except ValidationError:
        return True


# Модуль 10, урок 2: личные данные в ответе — с оговоркой. У «Полярис» есть
# СВОЙ публичный телефон и почта (kontakty.html) — наивная проверка «похоже
# на телефон» заблокирует законный ответ на «как с вами связаться?». Поэтому
# проверяем не «есть ли похожее на телефон», а «есть ли то, что НЕ входит
# в список уже опубликованных на сайте контактов».
PATTERN_TELEFON = re.compile(r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")
PATTERN_EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")

RAZRESHENNYE_KONTAKTY = {"+7 (999) 000-00-00", "help@polaris-service.example"}


@register_validator(name="net-neizvestnyh-dannyh", data_type="string")
class NetNeizvestnyhDannyh(Validator):
    """Ищет телефон/почту в ответе, которых нет в списке уже опубликованных контактов."""

    def _validate(self, value, metadata):
        naydennoe = PATTERN_TELEFON.findall(value) + PATTERN_EMAIL.findall(value)
        neizvestnoe = [n for n in naydennoe if n not in RAZRESHENNYE_KONTAKTY]
        if neizvestnoe:
            return FailResult(error_message=f"в ответе неопубликованные контактные данные: {neizvestnoe}")
        return PassResult()


def soderzhit_neizvestnye_dannye(otvet):
    """True, если в ответе есть телефон/почта, которых нет в RAZRESHENNYE_KONTAKTY."""
    guard = Guard().use(NetNeizvestnyhDannyh(on_fail="exception"))
    try:
        guard.validate(otvet)
        return False
    except ValidationError:
        return True
