"""Настройки сервиса — из переменных окружения, без секретов в коде."""
import os


def iz_okruzheniya(imya, po_umolchaniyu=None):
    znachenie = os.environ.get(imya)
    return znachenie if znachenie else po_umolchaniyu


BASE_URL = iz_okruzheniya("AI_BASE_URL", "https://ai9.adelfos.ru/api/v1")
MODEL = iz_okruzheniya("AI_MODEL", "qwen/qwen3.7-flash")
API_KEY = iz_okruzheniya("AI_KEY")
SITE_BASE = iz_okruzheniya(
    "SITE_BASE", "https://raw.githubusercontent.com/iRoboTron/ai-docs-course/main/fixtures/site/")
SITE_STRANICY = ["index.html", "uslugi.html", "garantiya.html", "dostavka.html", "kontakty.html"]
