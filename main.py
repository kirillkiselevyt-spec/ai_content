from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os

app = FastAPI()

# CORS (GitHub Pages → Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Простая память в RAM (для старта, без БД)
USER_MEMORY = {}

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

    # получаем историю пользователя
    history = USER_MEMORY.get(data.user_id, [])

    # формируем контекст
    history_text = "\n".join(history[-5:])  # последние 5 запросов

    prompt = f"""
Ты — эксперт по маркетингу и вирусному контенту.

Параметры пользователя:
- Ниша: {data.niche}
- Аудитория: {data.audience}
- Цель: {data.goal}
- Стиль: {data.style}

История пользователя:
{history_text}

Сгенерируй 5 новых, уникальных и вирусных идей контента.
Сделай их конкретными и применимыми.
"""

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    result = response.text

    # сохраняем память пользователя
    if data.user_id not in USER_MEMORY:
        USER_MEMORY[data.user_id] = []

    USER_MEMORY[data.user_id].append(result)

    return {"result": result}
