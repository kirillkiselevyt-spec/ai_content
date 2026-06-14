from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ✅ ПРАВИЛЬНЫЙ ENDPOINT DeepSeek
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


class RequestData(BaseModel):
    user_id: str
    niche: str
    audience: str
    goal: str
    style: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/debug")
def debug():
    return {
        "key_exists": bool(DEEPSEEK_API_KEY),
        "key_preview": DEEPSEEK_API_KEY[:6] if DEEPSEEK_API_KEY else None
    }


def build_prompt(data: RequestData):
    return f"""
Ты — эксперт по маркетингу и вирусному контенту.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Сгенерируй:
- 5 вирусных идей контента
- 3 продающих поста
- 3 hooks (зацепки для первых секунд)
"""


def call_deepseek(prompt: str):
    return requests.post(
        DEEPSEEK_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты маркетинговый AI-ассистент."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8
        },
        timeout=40
    )


@app.post("/generate")
def generate(data: RequestData):

    if not DEEPSEEK_API_KEY:
        return {"error": "Missing DEEPSEEK_API_KEY"}

    prompt = build_prompt(data)

    try:
        response = call_deepseek(prompt)

        # 🔥 ВАЖНО: диагностика (чтобы больше не гадать)
        if response.status_code != 200:
            return {
                "error": "DeepSeek API error",
                "status_code": response.status_code,
                "text": response.text
            }

        result = response.json()

        # ✔ безопасное извлечение
        content = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", None)
        )

        if not content:
            return {
                "error": "No content in response",
                "raw": result
            }

        return {
            "result": content
        }

    except Exception as e:
        return {
            "error": str(e)
        }
