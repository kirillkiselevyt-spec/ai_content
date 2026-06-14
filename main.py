from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os

app = FastAPI()

# ✅ ЖЁСТКИЙ CORS (фикс Failed to fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# простая память
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


# ✅ ОБЯЗАТЕЛЬНЫЙ PREFLIGHT FIX
@app.options("/generate")
def options_generate():
    return {"ok": True}


@app.post("/generate")
def generate(data: RequestData):

    history = USER_MEMORY.get(data.user_id, [])
    history_text = "\n".join(history[-5:])

    prompt = f"""
Ты — эксперт по вирусному контенту.

Ниша: {data.niche}
Аудитория: {data.audience}
Цель: {data.goal}
Стиль: {data.style}

История пользователя:
{history_text}

Сгенерируй 5 идей контента.
"""

   try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    result = response.text
except Exception as e:
    result = f"AI ERROR: {str(e)}"
    
    # память пользователя
    if data.user_id not in USER_MEMORY:
        USER_MEMORY[data.user_id] = []

    USER_MEMORY[data.user_id].append(result)

    return {"result": result}
