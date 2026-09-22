"""Модуль 8: потоковый ответ (урок 1) + память диалога через LangChain (урок 2).

Память — не «помнить всё», а обрезать историю по бюджету токенов, когда она
разрастётся. Ровно та задача, ради которой в TODO.md курса выбрали LangChain:
у него для этого есть готовая функция `trim_messages`.
"""
from collections import defaultdict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_openai import ChatOpenAI

from app.config import API_KEY, BASE_URL, MODEL

PRAVILA_CHAT = SystemMessage(
    "Ты помощник сервисного центра «Полярис». Отвечай вежливо и коротко, "
    "на русском языке, помни, о чём спрашивал гость раньше в этом разговоре.")

MAX_TOKENS_ISTORII = 800  # бюджет памяти диалога, не всего запроса целиком

# session_id -> список сообщений. В памяти процесса — тот же приём, что с
# индексом в модуле 7: работает для одного процесса, для нескольких инстансов
# за балансировщиком понадобится общее хранилище (Redis/БД) — модуль 9.
ISTORII = defaultdict(list)


def llm(streaming=True):
    return ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODEL,
                       temperature=0, streaming=streaming)


def obrezat_istoriyu(soobshcheniya, max_tokens=MAX_TOKENS_ISTORII):
    """Оставляет самые свежие сообщения в пределах бюджета токенов."""
    return trim_messages(
        soobshcheniya, strategy="last", token_counter=count_tokens_approximately,
        max_tokens=max_tokens, start_on="human", include_system=True)


def poток_otveta(session_id, vopros, model_factory=None):
    """Отдаёт ответ по кусочкам и запоминает вопрос и ответ в истории сессии."""
    model_factory = model_factory or llm

    ISTORII[session_id].append(HumanMessage(vopros))
    soobshcheniya = obrezat_istoriyu([PRAVILA_CHAT] + ISTORII[session_id])

    kuski = []
    for chast in model_factory().stream(soobshcheniya):
        if chast.content:
            kuski.append(chast.content)
            yield chast.content
    ISTORII[session_id].append(AIMessage("".join(kuski)))
