from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests

app = FastAPI()

# CORS (для GitHub Pages / браузера)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ⚠️ безопасная дефолтная модель (поменяешь после /models)
GEMINI_MODEL = "gemini-pro"


# ---------- REQUEST MODEL ----------
class RequestData(BaseModel):
    user_id: str
    niche: str
    audience: str
    goal: str
    style: str


# ---------- ROOT ----------
@app.get("/")
def root():
    return {"status": "ok"}


# ---------- DEBUG KEY ----------
@app.get("/debug")
def debug():
    return {
        "key_exists": bool(GEMINI_API_KEY),
        "key_preview": GEMINI_API_KEY[:6] if GEMINI_API_KEY else None
    }


# ---------- LIST MODELS (ВАЖНО ДЛЯ ТЕБЯ) ----------
@app.get("/models")
def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    r = requests.get(url)
    return r.json()


# ---------- PROMPT ----------
def build_prompt(data: RequestData):
    return f"""
Ты — эксперт по вирусному и продающему контенту.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

Сгенерируй:
- 5 вирусных идей
- 3 продающих поста
- 5 цепляющих заголовков
"""


# ---------- GENERATE ----------
@app.post("/generate")
def generate(data: RequestData):

    if not GEMINI_API_KEY:
        return {"error": "Missing GEMINI_API_KEY"}

    prompt = build_prompt(data)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(url, json=payload, timeout=40)

        # если API упал
        if response.status_code != 200:
            return {
                "error": "Gemini API error",
                "status_code": response.status_code,
                "details": response.text
            }

        result = response.json()

        # безопасное извлечение текста
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return {
                "error": "Bad Gemini response format",
                "raw": result
            }

        return {
            "text": text
        }

    except Exception as e:
        return {
            "error": str(e)
        }
