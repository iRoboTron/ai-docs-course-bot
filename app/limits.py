"""Модуль 9, урок 2: лимит запросов по сессии и резервная модель через LiteLLM Router."""
import os
import time
from collections import defaultdict, deque

import litellm
from litellm import Router

from app.config import API_KEY, BASE_URL

litellm.suppress_debug_info = True

MAX_ZAPROSOV_V_MINUTU = int(os.environ.get("AI_LIMIT_V_MINUTU", "10"))
OKNO_SEKUND = 60

# session_id -> времена последних запросов. Память процесса — тот же
# ограниченный приём, что файловый кэш модуля 7 и история диалога модуля 8:
# годится для одного процесса, несколько инстансов за балансировщиком
# лимит друг друга не увидят.
ZAPROSY = defaultdict(deque)


def prevysen_limit(session_id, seychas=None, max_zaprosov=MAX_ZAPROSOV_V_MINUTU, okno=OKNO_SEKUND):
    """True, если для session_id уже было max_zaprosov запросов за последнее окно."""
    seychas = seychas if seychas is not None else time.time()
    ochered = ZAPROSY[session_id]
    while ochered and seychas - ochered[0] > okno:
        ochered.popleft()
    if len(ochered) >= max_zaprosov:
        return True
    ochered.append(seychas)
    return False


# Список моделей прокси курса (proxy/app.py в ai-engineering-2) — первая
# в списке основная, остальные резервные, в этом же порядке.
MODELI_PROKSI = ["qwen/qwen3.7-flash", "google/gemma-3-12b-it", "mistralai/mistral-nemo"]


def postroit_router(modeli=MODELI_PROKSI):
    """Router с fallback: если основная модель отказала, пробует следующую по списку."""
    model_list = [{
        "model_name": model,
        "litellm_params": {"model": f"openai/{model}", "api_base": BASE_URL, "api_key": API_KEY},
    } for model in modeli]
    fallbacks = [{modeli[0]: modeli[1:]}] if len(modeli) > 1 else []
    return Router(model_list=model_list, fallbacks=fallbacks, num_retries=0)
