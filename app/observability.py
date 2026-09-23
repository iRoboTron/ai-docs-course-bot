"""Модуль 9, урок 1: журнал запросов и стоимость через LiteLLM.

Считаем цену не своим кодом, а `litellm.completion_cost` — но litellm не
знает цену чужого прокси под именем модели вроде "qwen/qwen3.7-flash":
у него нет записи об этом имени в собственном каталоге цен. Поэтому цену
задаём явно через `custom_cost_per_token`, а не полагаемся на автоопределение.
"""
import json
import os
import time
from pathlib import Path

import litellm
from litellm.types.utils import CostPerToken

litellm.suppress_debug_info = True  # иначе на каждый вызов шумит в stderr

LOG_PATH = Path(os.environ.get("USAGE_LOG", "usage.jsonl"))

# $ за миллион токенов — из прокси курса (см. proxy/app.py в ai-engineering-2):
# дешёвые платные модели стоят 0,03-0,15 доллара за миллион токенов.
CENA_VHODA = float(os.environ.get("AI_CENA_VHODA_ZA_MLN", "0.03")) / 1_000_000
CENA_VYHODA = float(os.environ.get("AI_CENA_VYHODA_ZA_MLN", "0.15")) / 1_000_000


def stoimost(otvet):
    """Стоимость одного вызова модели в долларах, по фактическим токенам ответа."""
    cena = CostPerToken(input_cost_per_token=CENA_VHODA, output_cost_per_token=CENA_VYHODA)
    return litellm.completion_cost(
        completion_response=otvet, model=getattr(otvet, "model", None), custom_cost_per_token=cena)


def zapisat(endpoint, vopros, otvet, nachalo, put=LOG_PATH):
    """Одна строка в журнал: что спросили, сколько токенов, сколько стоило."""
    zapis = {
        "ts": time.time(),
        "endpoint": endpoint,
        "vopros_simvolov": len(vopros),
        "prompt_tokens": otvet.usage.prompt_tokens,
        "completion_tokens": otvet.usage.completion_tokens,
        "stoimost_usd": stoimost(otvet),
        "sekund": round(time.time() - nachalo, 3),
    }
    with put.open("a", encoding="utf-8") as f:
        f.write(json.dumps(zapis, ensure_ascii=False) + "\n")
    return zapis
