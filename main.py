import os
import urllib.parse
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

# ВАЖНО: убрали всё про изображения из системного промпта —
# иначе Gemini пытается сам "описывать" картинки вместо того
# чтобы молчать и дать сработать Pollinations.
SYSTEM_PROMPT = """Ты — универсальный AI-ассистент высокого уровня. Один инструмент вместо команды специалистов.

## ОПРЕДЕЛЕНИЕ НАМЕРЕНИЯ
Определи тип каждого запроса:
- education    → объяснение, обучение, «как это работает»
- problem      → конкретная задача, нужен результат прямо сейчас
- business     → монетизация, рост, стратегия, продажи
- creative     → контент, тексты, идеи, концепции
- automation   → автоматизация, повторяющиеся процессы, масштабирование
- casual       → короткий вопрос, неформальный диалог

## АДАПТИВНЫЙ СТИЛЬ
- education  → структурно, с примерами, пошагово
- problem    → чётко, без лирики, решение + что можно улучшить
- business   → стратегически, с конкретными действиями и метриками
- creative   → живо, сразу готовый результат + варианты
- automation → технически точно, с описанием процесса и инструментов
- casual     → кратко, по-человечески, без формальностей

## СТРУКТУРА ОТВЕТА
1. РЕШЕНИЕ — прямой ответ, без вступлений и похвал
2. УЛУЧШЕНИЕ — один конкретный способ сделать лучше (если уместно)
3. СЛЕДУЮЩИЙ ШАГ — только если логично продолжение диалога

## ПРИНЦИПЫ ПОВЕДЕНИЯ
- Никогда не начинай с «Конечно!», «Отличный вопрос!» и аналогов
- Говори как опытный практик, не как справочник
- Не рекламируй себя напрямую — ценность проявляется через результат
- Если задача сложная, повторяющаяся или подразумевает масштаб — добавь в конце:
  «Это можно полностью автоматизировать — скажи, если интересно»
- Уточняющий вопрос задавай ТОЛЬКО если без него ответ будет бесполезным

## РОЛИ (переключай автоматически по контексту)
Консультант · Аналитик · Стратег · Копирайтер · Технический ассистент · Генератор идей · Бизнес-ассистент

Цель: стать инструментом, без которого неудобно работать."""

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

AUTOMATION_KEYWORDS = {
    "каждый день", "каждую неделю", "каждый месяц", "регулярно",
    "автоматиз", "масштаб", "поток", "система", "процесс", "повтор",
    "постоянно", "всегда делаю", "раз в", "напоминать",
}

# Расширенный список триггеров — покрывает разные формулировки
IMAGE_KEYWORDS = [
    "нарисуй", "нарисовать", "нарисуйте",
    "сгенерируй", "сгенерировать", "сгенерируйте",
    "создай картинку", "создай изображение", "создай фото", "создай иллюстрацию",
    "сделай картинку", "сделай изображение", "сделай фото", "сделай фотографию",
    "покажи картинку", "покажи изображение", "покажи фото",
    "генерация изображения", "генерация картинки", "генерация фото",
    "сгенерируй картинку", "сгенерируй изображение", "сгенерируй фото",
    "нарисуй мне", "нарисуй картинку", "нарисуй фото",
    "generate image", "generate photo", "draw me", "create image",
    "визуализируй", "визуализация",
]

def is_image_request(message: str) -> bool:
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in IMAGE_KEYWORDS)

def should_suggest_automation(message: str, message_count: int) -> bool:
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in AUTOMATION_KEYWORDS) or message_count >= 5


def generate_image_url(prompt: str) -> str:
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true&enhance=true&seed={hash(prompt) % 9999}"


def extract_image_prompt(user_message: str) -> str:
    """
    Gemini используется ТОЛЬКО для оптимизации промпта на английский.
    Сам текстовый ответ при image-запросе Gemini НЕ генерирует.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME, safety_settings=SAFETY_SETTINGS)
        result = model.generate_content(
            "You are a prompt engineer for image generation. "
            "Extract the visual description from the user message and rewrite it as a detailed English image generation prompt. "
            "Return ONLY the prompt text, no explanations, no quotes, no extra words.\n\n"
            f"User message: {user_message}"
        )
        if hasattr(result, "text") and result.text:
            return result.text.strip()
    except Exception:
        pass
    return user_message


class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: List[Message] = []


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat")
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY не установлен на сервере.")

    try:
        user = db.query(User).filter(User.user_id == data.user_id).first()
        if not user:
            user = User(user_id=data.user_id, message_count=0, history="")
            db.add(user)
            db.flush()

        user.message_count = (user.message_count or 0) + 1

        # ── Ветка изображения — Gemini для текста НЕ вызывается ──────────────
        if is_image_request(data.message):
            image_prompt = extract_image_prompt(data.message)
            image_url = generate_image_url(image_prompt)

            user.history = (user.history or "") + (
                f"\n[User]: {data.message}\n[Bot]: [Image: {image_prompt}]\n"
            )
            db.commit()

            return {
                "type": "image",
                "image_url": image_url,
                "prompt": image_prompt,
                "suggest_upgrade": False,
            }

        # ── Ветка текста ──────────────────────────────────────────────────────
        gemini_history = []
        for msg in data.history[-20:]:
            role = "model" if msg.role == "assistant" else "user"
            gemini_history.append({"role": role, "parts": [{"text": msg.content}]})

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
            raise HTTPException(status_code=422, detail="Запрос заблокирован фильтрами Gemini.")

        user.history = (user.history or "") + (
            f"\n[User]: {data.message}\n[Bot]: {generated_text}\n"
        )
        db.commit()

        return {
            "type": "text",
            "result": generated_text,
            "message_count": user.message_count,
            "suggest_upgrade": should_suggest_automation(data.message, user.message_count),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")
