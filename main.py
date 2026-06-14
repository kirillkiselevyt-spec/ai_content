from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests

app = FastAPI()

# CORS для GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# актуальная модель
GEMINI_MODEL = "gemini-1.5-flash"

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
        "key_exists": bool(GEMINI_API_KEY),
        "key_preview": GEMINI_API_KEY[:6] if GEMINI_API_KEY else None
    }


def build_prompt(data: RequestData):
    return f"""
Ты — эксперт по вирусному и продающему контенту.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Сгенерируй:
- 5 вирусных идей контента
- 3 продающих поста
- 5 hooks (цепляющих заголовков)
"""


@app.post("/generate")
def generate(data: RequestData):

    if not GEMINI_API_KEY:
        return {"error": "Missing GEMINI_API_KEY"}

    prompt = build_prompt(data)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        response = requests.post(
            url,
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=40
        )

        if response.status_code != 200:
            return {
                "error": "Gemini API error",
                "status_code": response.status_code,
                "text": response.text
            }

        result = response.json()

        # безопасное извлечение текста
        text = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", None)
        )

        if not text:
            return {
                "error": "No text in response",
                "raw": result
            }

        return {
            "text": text
        }

    except Exception as e:
        return {
            "error": str(e)
        }
