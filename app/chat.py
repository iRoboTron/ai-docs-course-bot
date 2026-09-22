"""Модуль 8, урок 1: потоковый ответ для диалога на сайте.

Памяти диалога здесь ещё нет — каждый вопрос независим, как v1 из модуля 1.
Память добавим в уроке 2, когда появится, что именно обрезать.
"""
from app.config import MODEL
from app.rag import klient

PRAVILA_CHAT = (
    "Ты помощник сервисного центра «Полярис». Отвечай вежливо и коротко, "
    "на русском языке."
)


def poток_otveta(vopros, client_=None):
    """Отдаёт ответ по кусочкам — генератор, а не готовая строка."""
    client_ = client_ or klient()
    potok = client_.chat.completions.create(
        model=MODEL, temperature=0, max_tokens=300, stream=True,
        messages=[{"role": "system", "content": PRAVILA_CHAT},
                  {"role": "user", "content": vopros}])
    for kusok in potok:
        if kusok.choices and kusok.choices[0].delta.content:
            yield kusok.choices[0].delta.content
