from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# CORS (обязательно для GitHub Pages / браузера)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key берём только из Render Environment Variables
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


@app.post("/generate")
def generate(data: RequestData):

    prompt = f"""
Ты — эксперт по созданию вирусного и продающего контента.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Сгенерируй 5 уникальных идей контента.
Каждая идея должна быть конкретной, применимой и не общей.
"""

    # ❗ защита: если ключ не задан
    if not DEEPSEEK_API_KEY:
        return {"result": "ERROR: DEEPSEEK_API_KEY is not set in environment variables"}

    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты маркетинговый AI, который генерирует вирусные идеи контента"
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

        # ❗ если API вернул ошибку
        if response.status_code != 200:
            return {
                "result": "API ERROR",
                "status_code": response.status_code,
                "details": response.text
            }

        data = response.json()

        # ❗ защита от неожиданных ответов
        if "choices" not in data:
            return {
                "result": "INVALID RESPONSE FROM DEEPSEEK",
                "raw_response": data
            }

        result = data["choices"][0]["message"]["content"]

        return {"result": result}

    except Exception as e:
        return {"result": f"AI ERROR: {str(e)}"}
