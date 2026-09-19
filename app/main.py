"""Каркас сервиса из модуля 7: FastAPI поверх RAG из модуля 6."""
from fastapi import FastAPI
from pydantic import BaseModel

from app.rag import otvetit

app = FastAPI(title="Полярис: бот для сайта")


class Vopros(BaseModel):
    vopros: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(zapros: Vopros):
    return otvetit(zapros.vopros)
