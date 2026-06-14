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


@app.post("/generate")
def generate(data: RequestData):

    prompt = f"""
Ты эксперт по вирусному и продающему контенту.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Сгенерируй 5 идей контента.
"""

    if not DEEPSEEK_API_KEY:
        return {"result": "ERROR: DEEPSEEK_API_KEY is not set"}

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
                        "content": "Ты маркетинговый AI ассистент"
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

        if response.status_code != 200:
            # 🔥 ВОТ ТО, ЧТО ТЫ ПРОСИЛ ДОБАВИТЬ
            return {
                "result": "API ERROR",
                "status_code": response.status_code,
                "details": response.text
            }

        data_json = response.json()

        if "choices" not in data_json:
            return {
                "result": "INVALID RESPONSE FROM DEEPSEEK",
                "raw_response": data_json
            }

        result = data_json["choices"][0]["message"]["content"]

        return {"result": result}

    except Exception as e:
        return {
            "result": "AI ERROR",
            "error": str(e)
        }
