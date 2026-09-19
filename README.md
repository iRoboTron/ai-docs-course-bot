# Полярис: бот для сайта

Часть 2 курса [«ИИ для документов»](https://github.com/iRoboTron/ai-docs-course) — модуль 7 и дальше.
В части 1 (модули 1-6, Colab) мы выбрали связку RAG и научили бота проверять свои
ответы. Здесь та же логика становится настоящим сервисом: FastAPI вместо ячеек
ноутбука, тесты вместо «посмотри на вывод», CI вместо «запусти ещё раз руками».

## Что понадобится

Пройденные модули 1-6 в [ai-docs-course](https://github.com/iRoboTron/ai-docs-course) —
код в `app/rag.py` дословно перенесён из `notebooks/modul6__01_citaty_i_kachestvo.py`,
без нового объяснения того, что уже разобрано в курсе.

## Устройство

- `app/rag.py` — поиск, ответ с цитатой, проверка цитаты и чисел (модули 4-6).
- `app/main.py` — `GET /health`, `POST /ask`.
- `app/config.py` — настройки из переменных окружения: `AI_BASE_URL`, `AI_MODEL`, `AI_KEY`.
- `tests/` — проверки без сети и без модели: чистая логика (`test_rag_checks.py`)
  и API с подставным индексом и подставным ответом модели (`test_api.py`).

## Запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export AI_KEY=...          # ключ или код доступа из секретов курса
uvicorn app.main:app --reload
```

```bash
curl -X POST localhost:8000/ask -H 'content-type: application/json' \
  -d '{"vopros": "Какая у вас гарантия на ремонт?"}'
```

## Тесты

```bash
AI_KEY=fake PYTHONPATH=. pytest -q
```

Тесты не ходят в сеть и не зовут модель: `Indeks` и `sprosit_json` в `otvetit()`
подменяются на фейковые (`tests/test_api.py`), поэтому CI проходит без ключа и без
доступа к прокси курса.

## Хранилище (следующий урок)

Сейчас куски и эмбеддинги живут в памяти процесса (`app/rag.py:zagruzit_indeks`) —
тот же приём, что в модулях 4-6, только внутри сервиса вместо ноутбука. Сравнение
файла / SQLite / pgvector — тема следующего урока модуля 7.
