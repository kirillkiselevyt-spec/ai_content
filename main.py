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


class RequestData(BaseModel):
    user_id: str
    niche: str
    audience: str
    goal: str
    style: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/debug-key")
def debug_key():
    return {
        "key_exists": bool(DEEPSEEK_API_KEY),
        "key_preview": DEEPSEEK_API_KEY[:6] if DEEPSEEK_API_KEY else None
    }


def call_deepseek(model: str, prompt: str):
    """универсальный вызов DeepSeek"""
    return requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты эксперт по вирусному и продающему контенту"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8
        },
        timeout=30
    )


@app.post("/generate")
def generate(data: RequestData):

    prompt = f"""
Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Сгенерируй 5 идей вирусного контента.
"""

    if not DEEPSEEK_API_KEY:
        return {"result": "ERROR: missing API key"}

    # 🔥 список моделей (авто fallback)
    models = [
        "deepseek-chat",
        "deepseek-reasoner",
        "deepseek-v3"
    ]

    last_error = None

    for model in models:
        try:
            response = call_deepseek(model, prompt)

            if response.status_code == 200:
                data_json = response.json()

                if "choices" in data_json:
                    return {
                        "result": data_json["choices"][0]["message"]["content"],
                        "model_used": model
                    }

                last_error = data_json

            else:
                last_error = {
                    "status_code": response.status_code,
                    "text": response.text
                }

        except Exception as e:
            last_error = str(e)

    # если все модели упали
    return {
        "result": "ALL MODELS FAILED",
        "error": last_error
    }
