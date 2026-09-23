"""Каркас сервиса из модуля 7 (RAG с проверками) + модуль 8 (диалог)."""
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import app.chat as chat
from app.limits import prevysen_limit
from app.rag import otvetit

app = FastAPI(title="Полярис: бот для сайта")
app.mount("/widget", StaticFiles(directory="static"), name="static")


class Vopros(BaseModel):
    vopros: str


class ChatZapros(BaseModel):
    session_id: str
    vopros: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(zapros: Vopros):
    return otvetit(zapros.vopros)


@app.post("/chat")
def chat_endpoint(zapros: ChatZapros):
    """Диалог: поток без проверки цитат — для живого общения, не для фактов.
    За проверенным фактом гость всё ещё идёт в /ask (модуль 6-7)."""
    if prevysen_limit(zapros.session_id):
        raise HTTPException(429, "Слишком много сообщений подряд, подождите минуту.")

    def sobytiya():
        for kusok in chat.poток_otveta(zapros.session_id, zapros.vopros):
            yield f"data: {json.dumps({'tekst': kusok}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sobytiya(), media_type="text/event-stream")
