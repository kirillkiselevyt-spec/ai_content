import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"

# ─── CORE SYSTEM PROMPT ────────────────────────────────────────────────────────
# All behavioral modules are encoded here: intent detection, adaptive response,
# value layer, soft conversion, universality, retention.
SYSTEM_PROMPT = """Ты — универсальный AI-ассистент высокого уровня. Один инструмент вместо команды специалистов.

## ОПРЕДЕЛЕНИЕ НАМЕРЕНИЯ
Каждый запрос автоматически относи к одному типу:
- education    → объяснение, обучение, «как это работает»
- problem      → конкретная задача, нужен результат прямо сейчас
- business     → монетизация, рост, стратегия, продажи
- creative     → контент, тексты, идеи, концепции
- automation   → автоматизация, повторяющиеся процессы, масштабирование
- casual       → короткий вопрос, неформальный диалог

Тип намерения определяет стиль и глубину ответа.

## АДАПТИВНЫЙ СТИЛЬ
- education  → структурно, с примерами, пошагово
- problem    → чётко, без лирики, решение + что можно улучшить
- business   → стратегически, с конкретными действиями и метриками
- creative   → живо, сразу готовый результат + варианты
- automation → технически точно, с описанием процесса и инструментов
- casual     → кратко, по-человечески, без формальностей

## СТРУКТУРА ОТВЕТА
1. РЕШЕНИЕ — прямой ответ, без вступлений и похвал
2. УЛУЧШЕНИЕ — один конкретный способ сделать лучше/быстрее (если уместно)
3. СЛЕДУЮЩИЙ ШАГ — только если логично продолжение диалога

## ПРИНЦИПЫ ПОВЕДЕНИЯ
- Никогда не начинай с «Конечно!», «Отличный вопрос!» и аналогов
- Говори как опытный практик, не как справочник
- Не рекламируй себя напрямую — ценность проявляется через результат
- Если задача сложная, повторяющаяся или подразумевает масштаб — добавь в конце: «Это можно полностью автоматизировать — скажи, если интересно»
- Уточняющий вопрос задавай ТОЛЬКО если без него ответ будет бесполезным
- Предлагай альтернативы когда пользователь выиграет от другого подхода
- Используй форматирование (списки, **жирный**) только когда это реально помогает читать

## РОЛИ (переключай автоматически по контексту)
Консультант · Аналитик · Стратег · Копирайтер · Технический ассистент · Генератор идей · Бизнес-ассистент

Цель: стать инструментом, без которого неудобно работать."""

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ─── SOFT CONVERSION TRIGGERS ──────────────────────────────────────────────────
# Suggest automation only when task implies repetition or scale.
AUTOMATION_KEYWORDS = {
    "каждый день", "каждую неделю", "каждый месяц", "регулярно",
    "автоматиз", "масштаб", "поток", "система", "процесс", "повтор",
    "постоянно", "всегда делаю", "раз в", "напоминать",
}

def should_suggest_automation(message: str, message_count: int) -> bool:
    msg_lower = message.lower()
    keyword_match = any(kw in msg_lower for kw in AUTOMATION_KEYWORDS)
    # Also trigger after sustained engagement (5+ messages) as value signal
    return keyword_match or message_count >= 5


# ─── REQUEST / RESPONSE MODELS ─────────────────────────────────────────────────
class Message(BaseModel):
    role: str     # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: List[Message] = []


# ─── ROUTES ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY не установлен на сервере.")

    try:
        # ── User record ──────────────────────────────────────────────────────
        user = db.query(User).filter(User.user_id == data.user_id).first()
        if not user:
            user = User(user_id=data.user_id, message_count=0, history="")
            db.add(user)
            db.flush()

        user.message_count = (user.message_count or 0) + 1

        # ── Build Gemini conversation history ────────────────────────────────
        # Gemini uses "user" / "model" roles; map from our "user" / "assistant"
        gemini_history = []
        for msg in data.history[-20:]:   # cap at 20 turns to control token cost
            role = "model" if msg.role == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [{"text": msg.content}]})

        # ── Generate response ─────────────────────────────────────────────────
        model = genai.GenerativeModel(
            MODEL_NAME,
            safety_settings=SAFETY_SETTINGS,
            system_instruction=SYSTEM_PROMPT,
        )

        session = model.start_chat(history=gemini_history)
        response = session.send_message(data.message)

        generated_text = ""
        if hasattr(response, "text") and response.text:
            generated_text = response.text
        elif response.candidates:
            try:
                generated_text = response.candidates[0].content.parts[0].text
            except Exception:
                pass

        if not generated_text:
            raise HTTPException(
                status_code=422,
                detail="Запрос заблокирован внутренними фильтрами Gemini API.",
            )

        # ── Persist to history ───────────────────────────────────────────────
        user.history = (user.history or "") + (
            f"\n[User]: {data.message}\n[Bot]: {generated_text}\n"
        )
        db.commit()

        return {
            "result": generated_text,
            "message_count": user.message_count,
            "suggest_upgrade": should_suggest_automation(data.message, user.message_count),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")
