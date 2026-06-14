from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# CORS (фикс Failed to fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# 🔐 ключ берётся только из Render ENV
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
Ты — эксперт по вирусному и продающему контенту.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Сгенерируй 5 сильных идей контента, которые можно использовать в соцсетях.
Сделай их конкретными, не общими.
"""

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
                        "content": "Ты маркетинговый AI ассистент, который генерирует вирусные идеи контента."
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

        data_json = response.json()
        result = data_json["choices"][0]["message"]["content"]

    except Exception as e:
        result = f"AI ERROR: {str(e)}"

    return {"result": result}
